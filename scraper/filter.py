"""Gleicht gemergte Sendungen gegen die feste Liste bekannter Reality-Formate ab."""
from __future__ import annotations

import json
from pathlib import Path

from rapidfuzz import fuzz

from scraper.merge import MergedEintrag

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PFAD = PROJEKT_ROOT / "config" / "reality_shows.json"
CONFIG_VORLAGE_PFAD = PROJEKT_ROOT / "config" / "reality_shows.default.json"

AEHNLICHKEIT_SCHWELLE = 88


def _normalisiert(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").replace("!", "").split())


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
    titel_norm = _normalisiert(titel)
    for name_norm in normalisierte_namen:
        if not name_norm:
            continue
        if name_norm in titel_norm:
            return True
        if fuzz.token_set_ratio(titel_norm, name_norm) >= AEHNLICHKEIT_SCHWELLE:
            return True
    return False


def filtere_reality_shows(
    eintraege: list[MergedEintrag], config_pfad: Path = CONFIG_PFAD
) -> list[MergedEintrag]:
    show_namen = [_normalisiert(name) for name in lade_show_namen(config_pfad)]
    return [e for e in eintraege if _passt_zu_liste(e.titel, show_namen)]
