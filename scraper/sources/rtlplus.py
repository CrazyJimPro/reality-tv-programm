"""Quelle fuer Sendungen, die zuerst (oder nur) im Streaming-Angebot RTL+ starten.

Solche Sendungen tauchen in keinem Fernsehprogramm auf, deshalb fehlen sie in
rtl.de und tvspielfilm.de. plus.rtl.de ist oeffentlich lesbar (robots.txt
erlaubt es und nennt die Sitemaps selbst), ein Login ist nicht noetig.

So wird gesucht (Stand Oktober 2026, per Browser und requests verifiziert):

1. Die Programm-Sitemap (plus.rtl.de/programs.sitemap.xml, ~220 Teil-Dateien,
   gut 200.000 Programme inkl. Hoerbuecher) liefert zu jedem Programm eine
   Adresse der Form "<titel>-p_<id>". Gesucht wird ueber den Namen aus
   config/reality_shows.json - eine von Hand gepflegte Zuordnung ist nicht
   noetig. Das Ergebnis wird in data/rtlplus_katalog.json zwischengespeichert,
   die Sitemaps werden hoechstens einmal pro Woche neu gelesen (oder wenn ein
   neuer Name in der Liste auftaucht).
2. Jede Programmseite ist serverseitig gerendert und enthaelt den Zustand der
   Seite als JSON (root.__dehydratedState). Daraus kommen Titel, Beschreibung,
   die Ueberschriften der Folgen-Reihen und - falls vorhanden - eine
   redaktionelle Tabelle "Folge | Datum und Uhrzeit | Sender".

Wichtig zur Datenlage: Einzelne Folgen tragen auf RTL+ KEIN Datum. Termine
stehen nur als Freitext ("Staffel 7 ab 12. Oktober", "ab 4.11."), bei
Temptation Island VIP zusaetzlich als Tabelle. Deshalb werden nur Termine
ausgegeben, die wirklich dort stehen und in der Zukunft liegen - es wird
nichts hochgerechnet. Nennt die Seite keine Uhrzeit, steht 00:00 als
Platzhalter da und die Beschreibung sagt das ausdruecklich.
"""
from __future__ import annotations

import json
import logging
import re
import time as time_module
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta
from pathlib import Path

from scraper.base import ProgrammEintrag, ScraperFehler, get_html, neue_session
from scraper.filter import lade_show_namen

QUELLE = "plus.rtl.de"
SENDER = "RTL+"
BASIS_URL = "https://plus.rtl.de"

PROJEKT_ROOT = Path(__file__).resolve().parent.parent.parent
KATALOG_PFAD = PROJEKT_ROOT / "data" / "rtlplus_katalog.json"
KATALOG_MAX_ALTER = timedelta(days=7)

# Hoechstens so viele Seiten je Sendungsname abrufen (Namen wie "Bachelor"
# treffen sonst auch Hoerbuecher und Podcasts).
MAX_SEITEN_PRO_NAME = 8
WARTEZEIT_ZWISCHEN_SEITEN_SEK = 0.3
SITEMAP_PARALLEL = 8

# Slugs, die sicher keine Fernsehsendung sind.
AUSGESCHLOSSEN = ("podcast", "vodcast", "hoerbuch", "hoerspiel")

MONATE = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
_MONATS_MUSTER = "|".join(sorted(MONATE, key=len, reverse=True))

# "ab 12.10." / "ab dem 4.11.2026" / "ab 12. Oktober" / "ab dem 16. September"
AB_ZAHL = re.compile(r"\bab\s+(?:dem\s+)?(\d{1,2})\.(\d{1,2})\.(\d{4})?", re.IGNORECASE)
AB_MONAT = re.compile(rf"\bab\s+(?:dem\s+)?(\d{{1,2}})\.\s*({_MONATS_MUSTER})\b(?:\s+(\d{{4}}))?", re.IGNORECASE)
UHRZEIT = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?\s*Uhr", re.IGNORECASE)
STAFFEL = re.compile(r"Staffel\s*(\d+)", re.IGNORECASE)
FOLGE = re.compile(r"Folge\s*(\d+)", re.IGNORECASE)
TABELLEN_ZEILE = re.compile(r"^\|\s*(?P<folge>[^|]+?)\s*\|\s*(?P<wann>[^|]+?)\s*\|\s*(?P<sender>[^|]+?)\s*\|\s*$")
TABELLEN_WANN = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})?")

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Namen und Adressen
# --------------------------------------------------------------------------

