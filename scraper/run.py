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
from scraper.filter import filtere_reality_shows
from scraper.merge import merge
from scraper.sources import rtl, tvspielfilm
from scraper.storage import (
    hole_quellen_status,
    init_db,
    markiere_quelle_erfolg,
    markiere_quelle_fehler,
    speichere_eintraege,
)

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
LOG_PFAD = PROJEKT_ROOT / "logs" / "scraper.log"

# Deckt "naechste Woche" + "uebernaechste Woche" ab wie im Plan gefordert.
VORSCHAU_TAGE = 14

QUELLEN_MODULE = [rtl, tvspielfilm]


def _logging_einrichten() -> None:
    LOG_PFAD.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_PFAD, encoding="utf-8"), logging.StreamHandler()],
    )


def main() -> None:
    _logging_einrichten()
    logger = logging.getLogger("run")
    logger.info("Scrape-Lauf gestartet")

    init_db()

    alle_rohdaten = []
    for modul in QUELLEN_MODULE:
        try:
            eintraege = modul.fetch()
        except ScraperFehler as exc:
            logger.error("Quelle %s fehlgeschlagen: %s", modul.QUELLE, exc)
            markiere_quelle_fehler(modul.QUELLE, str(exc))
            continue
        logger.info("Quelle %s lieferte %d Rohdatensaetze", modul.QUELLE, len(eintraege))
        markiere_quelle_erfolg(modul.QUELLE)
        alle_rohdaten.extend(eintraege)

    if not alle_rohdaten:
        logger.critical("Alle Quellen sind fehlgeschlagen - bestehende Daten in der DB bleiben unveraendert.")
        return

    gemergt = merge(alle_rohdaten)
    logger.info("%d Ausstrahlungen nach Merge/Dedupe", len(gemergt))

    reality = filtere_reality_shows(gemergt)
    logger.info("%d davon erkannt als Reality-TV (siehe config/reality_shows.json)", len(reality))

    heute = date.today()
    bis = heute + timedelta(days=VORSCHAU_TAGE - 1)
    speichere_eintraege(reality, ab_datum=heute, bis_datum=bis, db_pfad=PROJEKT_ROOT / "data" / "programm.db")
    logger.info("Gespeichert fuer Zeitraum %s bis %s", heute, bis)

    status = hole_quellen_status()
    for eintrag in status:
        logger.info("Quellen-Status: %s", eintrag)

    logger.info("Scrape-Lauf beendet")


if __name__ == "__main__":
    main()
