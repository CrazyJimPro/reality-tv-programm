"""Fuehrt die rohen Eintraege mehrerer Quellen zu einer Sendung pro Ausstrahlung zusammen."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time

from rapidfuzz import fuzz

from scraper.base import ProgrammEintrag

# Sender-eigene Seite ist naeher an der Quelle -> gewinnt bei Titel/Beschreibung,
# falls beide Quellen denselben Termin liefern.
QUELLEN_PRIORITAET = ["rtl.de", "tvspielfilm.de"]

# Zwei Eintraege gelten als dieselbe Ausstrahlung, wenn ihre Startzeiten
# hoechstens so viele Minuten auseinanderliegen UND die Titel-Aehnlichkeit
# den Schwellwert erreicht.
ZEIT_TOLERANZ_MINUTEN = 5
TITEL_AEHNLICHKEIT_SCHWELLE = 85


@dataclass
class MergedEintrag:
    sender: str
    datum: date
    uhrzeit: time
    titel: str
    beschreibung: str | None = None
    genre: str | None = None
    quellen: list[str] = field(default_factory=list)

    @property
    def konfidenz(self) -> str:
        return "hoch" if len(self.quellen) > 1 else "mittel"


def _normalisiert(titel: str) -> str:
    return " ".join(titel.lower().replace("-", " ").split())


def _minuten(t: time) -> int:
    return t.hour * 60 + t.minute


def _quellen_rang(quelle: str) -> int:
    try:
        return QUELLEN_PRIORITAET.index(quelle)
    except ValueError:
        return len(QUELLEN_PRIORITAET)


def merge(eintraege: list[ProgrammEintrag]) -> list[MergedEintrag]:
    """Gruppiert nach (Sender, Datum) und clustert dann Eintraege mit aehnlicher
    Uhrzeit + aehnlichem Titel zu einer gemergten Sendung."""

    nach_tag: dict[tuple[str, date], list[ProgrammEintrag]] = {}
    for eintrag in eintraege:
        nach_tag.setdefault((eintrag.sender, eintrag.datum), []).append(eintrag)

    ergebnis: list[MergedEintrag] = []

    for (_sender, _datum), tag_eintraege in nach_tag.items():
        tag_eintraege.sort(key=lambda e: _minuten(e.uhrzeit))
        cluster: list[list[ProgrammEintrag]] = []
        for eintrag in tag_eintraege:
            ziel_cluster = None
            for bestehendes_cluster in cluster:
                referenz = bestehendes_cluster[0]
                if abs(_minuten(eintrag.uhrzeit) - _minuten(referenz.uhrzeit)) > ZEIT_TOLERANZ_MINUTEN:
                    continue
                aehnlichkeit = fuzz.token_set_ratio(_normalisiert(eintrag.titel), _normalisiert(referenz.titel))
                if aehnlichkeit >= TITEL_AEHNLICHKEIT_SCHWELLE:
                    ziel_cluster = bestehendes_cluster
                    break
            if ziel_cluster is not None:
                ziel_cluster.append(eintrag)
            else:
                cluster.append([eintrag])

        for gruppe in cluster:
            gruppe_sortiert = sorted(gruppe, key=lambda e: _quellen_rang(e.quelle))
            beste = gruppe_sortiert[0]
            beschreibung = next((e.beschreibung for e in gruppe_sortiert if e.beschreibung), None)
            genre = next((e.genre for e in gruppe_sortiert if e.genre), None)
            quellen = sorted({e.quelle for e in gruppe}, key=_quellen_rang)
            ergebnis.append(
                MergedEintrag(
                    sender=beste.sender,
                    datum=beste.datum,
                    uhrzeit=beste.uhrzeit,
                    titel=beste.titel,
                    beschreibung=beschreibung,
                    genre=genre,
                    quellen=quellen,
                )
            )

    ergebnis.sort(key=lambda e: (e.datum, _minuten(e.uhrzeit), e.sender))
    return ergebnis