def _slug_form(text: str) -> str:
    """Schreibt einen Namen so, wie RTL+ seine Adressen bildet: Umlaute ohne
    Punkte (Köln -> koln, für -> fur), ß -> ss, alles andere wird zu '-'."""
    text = text.lower().replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _slug_passt(slug: str, name_form: str) -> bool:
    """True, wenn der Slug mit dem Namen BEGINNT (ganze Woerter). Zusaetzlich
    werden Leerzeichen ignoriert, damit "Couple Challenge" auch
    "couplechallenge-..." trifft und umgekehrt."""
    name_zusammen = name_form.replace("-", "")
    if not name_zusammen:
        return False
    woerter = slug.split("-")
    gesammelt = ""
    for wort in woerter:
        gesammelt += wort
        if gesammelt == name_zusammen:
            return True
        if len(gesammelt) > len(name_zusammen):
            return False
    return False


def _sitemap_unterdateien(session) -> list[str]:
    index = get_html(session, f"{BASIS_URL}/programs.sitemap.xml")
    adressen = re.findall(r"<loc>([^<]+)</loc>", index)
    if not adressen:
        raise ScraperFehler(f"{QUELLE}: Programm-Sitemap enthaelt keine Teil-Dateien")
    return adressen


def _sitemap_lesen(adresse: str) -> list[tuple[str, str, str]]:
    """Liefert (slug, url, lastmod) aller Programme einer Teil-Sitemap."""
    session = neue_session()
    letzter_fehler = None
    for _ in range(3):
        try:
            text = get_html(session, adresse)
            break
        except ScraperFehler as exc:
            letzter_fehler = exc
    else:
        raise ScraperFehler(str(letzter_fehler))
    treffer = []
    for m in re.finditer(r"<loc>(https://plus\.rtl\.de/([^<]+?)-p_\d+)</loc>\s*(?:<lastmod>([^<]+)</lastmod>)?", text):
        treffer.append((m.group(2), m.group(1), m.group(3) or ""))
    return treffer


def _katalog_neu_aufbauen(namen_formen: set[str]) -> dict:
    """Liest alle Programm-Sitemaps und merkt sich je Sendungsname die
    passenden Seiten (neueste zuerst)."""
    session = neue_session()
    unterdateien = _sitemap_unterdateien(session)
    logger.info("%s: lese %d Sitemap-Dateien (einmal pro Woche)", QUELLE, len(unterdateien))

    gefunden: dict[str, list[tuple[str, str]]] = {form: [] for form in namen_formen}
    fehlgeschlagen = 0
    with ThreadPoolExecutor(SITEMAP_PARALLEL) as pool:
        futures = [pool.submit(_sitemap_lesen, adresse) for adresse in unterdateien]
        for future in futures:
            try:
                eintraege = future.result()
            except ScraperFehler:
                fehlgeschlagen += 1
                continue
            for slug, url, lastmod in eintraege:
                if any(wort in slug for wort in AUSGESCHLOSSEN):
                    continue
                for form in namen_formen:
                    if _slug_passt(slug, form):
                        gefunden[form].append((url, lastmod))

    if fehlgeschlagen > len(unterdateien) // 4:
        raise ScraperFehler(f"{QUELLE}: {fehlgeschlagen} von {len(unterdateien)} Sitemap-Dateien nicht lesbar")
    if fehlgeschlagen:
        logger.warning("%s: %d Sitemap-Dateien nicht lesbar, Katalog evtl. unvollstaendig", QUELLE, fehlgeschlagen)

    treffer = {
        form: [[url, lm] for url, lm in sorted(seiten, key=lambda x: x[1], reverse=True)[:MAX_SEITEN_PRO_NAME]]
        for form, seiten in gefunden.items()
    }
    return {"stand": datetime.now().isoformat(timespec="seconds"), "treffer": treffer}


