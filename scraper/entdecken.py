"""Findet Reality-Formate im Fernsehprogramm, die (noch) nicht in der
Sendungsliste stehen - fuer den Kasten "Neu entdeckt" auf der Startseite.

Grundlage ist das Genre, das tvspielfilm.de zu jeder Ausstrahlung liefert
(category1/category2, siehe scraper/sources/tvspielfilm.py). Die Genres sind
dort sehr fein unterteilt ("Realitysoap", "Kuppelshow", "Goldsuchersoap",
"Gerichtssoap" ...). Daraus werden zwei Stufen:

  reality - eindeutig: Genre enthaelt "Reality", "Dating" oder "Kuppel"
  soap    - weitere Doku-Soaps: alles mit "...soap" bzw. "Dokusop", ohne
            fiktionale Serien (GZSZ, Unter uns) und ohne gespielte Gerichts-
            und Ermittler-Formate, die sonst alles andere ueberdecken wuerden

Gespeichert werden alle Kandidaten samt Terminen (Tabelle entdeckungen), auch
solche, die schon in der Liste stehen. Ausgesiebt wird erst beim Anzeigen
gegen die *aktuelle* Liste - so verschwindet ein gerade hinzugefuegter oder
ausgeblendeter Titel sofort, ohne neuen Datenabruf.
"""
from __future__ import annotations

from datetime import date, datetime

from scraper.filter import normalisiert, passt_zu_namen
from scraper.merge import MergedEintrag

STUFE_REALITY = "reality"
STUFE_SOAP = "soap"

REALITY_STICHWORTE = ("realit", "dating", "kuppel")
SOAP_STICHWORTE = ("soap", "dokusop")
# Ganze Genre-Teile, die fiktionale Serien bezeichnen
SOAP_FIKTION = {"soap", "daily soap"}
# Gespielte Formate (Scripted Reality) - zusammen ueber 150 Ausstrahlungen
# in zwei Wochen, alle von denselben paar Sendungen
SOAP_AUSNAHMEN = ("gericht", "ermittler", "anwalt")


def stufe(genre: str | None) -> str | None:
    """Ordnet ein tvspielfilm-Genre wie "Realitysoap / Reality" einer Stufe zu."""
    if not genre:
        return None
    teile = [t.strip().lower() for t in genre.split("/") if t.strip()]
    if any(stichwort in teil for teil in teile for stichwort in REALITY_STICHWORTE):
        return STUFE_REALITY
    if any(ausnahme in teil for teil in teile for ausnahme in SOAP_AUSNAHMEN):
        return None
    if any(stichwort in teil for teil in teile if teil not in SOAP_FIKTION for stichwort in SOAP_STICHWORTE):
        return STUFE_SOAP
    return None


def finde_kandidaten(eintraege: list[MergedEintrag]) -> list[tuple[MergedEintrag, str]]:
    """Alle Ausstrahlungen, deren Genre zu einer Stufe passt."""
    kandidaten = []
    for eintrag in eintraege:
        gefundene_stufe = stufe(eintrag.genre)
        if gefundene_stufe:
            kandidaten.append((eintrag, gefundene_stufe))
    return kandidaten


def fuer_anzeige(
    rows: list[dict],
    show_namen: list[str],
    ausgeblendet: list[str],
    jetzt: datetime | None = None,
) -> dict[str, list[dict]]:
    """Fasst die gespeicherten Kandidaten-Termine je Titel zusammen und
    laesst weg, was schon in der Liste steht oder ausgeblendet wurde.

    Liefert {"reality": [...], "soap": [...]}, je Eintrag: titel, genre,
    sender (Liste), anzahl, naechster (datetime oder None, falls alle
    Termine heute schon vorbei sind)."""
    jetzt = jetzt or datetime.now()
    ausgeblendet_norm = {normalisiert(t) for t in ausgeblendet}

    gruppen: dict[str, dict] = {}
    for row in rows:
        schluessel = normalisiert(row["titel"])
        gruppe = gruppen.setdefault(
            schluessel,
            {"titel": row["titel"], "genre": row["genre"], "stufe": row["stufe"], "sender": [], "anzahl": 0, "naechster": None},
        )
        gruppe["anzahl"] += 1
        if row["sender"] not in gruppe["sender"]:
            gruppe["sender"].append(row["sender"])
        # Kommt derselbe Titel in beiden Stufen vor, zaehlt die eindeutigere
        if row["stufe"] == STUFE_REALITY:
            gruppe["stufe"] = STUFE_REALITY
        termin = datetime.combine(date.fromisoformat(row["datum"]), datetime.strptime(row["uhrzeit"], "%H:%M").time())
        if termin >= jetzt and (gruppe["naechster"] is None or termin < gruppe["naechster"]):
            gruppe["naechster"] = termin

    ergebnis: dict[str, list[dict]] = {STUFE_REALITY: [], STUFE_SOAP: []}
    for schluessel, gruppe in gruppen.items():
        if schluessel in ausgeblendet_norm or passt_zu_namen(gruppe["titel"], show_namen):
            continue
        ergebnis[gruppe["stufe"]].append(gruppe)

    for liste in ergebnis.values():
        # Bald Laufendes zuerst, bereits Vorbeigelaufenes ans Ende
        liste.sort(key=lambda g: (g["naechster"] is None, g["naechster"] or jetzt, g["titel"].lower()))
    return ergebnis
