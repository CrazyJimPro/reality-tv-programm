"""Gleicht gemergte Sendungen gegen die feste Liste bekannter Reality-Formate ab."""
from __future__ import annotations

import json
import re
from pathlib import Path

from rapidfuzz import fuzz

from scraper.merge import MergedEintrag

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PFAD = PROJEKT_ROOT / "config" / "reality_shows.json"
CONFIG_VORLAGE_PFAD = PROJEKT_ROOT / "config" / "reality_shows.default.json"

AEHNLICHKEIT_SCHWELLE = 88


# Bindestrich, Gedankenstrich, Geviertstrich: rtl.de schreibt "First Dates -
# Ein Tisch fuer zwei", tvspielfilm.de dieselbe Sendung mit "–"
STRICHE = str.maketrans({"-": " ", "–": " ", "—": " "})


def _normalisiert(text: str) -> str:
    return " ".join(text.lower().translate(STRICHE).replace("!", "").split())


def lade_shows_config(config_pfad: Path = CONFIG_PFAD) -> dict:
    """Laedt die aktive Sendungsliste. Existiert sie noch nicht (frische
    Installation), wird sie einmalig aus der versionierten Vorlage
    reality_shows.default.json angelegt. config_pfad selbst ist bewusst
    NICHT im Git-Repo verfolgt (siehe .gitignore) - so ueberschreibt eine
    Projekt-Auffrischung (Selbst-Update von start.bat/start.sh) niemals
    die persoenliche Auswahl des Nutzers."""
    if not config_pfad.exists() and CONFIG_VORLAGE_PFAD.exists():
        config_pfad.write_text(CONFIG_VORLAGE_PFAD.read_text(encoding="utf-8"), encoding="utf-8")
    return json.loads(config_pfad.read_text(encoding="utf-8"))


def speichere_shows_config(daten: dict, config_pfad: Path = CONFIG_PFAD) -> None:
    config_pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lade_show_namen(config_pfad: Path = CONFIG_PFAD) -> list[str]:
    daten = lade_shows_config(config_pfad)
    namen: list[str] = []
    for show in daten.get("shows", []):
        namen.append(show["name"])
        namen.extend(show.get("aliases", []))
    return namen


def _passt_zu_liste(titel: str, normalisierte_namen: list[str]) -> bool:
    """Ein Titel passt, wenn der Name darin steht ("Bauer sucht Frau
    International") oder beide insgesamt fast gleich sind
    (Tippfehler, andere Wortreihenfolge).

    Bewusst NICHT token_set_ratio: das vergleicht nur die gemeinsamen Woerter
    und gab "Das A-Team" gegen "#CoupleChallenge - Das staerkste Team gewinnt"
    knapp 89 Punkte - zwei Allerweltswoerter reichten fuer einen Treffer."""
    titel_norm = _normalisiert(titel)
    for name_norm in normalisierte_namen:
        if not name_norm:
            continue
        if name_norm in titel_norm:
            return True
        if fuzz.token_sort_ratio(titel_norm, name_norm) >= AEHNLICHKEIT_SCHWELLE:
            return True
    return False


def normalisiert(text: str) -> str:
    """Vergleichsform eines Titels (Kleinschreibung, ohne Bindestriche/Ausrufezeichen)."""
    return _normalisiert(text)


def sendungsname(titel: str) -> str:
    """Titel ohne Untertitel, als Eintrag fuer die Sendungsliste:
    "Dating ohne Grenzen: Die letzte Chance" -> "Dating ohne Grenzen".
    Damit passt der Eintrag auch auf die naechste Staffel mit anderem
    Untertitel. Bleibt nur ein kurzes Einzelwort uebrig ("Berlin - Tag &
    Nacht", "SOS - Retter im Einsatz"), wird der ganze Titel behalten - so
    ein Wort taucht auch in fremden Sendungen auf."""
    vorne = re.split(r"\s+[-–—]\s+|:\s+", titel, maxsplit=1)[0].strip()
    if len(vorne.split()) >= 2 or len(vorne) >= 10:
        return vorne
    return titel


def passt_zu_namen(titel: str, namen: list[str]) -> bool:
    """Derselbe Abgleich wie im Scrape-Lauf, fuer einen einzelnen Titel -
    damit der Kasten "Neu entdeckt" genau das als bekannt ansieht, was der
    Filter auch in die Uebersicht durchlassen wuerde."""
    return _passt_zu_liste(titel, [_normalisiert(name) for name in namen])


def filtere_reality_shows(
    eintraege: list[MergedEintrag], config_pfad: Path = CONFIG_PFAD
) -> list[MergedEintrag]:
    show_namen = [_normalisiert(name) for name in lade_show_namen(config_pfad)]
    return [e for e in eintraege if _passt_zu_liste(e.titel, show_namen)]