def _katalog_laden(namen_formen: set[str], katalog_pfad: Path = KATALOG_PFAD) -> dict:
    """Gibt den Zwischenspeicher zurueck, solange er frisch ist und alle
    aktuellen Namen kennt - sonst wird er neu aufgebaut. Scheitert der
    Neuaufbau, wird ein vorhandener (auch veralteter) Speicher weiterverwendet."""
    alt: dict | None = None
    try:
        alt = json.loads(katalog_pfad.read_text(encoding="utf-8"))
        stand = datetime.fromisoformat(alt["stand"])
        kennt_alle = namen_formen <= set(alt["treffer"])
        if kennt_alle and datetime.now() - stand < KATALOG_MAX_ALTER:
            return alt
    except (OSError, ValueError, KeyError, TypeError):
        alt = None

    try:
        neu = _katalog_neu_aufbauen(namen_formen)
    except ScraperFehler:
        if alt is None:
            raise
        logger.warning("%s: Sitemap nicht erreichbar - verwende den gespeicherten Katalog", QUELLE)
        return alt
    katalog_pfad.parent.mkdir(parents=True, exist_ok=True)
    katalog_pfad.write_text(json.dumps(neu, ensure_ascii=False), encoding="utf-8")
    return neu


# --------------------------------------------------------------------------
# Programmseite auswerten
# --------------------------------------------------------------------------

def _zustand_lesen(html_text: str) -> dict | None:
    m = re.search(r"root\.__dehydratedState\s*=\s*", html_text)
    if not m:
        return None
    try:
        objekt, _ = json.JSONDecoder().raw_decode(html_text[m.end():])
        return json.loads(objekt["__reduxState"])
    except (ValueError, KeyError, TypeError):
        return None


def _alle_texte(objekt):
    """Alle Strings eines verschachtelten JSON-Objekts."""
    if isinstance(objekt, str):
        yield objekt
    elif isinstance(objekt, dict):
        for wert in objekt.values():
            yield from _alle_texte(wert)
    elif isinstance(objekt, list):
        for wert in objekt:
            yield from _alle_texte(wert)


def _uhrzeit_in(text: str) -> time | None:
    m = UHRZEIT.search(text)
    if not m:
        return None
    stunde, minute = int(m.group(1)), int(m.group(2) or 0)
    if stunde > 23 or minute > 59:
        return None
    return time(stunde, minute)


def _datum_bauen(tag: int, monat: int, jahr: int | None, heute: date) -> date | None:
    """Fehlt das Jahr, gilt das laufende Jahr. Liegt das Datum dann mehr als ein
    halbes Jahr zurueck, ist das naechste Jahr gemeint (ein "ab 4.1." im
    Dezember meint Januar). Liegt es weniger weit zurueck, ist es schlicht
    vorbei - so wie das "ab 25. August" auf der Seite einer laufenden Staffel."""
    try:
        if jahr:
            return date(jahr, monat, tag)
        kandidat = date(heute.year, monat, tag)
        if kandidat < heute - timedelta(days=183):
            kandidat = date(heute.year + 1, monat, tag)
        return kandidat
    except ValueError:
        return None


