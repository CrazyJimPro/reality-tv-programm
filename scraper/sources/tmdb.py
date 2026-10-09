"""Streaming- und Staffelstarts ueber TMDB (themoviedb.org).

Joyn und Prime Video selbst taugen nicht als Quelle (Untersuchung Oktober
2026): Joyn fuehrt auf den Serienseiten nur bereits verfuegbare Folgen,
kuenftige Starts stehen dort hoechstens als Redaktionstext; Amazon sperrt
seine Video-Schnittstelle in der robots.txt und verbietet Scraping in den
AGB. TMDB dagegen nennt je Serie die kommenden Folgen mit Datum - auch die,
die zuerst im Streaming starten (z.B. "Das grosse Promi-Buessen" Staffel 5
am 26.10. bei Joyn, im Fernsehen erst vier Wochen spaeter).

Liefert drei Dinge (siehe Ergebnis):
  termine      - kommende Folgen der Sendungen aus der Liste im
                 Vorschauzeitraum. Welche davon schon im Fernsehprogramm
                 stehen, sortiert run.py aus.
  demnaechst   - Staffelstarts (Folge 1) danach, bis TAGE_DEMNAECHST
  entdeckungen - kommende deutsche Reality-Formate bei Joyn, RTL+, Prime
                 Video und Netflix, fuer den Kasten "Neu entdeckt"

Grenzen: TMDB pflegt die Community. Ein Tag Abweichung kommt vor, eine
Uhrzeit gibt es nicht, und die Senderangabe kann veraltet sein (Promi-Buessen
steht dort noch bei ProSieben). Die Anzeige sagt deshalb immer "laut TMDB".

Braucht einen kostenlosen TMDB-Schluessel (config/tmdb.json, eingetragen
ueber die Einstellungen). Ohne Schluessel tut die Quelle schlicht nichts.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from pathlib import Path

import requests
from rapidfuzz import fuzz

from scraper.base import REQUEST_TIMEOUT, ScraperFehler, neue_session
from scraper.filter import normalisiert
from scraper.merge import MergedEintrag

QUELLE = "themoviedb.org"
API = "https://api.themoviedb.org/3/"

PROJEKT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHLUESSEL_PFAD = PROJEKT_ROOT / "config" / "tmdb.json"
# Feste Installationsorte des Schwesterprojekts streaming-info (start.bat /
# start.sh legen es dort an) - nur fuer den Knopf "Aus Streaming-Info
# uebernehmen" in den Einstellungen
STREAMING_INFO_CONFIGS = [Path.home() / "streaming-info" / "config" / "config.json"]

# Name aus der Liste -> TMDB-Serien. Aendert sich praktisch nie; ein
# Fehlschlag wird frueher erneut versucht, weil Serien bei TMDB oft erst
# kurz vor dem Start angelegt werden.
ZUORDNUNG_PFAD = PROJEKT_ROOT / "data" / "tmdb_zuordnung.json"
ZUORDNUNG_TAGE = 30
ZUORDNUNG_NICHTS_TAGE = 7

TAGE_DEMNAECHST = 90
TAGE_ENTDECKEN = 60
NAMENS_SCHWELLE = 85
GLEICHZEITIG = 4

# TMDB-Netzwerk-IDs der Streamingdienste (per tv/{id} -> networks ermittelt)
STREAMING_NETZWERKE = {3155: "Joyn", 5428: "RTL+", 1024: "Prime Video", 213: "Netflix"}
# Genre "Reality" bei TMDB (umfasst leider auch Spiel- und Quizshows)
GENRE_REALITY = 10764
DEUTSCHSPRACHIG = {"DE", "AT", "CH"}
# "Folge 12"/"Episode 12" ist kein echter Folgentitel
GENERISCHER_FOLGENTITEL = re.compile(r"^(Folge|Episode)\s*\d+$", re.IGNORECASE)

logger = logging.getLogger(__name__)


@dataclass
class Ergebnis:
    # (Eintrag, Suchbegriffe der Sendung aus der Liste) - fuer den Abgleich
    # mit dem Fernsehprogramm in run.py
    termine: list[tuple[MergedEintrag, list[str]]] = field(default_factory=list)
    demnaechst: list[dict] = field(default_factory=list)
    entdeckungen: list[MergedEintrag] = field(default_factory=list)


def lade_schluessel() -> str | None:
    try:
        daten = json.loads(SCHLUESSEL_PFAD.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return (daten.get("tmdb_api_key") or "").strip() or None


def speichere_schluessel(schluessel: str | None) -> None:
    if not schluessel:
        SCHLUESSEL_PFAD.unlink(missing_ok=True)
        return
    SCHLUESSEL_PFAD.parent.mkdir(parents=True, exist_ok=True)
    SCHLUESSEL_PFAD.write_text(json.dumps({"tmdb_api_key": schluessel.strip()}, indent=2) + "\n", encoding="utf-8")


def schluessel_aus_streaming_info() -> str | None:
    for pfad in STREAMING_INFO_CONFIGS:
        try:
            schluessel = json.loads(pfad.read_text(encoding="utf-8")).get("tmdb_api_key")
        except (OSError, ValueError):
            continue
        if schluessel:
            return schluessel.strip()
    return None


class _Tmdb:
    def __init__(self, schluessel: str):
        self.schluessel = schluessel
        self.lokal = threading.local()

    def get(self, pfad: str, **params) -> dict:
        if not hasattr(self.lokal, "session"):
            self.lokal.session = neue_session()
        params.setdefault("language", "de-DE")
        headers = {}
        # v3-Schluessel (32 Zeichen) als Parameter, v4-Lesetoken als Bearer
        if len(self.schluessel) > 40:
            headers["Authorization"] = f"Bearer {self.schluessel}"
        else:
            params["api_key"] = self.schluessel
        try:
            antwort = self.lokal.session.get(API + pfad, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            raise ScraperFehler(f"{QUELLE}: Netzwerkfehler ({exc})") from exc
        if antwort.status_code == 401:
            raise ScraperFehler(f"{QUELLE}: Schlüssel ungültig (in den Einstellungen prüfen)")
        if antwort.status_code == 404:
            return {}
        if antwort.status_code >= 400:
            raise ScraperFehler(f"{QUELLE}: HTTP {antwort.status_code} bei {pfad}")
        return antwort.json()


def pruefe_schluessel(schluessel: str) -> str | None:
    """None, wenn der Schluessel funktioniert - sonst eine Fehlermeldung."""
    try:
        _Tmdb(schluessel.strip()).get("configuration")
    except ScraperFehler as exc:
        if "ungültig" in str(exc):
            return "TMDB hat den Schlüssel abgelehnt. Bitte prüfen, ob er vollständig kopiert wurde (API-Schlüssel v3, 32 Zeichen)."
        return f"TMDB ist gerade nicht erreichbar, der Schlüssel konnte nicht geprüft werden ({exc})."
    return None


def _ist_deutschsprachig(serie: dict) -> bool:
    return serie.get("original_language") == "de" or bool(DEUTSCHSPRACHIG & set(serie.get("origin_country") or []))


def _ohne_satzzeichen(text: str) -> str:
    return " ".join(re.sub(r"[^\w ]", " ", normalisiert(text)).split())


def _suche(tmdb: _Tmdb, begriff: str) -> int | None:
    """Beste deutschsprachige Serie zum Suchbegriff. Nur deutschsprachige,
    sonst landet "Love Island" bei der tschechischen oder der US-Fassung."""
    beste, beste_wertung = None, None
    for serie in tmdb.get("search/tv", query=begriff).get("results", [])[:10]:
        if not _ist_deutschsprachig(serie):
            continue
        namen = [normalisiert(serie.get(feld) or "") for feld in ("name", "original_name")]
        enthalten = max(fuzz.token_set_ratio(normalisiert(begriff), n) for n in namen)
        if enthalten < NAMENS_SCHWELLE:
            continue
        # token_set_ratio gibt 100, sobald der Begriff im Namen steckt - dann
        # sind "Promi Big Brother" und "Promi Big Brother - Die Late Night
        # Show" gleichauf. Ein exakt gleicher Name gewinnt, sonst die
        # bekanntere Serie ("Sommerhaus der Stars" -> die Hauptshow, nicht
        # der kuerzer benannte "Live Talk").
        exakt = _ohne_satzzeichen(begriff) in {_ohne_satzzeichen(n) for n in namen}
        wertung = (enthalten, exakt, serie.get("popularity") or 0)
        if beste_wertung is None or wertung > beste_wertung:
            beste, beste_wertung = serie["id"], wertung
    return beste


def _zuordnen(tmdb: _Tmdb, shows: list[dict], heute: date) -> dict[str, list[int]]:
    """Listenname -> TMDB-IDs (Name und jeder Alias werden gesucht, ein
    Eintrag kann so mehrere Serien abdecken, z.B. "Temptation Island" und
    "Temptation Island VIP")."""
    try:
        cache = json.loads(ZUORDNUNG_PFAD.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}

    def frisch(eintrag: dict | None) -> bool:
        if not eintrag:
            return False
        alter = (heute - date.fromisoformat(eintrag["am"])).days
        return alter < (ZUORDNUNG_TAGE if eintrag.get("id") else ZUORDNUNG_NICHTS_TAGE)

    begriffe = sorted({b for show in shows for b in [show["name"], *show.get("aliases", [])] if b.strip()})
    offen = [b for b in begriffe if not frisch(cache.get(b))]

    def _hole(begriff: str) -> tuple[str, int | None]:
        return begriff, _suche(tmdb, begriff)

    with ThreadPoolExecutor(max_workers=GLEICHZEITIG) as pool:
        for begriff, tmdb_id in pool.map(_hole, offen):
            cache[begriff] = {"id": tmdb_id, "am": heute.isoformat()}

    try:
        ZUORDNUNG_PFAD.parent.mkdir(parents=True, exist_ok=True)
        ZUORDNUNG_PFAD.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as exc:
        logger.warning("TMDB-Zuordnung nicht schreibbar (%s)", exc)

    ergebnis: dict[str, list[int]] = {}
    for show in shows:
        ids = []
        for begriff in [show["name"], *show.get("aliases", [])]:
            tmdb_id = (cache.get(begriff) or {}).get("id")
            if tmdb_id and tmdb_id not in ids:
                ids.append(tmdb_id)
        ergebnis[show["name"]] = ids
    return ergebnis


def _plattform(serie: dict) -> str:
    """Streamingdienst aus den TMDB-Netzwerken, sonst neutral "TMDB" - die
    Fernsehsender dort sind nicht verlaesslich genug, um sie als Sender
    einer Ausstrahlung hinzuschreiben."""
    for netz in serie.get("networks") or []:
        if netz.get("id") in STREAMING_NETZWERKE:
            return STREAMING_NETZWERKE[netz["id"]]
    return "TMDB"


def _beschreibung(serie: dict, folge: dict | None = None) -> str:
    teile = []
    if folge and folge.get("name") and not GENERISCHER_FOLGENTITEL.match(folge["name"].strip()):
        teile.append(folge["name"].strip())
    netze = ", ".join(n["name"] for n in serie.get("networks") or [])
    teile.append(f"Termin laut TMDB, ohne Uhrzeit{f' ({netze})' if netze else ''}")
    return " · ".join(teile)


def _eintrag(serie: dict, folge: dict, bis_folge: int | None = None) -> MergedEintrag:
    """bis_folge: mehrere Folgen am selben Tag (Streamingdienste veroeffentlichen
    oft zwei auf einmal) werden ein Eintrag "Folge 19-20" - ohne Uhrzeit
    haetten sie sonst denselben Schluessel und ueberschrieben sich."""
    nummer = f"{folge['episode_number']}–{bis_folge}" if bis_folge else str(folge["episode_number"])
    return MergedEintrag(
        sender=_plattform(serie),
        datum=date.fromisoformat(folge["air_date"]),
        uhrzeit=time(0, 0),
        titel=serie["name"],
        beschreibung=_beschreibung(serie, None if bis_folge else folge),
        quellen=[QUELLE],
        folge=f"Staffel {folge['season_number']}, Folge {nummer}",
        folgentitel=None if bis_folge else ((folge.get("name") or "").strip() or None),
    )


def _kommende_folgen(tmdb: _Tmdb, serie: dict, heute: date, bis: date) -> list[dict]:
    """Alle Folgen der laufenden bzw. naechsten Staffel mit Datum in [heute, bis]."""
    naechste = serie.get("next_episode_to_air")
    if not naechste:
        return []
    staffel = tmdb.get(f"tv/{serie['id']}/season/{naechste['season_number']}")
    folgen = []
    for folge in staffel.get("episodes") or [naechste]:
        try:
            datum = date.fromisoformat(folge.get("air_date") or "")
        except ValueError:
            continue
        if heute <= datum <= bis:
            folgen.append(folge)
    return folgen


def _entdecken(tmdb: _Tmdb, heute: date) -> list[MergedEintrag]:
    """Kommende deutsche Reality bei den Streamingdiensten - fuer "Neu entdeckt"."""
    ids: list[int] = []
    for seite in (1, 2):
        antwort = tmdb.get(
            "discover/tv",
            with_networks="|".join(str(i) for i in STREAMING_NETZWERKE),
            with_genres=GENRE_REALITY,
            with_original_language="de",
            sort_by="popularity.desc",
            page=seite,
            **{"air_date.gte": heute.isoformat(), "air_date.lte": (heute + timedelta(days=TAGE_ENTDECKEN)).isoformat()},
        )
        ids += [s["id"] for s in antwort.get("results", [])]
        if seite >= (antwort.get("total_pages") or 1):
            break

    def _hole(tmdb_id: int) -> MergedEintrag | None:
        serie = tmdb.get(f"tv/{tmdb_id}")
        naechste = serie.get("next_episode_to_air")
        if not naechste or not naechste.get("air_date"):
            return None
        eintrag = _eintrag(serie, naechste)
        eintrag.genre = "Reality"
        # Der Kasten "Neu entdeckt" zeigt die Beschreibung als Folgenangabe
        eintrag.beschreibung = eintrag.folge
        return eintrag

    with ThreadPoolExecutor(max_workers=GLEICHZEITIG) as pool:
        return [e for e in pool.map(_hole, ids) if e]


def hole(shows: list[dict], heute: date, vorschau_tage: int) -> Ergebnis | None:
    """None, wenn kein Schluessel eingetragen ist. ScraperFehler, wenn TMDB
    nicht antwortet oder den Schluessel ablehnt."""
    schluessel = lade_schluessel()
    if not schluessel:
        return None
    tmdb = _Tmdb(schluessel)
    bis = heute + timedelta(days=vorschau_tage - 1)
    ergebnis = Ergebnis()

    zuordnung = _zuordnen(tmdb, shows, heute)
    suchbegriffe = {show["name"]: [show["name"], *show.get("aliases", [])] for show in shows}
    auftraege = sorted({(tmdb_id, name) for name, ids in zuordnung.items() for tmdb_id in ids})

    def _hole(auftrag: tuple[int, str]) -> tuple[str, dict, list[dict]]:
        tmdb_id, name = auftrag
        serie = tmdb.get(f"tv/{tmdb_id}")
        return name, serie, _kommende_folgen(tmdb, serie, heute, heute + timedelta(days=TAGE_DEMNAECHST))

    erledigt: set[int] = set()
    with ThreadPoolExecutor(max_workers=GLEICHZEITIG) as pool:
        for name, serie, folgen in pool.map(_hole, auftraege):
            # Zwei Listennamen koennen auf dieselbe Serie zeigen
            # ("Temptation Island" und "Temptation Island VIP")
            if serie["id"] in erledigt:
                continue
            erledigt.add(serie["id"])
            je_tag: dict[str, list[dict]] = {}
            for folge in folgen:
                je_tag.setdefault(folge["air_date"], []).append(folge)
            for tag, tagesfolgen in je_tag.items():
                datum = date.fromisoformat(tag)
                tagesfolgen.sort(key=lambda f: f["episode_number"])
                erste, letzte = tagesfolgen[0], tagesfolgen[-1]
                if datum <= bis:
                    eintrag = _eintrag(serie, erste, letzte["episode_number"] if len(tagesfolgen) > 1 else None)
                    ergebnis.termine.append((eintrag, suchbegriffe[name] + [serie["name"]]))
                    continue
                folge = erste
                if folge["episode_number"] == 1:
                    ergebnis.demnaechst.append(
                        {
                            "tmdb_id": serie["id"],
                            "staffel": folge["season_number"],
                            "datum": folge["air_date"],
                            "titel": serie["name"],
                            "sender": _plattform(serie),
                            "beschreibung": _beschreibung(serie),
                        }
                    )

    ergebnis.entdeckungen = _entdecken(tmdb, heute)
    logger.info(
        "%s: %d Serien zugeordnet, %d Termine im Zeitraum, %d spaetere Staffelstarts, %d Vorschlaege",
        QUELLE,
        len(auftraege),
        len(ergebnis.termine),
        len(ergebnis.demnaechst),
        len(ergebnis.entdeckungen),
    )
    return ergebnis
