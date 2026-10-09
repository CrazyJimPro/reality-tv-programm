"""Folgen wiedererkennen: fuer das Kennzeichen "Wiederholung" und das
"Gesehen"-Haekchen in der Uebersicht.

tvspielfilm.de kennzeichnet Wiederholungen nicht. Die Detailseiten nennen
aber Staffel/Folge und den Folgentitel (scraper/sources/tvspielfilm.py:
folgen_ergaenzen). Laeuft dieselbe Folge mehrmals, gilt eine Ausstrahlung als
Hauptausstrahlung, alle anderen als Wiederholung.

Hauptausstrahlung ist die frueheste ausserhalb der Nacht (0-6 Uhr). Nur
"die frueheste" waere oft verkehrt herum: Spartensender zeigen eine Folge
nachts um 01:25 und dieselbe abends um 18:35 - "Wiederholungen ausblenden"
wuerde dann den Abendtermin verstecken. Nur wenn eine Folge ausschliesslich
nachts laeuft, zaehlt die frueheste Nachtausstrahlung.

Beruecksichtigt wird alles, was in der Datenbank steht - vergangene Termine
bleiben dort stehen, eine Folge von letzter Woche zaehlt also mit. Was schon
vor dem ersten Datenabruf gelaufen ist, kann naturgemaess nicht erkannt werden.
"""
from __future__ import annotations

import re

from scraper.filter import normalisiert

# "Staffel 7, Folge 2/13", "Folge 86" - die Gesamtzahl hinter dem Schraegstrich
# gehoert nicht zur Folge selbst
FOLGE_MUSTER = re.compile(r"(?:Staffel\s*(\d+)\D*?)?Folge\s*(\d+)", re.IGNORECASE)

NACHT_BIS = "06:00"


def folgen_schluessel(titel: str, folge: str | None, folgentitel: str | None) -> str | None:
    """Gleich fuer alle Ausstrahlungen derselben Folge, sonst verschieden.
    None, wenn die Quelle weder Folgennummer noch Folgentitel nennt."""
    sendung = normalisiert(titel)
    if folge:
        treffer = FOLGE_MUSTER.search(folge)
        if treffer:
            return f"{sendung}|s{treffer.group(1) or ''}f{treffer.group(2)}"
    if folgentitel:
        return f"{sendung}|{normalisiert(folgentitel)}"
    return None


def gesehen_schluessel(row: dict) -> str:
    """Je Folge, falls erkennbar - sonst je einzelner Ausstrahlung."""
    return folgen_schluessel(row["titel"], row.get("folge"), row.get("folgentitel")) or (
        f"termin|{row['sender']}|{row['datum']}|{row['uhrzeit']}|{row['titel']}"
    )


def _rang(row: dict) -> tuple:
    return (row["uhrzeit"] < NACHT_BIS, row["datum"], row["uhrzeit"])


def hauptausstrahlungen(verlauf: list[dict]) -> dict[str, dict]:
    """Je Folgen-Schluessel die Hauptausstrahlung (siehe Moduldoku)."""
    haupt: dict[str, dict] = {}
    for row in verlauf:
        schluessel = folgen_schluessel(row["titel"], row.get("folge"), row.get("folgentitel"))
        if schluessel is None:
            continue
        bisher = haupt.get(schluessel)
        if bisher is None or _rang(row) < _rang(bisher):
            haupt[schluessel] = row
    return haupt


def hauptausstrahlung_von(row: dict, haupt: dict[str, dict]) -> dict | None:
    """Die Hauptausstrahlung derselben Folge, falls row eine Wiederholung ist."""
    schluessel = folgen_schluessel(row["titel"], row.get("folge"), row.get("folgentitel"))
    if schluessel is None or schluessel not in haupt:
        return None
    hauptrow = haupt[schluessel]
    if (hauptrow["sender"], hauptrow["datum"], hauptrow["uhrzeit"]) == (row["sender"], row["datum"], row["uhrzeit"]):
        return None
    return hauptrow