def _termine_in_text(text: str, heute: date) -> list[tuple[date, time | None, int | None]]:
    """Alle "ab <Datum>"-Angaben eines Textes, die heute oder spaeter liegen.
    Die Staffelnummer zaehlt nur, wenn sie im selben Text steht."""
    staffel_treffer = STAFFEL.search(text)
    staffel = int(staffel_treffer.group(1)) if staffel_treffer else None
    ergebnis = []
    for muster, monat_aus in ((AB_ZAHL, lambda m: int(m.group(2))), (AB_MONAT, lambda m: MONATE[m.group(2).lower()])):
        for m in muster.finditer(text):
            jahr = int(m.group(3)) if m.group(3) else None
            tag = _datum_bauen(int(m.group(1)), monat_aus(m), jahr, heute)
            if tag is None or tag < heute:
                continue
            ergebnis.append((tag, _uhrzeit_in(text[m.end():m.end() + 25]), staffel))
    return ergebnis


def _tabelle_lesen(zustand: dict, heute: date) -> list[tuple[date, time, int | None, str]]:
    """Liest die redaktionelle Tabelle "Folge | Datum und Uhrzeit | Sender".
    Nur Zeilen mit Sender RTL+ zaehlen - Fernsehtermine kennen die anderen
    Quellen bereits. Ohne Jahresangabe wird fortlaufend gezaehlt (Dezember ->
    Januar springt ins naechste Jahr)."""
    ergebnis = []
    for text in _alle_texte(zustand):
        if "Datum und Uhrzeit" not in text:
            continue
        jahr = heute.year
        vorheriger_monat = None
        for zeile in text.splitlines():
            m = TABELLEN_ZEILE.match(zeile.strip())
            if not m or set(m.group("folge")) <= set("-: "):
                continue
            wann = TABELLEN_WANN.search(m.group("wann"))
            if not wann or not FOLGE.search(m.group("folge")):
                continue
            tag, monat = int(wann.group(1)), int(wann.group(2))
            if wann.group(3):
                jahr = int(wann.group(3))
            elif vorheriger_monat is not None and monat < vorheriger_monat:
                jahr += 1
            vorheriger_monat = monat
            if "rtl+" not in m.group("sender").lower().replace(" plus", "+"):
                continue
            datum = _datum_bauen(tag, monat, jahr, heute)
            if datum is None or datum < heute:
                continue
            uhrzeit = _uhrzeit_in(m.group("wann")) or time(0, 0)
            ergebnis.append((datum, uhrzeit, int(FOLGE.search(m.group("folge")).group(1)), m.group("folge").strip()))
        if ergebnis:
            break
    return ergebnis


def _beschreibung(staffel: int | None, folge: int | None, uhrzeit_bekannt: bool) -> str:
    teile = []
    if staffel:
        teile.append(f"Staffel {staffel}")
    if folge:
        teile.append(f"Folge {folge}")
    kopf = " · ".join(teile)
    zusatz = "Start auf RTL+ (Streaming)"
    if not uhrzeit_bekannt:
        zusatz += ", Uhrzeit nicht angegeben - 0:00 ist nur ein Platzhalter"
    return f"{kopf} – {zusatz}" if kopf else zusatz


