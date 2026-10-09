"""Hauptskript: holt alle Quellen, merged/filtert sie und speichert das Ergebnis.

Wird von der Web-App aufgerufen (einmal beim Start der App und beim Klick
auf "Jetzt aktualisieren", siehe webapp/app.py). Kann auch manuell
gestartet werden:

    python -m scraper.run
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from scraper.base import ScraperFehler
from scraper.entdecken import STUFE_REALITY, finde_kandidaten
from scraper.filter import filtere_reality_shows, lade_shows_config, passt_zu_namen
from scraper.merge import MergedEintrag, merge
from scraper.sources import rtl, rtlplus, tmdb, tvspielfilm
from scraper.storage import (
    hole_quellen_status,
    init_db,
    loesche_quelle_status,
    markiere_quelle_erfolg,
    markiere_quelle_fehler,
    speichere_demnaechst,
    speichere_eintraege,
    speichere_entdeckungen,
)

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
LOG_PFAD = PROJEKT_ROOT / "logs" / "scraper.log"

# Deckt "naechste Woche" + "uebernaechste Woche" ab wie im Plan gefordert.
VORSCHAU_TAGE = 14

# Die Fernseh-Quellen werden gegen die Sendungsliste gefiltert. rtlplus sucht
# schon selbst nach den Namen der Liste (und liefert Titel, die der Filter
# nicht immer wiedererkennt, z.B. "#CoupleChallenge - Das staerkste Team
# gewinnt" gegen "Couple Challenge") und laeuft deshalb daran vorbei.
QUELLEN_MODULE = [rtl, tvspielfilm, rtlplus]


def _logging_einrichten() -> None:
    LOG_PFAD.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_PFAD, encoding="utf-8"), logging.StreamHandler()],
    )


def _noch_nicht_bekannt(
    tmdb_termine: list[tuple[MergedEintrag, list[str]]], bekannte: list[MergedEintrag]
) -> list[MergedEintrag]:
    """TMDB-Termine, die nicht schon als Fernseh- oder RTL+-Termin dastehen.

    TMDB kennt auch die taeglichen Folgen von Promi Big Brother oder dem
    Sommerhaus - die stehen mit Uhrzeit und Sender ohnehin im Programm. Uebrig
    bleiben, was nur gestreamt wird oder dort frueher startet. Ein Tag
    Spielraum, weil TMDB das Datum gelegentlich um einen Tag verschoben fuehrt."""
    uebrig = []
    for eintrag, begriffe in tmdb_termine:
        if not any(
            abs((bekannt.datum - eintrag.datum).days) <= 1 and passt_zu_namen(bekannt.titel, begriffe)
            for bekannt in bekannte
        ):
            uebrig.append(eintrag)
    return uebrig


def main() -> None:
    _logging_einrichten()
    logger = logging.getLogger("run")
    logger.info("Scrape-Lauf gestartet")

    init_db()

    tv_rohdaten = []
    streaming_rohdaten = []
    ausgefallene_sender = []
    for modul in QUELLEN_MODULE:
        try:
            eintraege = modul.fetch()
        except ScraperFehler as exc:
            logger.error("Quelle %s fehlgeschlagen: %s", modul.QUELLE, exc)
            markiere_quelle_fehler(modul.QUELLE, str(exc))
            if modul is rtlplus:
                ausgefallene_sender.append(rtlplus.SENDER)
            continue
        logger.info("Quelle %s lieferte %d Rohdatensaetze", modul.QUELLE, len(eintraege))
        markiere_quelle_erfolg(modul.QUELLE)
        (streaming_rohdaten if modul is rtlplus else tv_rohdaten).extend(eintraege)

    # Ohne frische Fernsehdaten wird nichts ersetzt - sonst wuerde ein Lauf, bei
    # dem nur RTL+ antwortet, das gespeicherte Fernsehprogramm wegraeumen.
    if not tv_rohdaten:
        logger.critical("Alle Fernseh-Quellen sind fehlgeschlagen - bestehende Daten in der DB bleiben unveraendert.")
        return

    gemergt = merge(tv_rohdaten)
    logger.info("%d Ausstrahlungen nach Merge/Dedupe", len(gemergt))

    reality = filtere_reality_shows(gemergt)
    logger.info("%d davon erkannt als Reality-TV (siehe config/reality_shows.json)", len(reality))

    # Staffel/Folge und Folgentitel fuer die Erkennung von Wiederholungen und
    # das "Gesehen"-Haekchen je Folge - nur fuer die gefundenen Sendungen.
    tvspielfilm.folgen_ergaenzen(reality)
    logger.info("%d davon mit Folgenangabe", sum(1 for e in reality if e.folge or e.folgentitel))

    heute = date.today()
    bis = heute + timedelta(days=VORSCHAU_TAGE - 1)

    # RTL+-Termine liegen teils Monate voraus (Folgenliste) - gespeichert wird nur
    # der angezeigte Zeitraum, der Rest kommt beim naechsten Lauf von selbst.
    streaming = [e for e in merge(streaming_rohdaten) if heute <= e.datum <= bis]
    logger.info("%d RTL+-Termine im Zeitraum %s bis %s", len(streaming), heute, bis)

    # Streaming- und Staffelstarts laut TMDB - nur mit Schluessel (Einstellungen)
    tmdb_ergebnis = None
    tmdb_termine: list[MergedEintrag] = []
    behalte_quellen: list[str] = []
    try:
        tmdb_ergebnis = tmdb.hole(lade_shows_config().get("shows", []), heute, VORSCHAU_TAGE)
    except ScraperFehler as exc:
        logger.error("Quelle %s fehlgeschlagen: %s", tmdb.QUELLE, exc)
        markiere_quelle_fehler(tmdb.QUELLE, str(exc))
        behalte_quellen.append(tmdb.QUELLE)
    if tmdb_ergebnis is not None:
        markiere_quelle_erfolg(tmdb.QUELLE)
        tmdb_termine = _noch_nicht_bekannt(tmdb_ergebnis.termine, reality + streaming)
        logger.info("%d TMDB-Termine, die nicht schon im Programm stehen", len(tmdb_termine))
        speichere_demnaechst(tmdb_ergebnis.demnaechst, db_pfad=PROJEKT_ROOT / "data" / "programm.db")
    elif not behalte_quellen:
        # Kein Schluessel (mehr): keine alten Staffelstarts und kein Status-Chip
        # stehen lassen, der sonst nach einem Tag als "veraltet" anschluege
        speichere_demnaechst([], db_pfad=PROJEKT_ROOT / "data" / "programm.db")
        loesche_quelle_status(tmdb.QUELLE)

    gesamt = sorted(reality + streaming + tmdb_termine, key=lambda e: (e.datum, e.uhrzeit, e.sender))

    speichere_eintraege(
        gesamt,
        ab_datum=heute,
        bis_datum=bis,
        db_pfad=PROJEKT_ROOT / "data" / "programm.db",
        behalte_sender=tuple(ausgefallene_sender),
        behalte_quellen=tuple(behalte_quellen),
    )
    logger.info("Gespeichert fuer Zeitraum %s bis %s", heute, bis)

    # Kandidaten fuer "Neu entdeckt" - bewusst ungefiltert, abgeglichen
    # wird erst beim Anzeigen gegen die dann aktuelle Liste.
    kandidaten = [(e, s) for e, s in finde_kandidaten(gemergt) if heute <= e.datum <= bis]
    if tmdb_ergebnis is not None:
        # Kommende Reality bei Joyn, RTL+, Prime Video, Netflix - auch nach
        # den zwei Wochen, der Kasten zeigt dann das Startdatum
        kandidaten += [(e, STUFE_REALITY) for e in tmdb_ergebnis.entdeckungen]
    speichere_entdeckungen(kandidaten, db_pfad=PROJEKT_ROOT / "data" / "programm.db")
    logger.info("%d Ausstrahlungen mit Reality-/Doku-Soap-Genre fuer 'Neu entdeckt'", len(kandidaten))

    status = hole_quellen_status()
    for eintrag in status:
        logger.info("Quellen-Status: %s", eintrag)

    logger.info("Scrape-Lauf beendet")


if __name__ == "__main__":
    main()
