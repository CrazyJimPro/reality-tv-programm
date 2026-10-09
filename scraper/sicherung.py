"""Sicherung und Wiederherstellung der persoenlichen Sendungsliste.

Gesichert wird genau das, was sich nicht von selbst wiederbeschafft: die
Auswahl in config/reality_shows.json (welche Sendungen ueberhaupt als
Reality-TV erkannt werden, samt ihren Aliasen). **Nicht** gesichert wird
data/programm.db - die geholten Sendetermine sind Abruf-Ergebnisse, die der
naechste Lauf ohnehin neu holt; sie in eine Sicherung zu packen wuerde nur
alte Termine wieder einschleppen.

Aufbau und Verhalten sind bewusst dieselben wie im Schwesterprojekt
streaming-info: Sicherung als Download aus der App heraus, Einspielen mit
freier Dateiauswahl (damit auch von USB-Stick oder Netzlaufwerk, ohne fest
verdrahtete Suchpfade), Sicherheitskopie des bisherigen Standes vor dem
Ueberschreiben.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scraper.filter import CONFIG_PFAD, lade_shows_config, speichere_shows_config

# Kennung im Dateikopf: verhindert, dass beim Einspielen irgendeine beliebige
# JSON-Datei als Sicherung durchgeht - oder eine des Schwesterprojekts.
KENNUNG = "reality-tv-sicherung"

# Steigt nur, wenn sich der Aufbau der Datei so aendert, dass aeltere Staende
# nicht mehr ohne Umbau gelesen werden koennen. Eine Sicherung mit hoeherer
# Nummer stammt aus einer neueren Programmfassung und wird abgelehnt, statt
# halb verstanden eingespielt zu werden.
FORMAT_VERSION = 1

# Wie viele Sicherheitskopien (der Stand *vor* einem Einspielen) aufgehoben
# werden. Der Dateiname sortiert dank JJJJ-MM-TT-HHMMSS-Schema chronologisch.
SICHERHEITSKOPIEN_BEHALTEN = 10


class SicherungsFehler(Exception):
    """Die uebergebene Datei taugt nicht als Sicherung. Der Text ist dafuer
    gedacht, dem Nutzer unveraendert angezeigt zu werden."""


def erstelle_sicherung(version: str = "unbekannt") -> dict:
    """Baut den Inhalt einer Sicherungsdatei aus dem *gespeicherten* Stand."""
    daten = lade_shows_config(CONFIG_PFAD)
    return {
        "typ": KENNUNG,
        "format": FORMAT_VERSION,
        "erstellt_am": datetime.now().isoformat(timespec="seconds"),
        "erstellt_mit_version": version,
        "shows": daten.get("shows", []),
        # Unter "Neu entdeckt" ausgeblendete Titel - ebenfalls Handarbeit.
        # Kam ohne Formatwechsel dazu: aeltere Programmfassungen lesen das
        # Feld schlicht nicht mit.
        "ausgeblendet": daten.get("ausgeblendet", []),
    }


def sicherungs_dateiname(zeitpunkt: datetime | None = None) -> str:
    """reality-tv-programm-JJJJ-MM-TT.json - Ortszeit, nicht UTC.

    Mit UTC truege eine Sicherung kurz nach Mitternacht das Datum von gestern.
    """
    jetzt = zeitpunkt or datetime.now()
    return f"reality-tv-programm-{jetzt:%Y-%m-%d}.json"


def _shows_bereinigen(roh: object) -> tuple[list[dict], int]:
    """Filtert die Sendungsliste auf brauchbare Eintraege.

    Liefert (Sendungen, Anzahl verworfener). Verworfen wird still, aber
    gezaehlt - lieber eine Sicherung teilweise einspielen und es sagen, als
    sie wegen eines kaputten Eintrags ganz abzulehnen.
    """
    if not isinstance(roh, list):
        return [], 0
    shows: list[dict] = []
    verworfen = 0
    for eintrag in roh:
        if not isinstance(eintrag, dict):
            verworfen += 1
            continue
        name = eintrag.get("name")
        if not isinstance(name, str) or not name.strip():
            verworfen += 1
            continue
        name = name.strip()
        roh_aliases = eintrag.get("aliases", [])
        aliases = (
            [a.strip() for a in roh_aliases if isinstance(a, str) and a.strip()]
            if isinstance(roh_aliases, list)
            else []
        )
        # Dieselbe Sendung kann in einer von Hand bearbeiteten Datei mehrfach
        # stehen - Gross-/Kleinschreibung spielt beim Abgleich ohnehin keine
        # Rolle, also hier genauso wenig.
        if any(s["name"].lower() == name.lower() for s in shows):
            continue
        shows.append({"name": name, "aliases": aliases})
    return shows, verworfen


def lies_sicherung(rohdaten: bytes | str) -> dict:
    """Prueft eine hochgeladene Datei und gibt den bereinigten Inhalt zurueck.

    Wirft SicherungsFehler mit einem fuer den Nutzer lesbaren Text, wenn die
    Datei keine Sicherung dieses Programms ist.
    """
    if isinstance(rohdaten, bytes):
        # utf-8-sig: schluckt ein BOM, falls die Datei zwischendurch in einem
        # Editor gespeichert wurde, und liest sonst normales UTF-8.
        try:
            rohdaten = rohdaten.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise SicherungsFehler("Die Datei ist keine Textdatei - wurde vielleicht die falsche ausgewählt?")

    try:
        daten = json.loads(rohdaten)
    except json.JSONDecodeError:
        raise SicherungsFehler("Die Datei lässt sich nicht lesen. Erwartet wird eine JSON-Sicherung dieses Programms.")

    if not isinstance(daten, dict) or daten.get("typ") != KENNUNG:
        raise SicherungsFehler(
            "Das ist keine Reality-TV-Sicherung. Erwartet wird eine Datei wie reality-tv-programm-2026-09-28.json."
        )

    try:
        format_version = int(daten.get("format", 0))
    except (TypeError, ValueError):
        format_version = 0
    if format_version > FORMAT_VERSION:
        raise SicherungsFehler(
            "Die Sicherung stammt aus einer neueren Programmfassung. Bitte zuerst das Programm aktualisieren."
        )

    shows, verworfen = _shows_bereinigen(daten.get("shows"))
    if not shows:
        raise SicherungsFehler("In der Sicherung steht keine einzige brauchbare Sendung.")

    notizen: list[str] = []
    if verworfen:
        notizen.append(f"{verworfen} unlesbare(r) Eintrag übergangen")

    # Fehlt das Feld (Sicherung von vor v1.8.0), bleibt die aktuelle
    # Ausblend-Liste beim Einspielen unangetastet - None statt [].
    roh_ausgeblendet = daten.get("ausgeblendet")
    ausgeblendet = (
        [t.strip() for t in roh_ausgeblendet if isinstance(t, str) and t.strip()]
        if isinstance(roh_ausgeblendet, list)
        else None
    )

    return {
        "shows": shows,
        "ausgeblendet": ausgeblendet,
        "erstellt_am": str(daten.get("erstellt_am", "")),
        "erstellt_mit_version": str(daten.get("erstellt_mit_version", "")),
        "notizen": notizen,
    }


def sicherheitskopie_anlegen(version: str = "unbekannt", ordner: Path | None = None) -> Path | None:
    """Legt den *bisherigen* Stand als vor-wiederherstellung-<Zeit>.json ab.

    Bewusst im selben Sicherungsformat: die Kopie laesst sich damit genauso
    wieder einspielen wie eine normale Sicherung - eine Rueckfahrkarte, die
    man nicht lesen kann, waere keine. Gibt es noch keine Sendungsliste
    (frische Installation), gibt es auch nichts zu sichern: None.
    """
    ordner = ordner or CONFIG_PFAD.parent
    if not CONFIG_PFAD.exists():
        return None
    ordner.mkdir(parents=True, exist_ok=True)
    ziel = ordner / f"vor-wiederherstellung-{datetime.now():%Y-%m-%d-%H%M%S}.json"
    ziel.write_text(
        json.dumps(erstelle_sicherung(version), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Aelteste wegraeumen, damit der Ordner nicht endlos voll laeuft.
    alle = sorted(ordner.glob("vor-wiederherstellung-*.json"))
    for veraltet in alle[:-SICHERHEITSKOPIEN_BEHALTEN]:
        veraltet.unlink(missing_ok=True)
    return ziel


def spiele_sicherung_ein(rohdaten: bytes | str, version: str = "unbekannt") -> dict:
    """Prueft die Datei, sichert den bisherigen Stand und spielt sie ein.

    Erst wenn die Pruefung durch ist, wird irgendetwas geschrieben - eine
    abgelehnte Datei laesst den bisherigen Stand voellig unberuehrt.
    """
    gepruefte = lies_sicherung(rohdaten)

    sicherheitskopie = sicherheitskopie_anlegen(version)

    # Die uebrigen Felder der Konfigurationsdatei (z.B. "_hinweis") bleiben
    # erhalten - ersetzt wird nur die Sendungsliste (und die Ausblend-Liste,
    # sofern die Sicherung eine enthaelt).
    daten = lade_shows_config(CONFIG_PFAD)
    daten["shows"] = sorted(gepruefte["shows"], key=lambda s: s["name"].lower())
    if gepruefte["ausgeblendet"] is not None:
        daten["ausgeblendet"] = sorted(gepruefte["ausgeblendet"], key=str.lower)
    # Wer eine Sicherung einspielt, hat sich eingerichtet: der Wegweiser fuer
    # frische Installationen auf der Startseite ist damit erledigt.
    daten["einrichtung_erledigt"] = True
    speichere_shows_config(daten, CONFIG_PFAD)

    return {
        "sendungen": len(gepruefte["shows"]),
        "erstellt_am": gepruefte["erstellt_am"],
        "sicherheitskopie": sicherheitskopie.name if sicherheitskopie else None,
        "notizen": gepruefte["notizen"],
    }