def analysiere_seite(html_text: str, heute: date) -> list[ProgrammEintrag]:
    """Liest eine RTL+-Programmseite und liefert die dort genannten
    kuenftigen Termine. Leere Liste, wenn die Seite keine nennt oder gar keine
    Fernseh-/Streaming-Sendung ist (Hoerbuch, Podcast, ...)."""
    zustand = _zustand_lesen(html_text)
    if zustand is None:
        return []
    try:
        programm = next(iter(zustand["layout"]["layouts"]["main"]["program"].values()))
    except (KeyError, StopIteration, AttributeError):
        return []

    # Nur Sendungen/Serien - Hoerbuecher und Podcasts tragen andere Kennungen.
    kopf = ""
    genre = None
    for block in programm.get("blocks", []):
        inhalt = block.get("content", {})
        if inhalt.get("blockTemplateId") == "Solo" and inhalt.get("items"):
            teile = inhalt["items"][0].get("itemContent", {})
            kopf = teile.get("highlight") or ""
            break
    if not re.match(r"(Show|Serie)\b", kopf):
        return []
    genre = " / ".join(t.strip() for t in kopf.split("•") if t.strip())

    titel = (programm.get("entity", {}).get("metadata", {}).get("title")
             or programm.get("seo", {}).get("title") or "").strip()
    if not titel:
        return []

    seo = programm.get("seo", {}).get("metadata", {})
    freitexte = []
    for block in programm.get("blocks", []):
        ueberschrift = block.get("content", {}).get("title")
        if isinstance(ueberschrift, dict):
            ueberschrift = ueberschrift.get("long") or ueberschrift.get("short")
        if isinstance(ueberschrift, str):
            freitexte.append(ueberschrift)
    freitexte += [seo.get("title") or "", seo.get("description") or ""]

    freie_termine = []
    for text in freitexte:
        freie_termine.extend(_termine_in_text(text, heute))

    eintraege: list[ProgrammEintrag] = []
    tabelle = _tabelle_lesen(zustand, heute)
    if tabelle:
        # Staffelnummer: aus dem Freitext zum ersten Tabellentermin
        erster = tabelle[0][0]
        staffel = next((s for d, _u, s in freie_termine if d == erster and s), None)
        for datum, uhrzeit, folge, _zeile in tabelle:
            eintraege.append(ProgrammEintrag(
                quelle=QUELLE, sender=SENDER, datum=datum, uhrzeit=uhrzeit, titel=titel,
                beschreibung=_beschreibung(staffel, folge, True), genre=genre,
            ))
    elif freie_termine:
        # Nur der fruehste Termin: mehrere Datumsangaben im Freitext waeren sonst geraten.
        datum = min(d for d, _u, _s in freie_termine)
        gleiche = [(u, s) for d, u, s in freie_termine if d == datum]
        uhrzeit = next((u for u, _s in gleiche if u), None)
        staffel = next((s for _u, s in gleiche if s), None)
        eintraege.append(ProgrammEintrag(
            quelle=QUELLE, sender=SENDER, datum=datum, uhrzeit=uhrzeit or time(0, 0), titel=titel,
            beschreibung=_beschreibung(staffel, None, uhrzeit is not None), genre=genre,
        ))
    return eintraege


# --------------------------------------------------------------------------
# Einstiegspunkt
# --------------------------------------------------------------------------

def fetch(heute: date | None = None, katalog_pfad: Path = KATALOG_PFAD, namen: list[str] | None = None) -> list[ProgrammEintrag]:
    """Sucht die Sendungen der Liste auf RTL+ und liefert deren kuenftige Termine."""
    heute = heute or date.today()
    formen = {f for f in (_slug_form(n) for n in (namen if namen is not None else lade_show_namen())) if f}
    if not formen:
        return []

    katalog = _katalog_laden(formen, katalog_pfad)
    adressen: dict[str, None] = {}
    for form in sorted(formen):
        for url, _lastmod in katalog["treffer"].get(form, []):
            adressen[url] = None
    logger.info("%s: %d Programmseiten zu %d Sendungsnamen", QUELLE, len(adressen), len(formen))

    session = neue_session()
    alle: list[ProgrammEintrag] = []
    gelesen = 0
    for url in adressen:
        try:
            html_text = get_html(session, url)
        except ScraperFehler as exc:
            logger.warning("%s: %s", QUELLE, exc)
            continue
        gelesen += 1
        gefunden = analysiere_seite(html_text, heute)
        if gefunden:
            logger.info("%s: %s -> %d Termin(e)", QUELLE, url.rsplit("/", 1)[-1], len(gefunden))
        alle.extend(gefunden)
        time_module.sleep(WARTEZEIT_ZWISCHEN_SEITEN_SEK)

    if adressen and gelesen == 0:
        raise ScraperFehler(f"{QUELLE}: keine einzige Programmseite war lesbar")

    # Gleiche Termine (z.B. alte und neue Seite derselben Sendung) nur einmal.
    eindeutig = {(e.titel, e.datum, e.uhrzeit): e for e in alle}
    return list(eindeutig.values())
