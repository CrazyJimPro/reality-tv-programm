"""Scraper fuer den TV-Spielfilm-Aggregator (tvspielfilm.de).

Liefert - anders als die einzelnen Sender-Seiten - eine Vorschau von bis zu
14 Tagen und deckt alle vier gewuenschten Sender ueber dieselbe Seitenstruktur
ab. Dient hier hauptsaechlich dazu, die Termine der "uebernaechsten Woche"
zu befuellen, die rtl.de nicht mehr anzeigt.

Struktur (Stand September 2026, per Browser verifiziert):
  https://www.tvspielfilm.de/tv-programm/sendungen/rtl,RTL.html?date=2026-09-20

Jede Ausstrahlung steckt in <tr class="hover"> innerhalb <table class="info-table">.
Die Titel-Zelle (td.col-3) enthaelt einen <a class="js-track-link" data-tracking-point='{...JSON...}'>
mit den Feldern channel, broadcastTime (ISO-Zeitstempel, entspricht der lokal
angezeigten Uhrzeit), category1/category2 sowie einem <strong>Titel</strong>.
Dieses JSON-Attribut ist deutlich stabiler als layoutabhaengige CSS-Klassen
und wird deshalb bevorzugt ausgewertet.
"""
from __future__ import annotations

import html as html_lib
import json
import logging
import time as time_module
from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup

from scraper.base import ProgrammEintrag, ScraperFehler, get_html, neue_session

QUELLE = "tvspielfilm.de"

# Sender-Name -> (URL-Slug, Sendercode wie ihn tvspielfilm intern verwendet)
SENDER_SLUGS = {
    "RTL": "rtl,RTL",
    "VOX": "vox,VOX",
    "Sat.1": "sat1,SAT1",
    "ProSieben": "prosieben,PRO7",
}

TAGE_IM_VORAUS = 14
WARTEZEIT_ZWISCHEN_REQUESTS_SEK = 0.4

logger = logging.getLogger(__name__)


def _parse_tag(html_text: str, sender: str, tag: date) -> list[ProgrammEintrag]:
    soup = BeautifulSoup(html_text, "html.parser")
    eintraege: list[ProgrammEintrag] = []
    for row in soup.select("table.info-table tr.hover"):
        title_cell = row.find("td", class_="col-3")
        if title_cell is None:
            continue
        link = title_cell.find("a", attrs={"data-tracking-point": True})
        strong = title_cell.find("strong")
        if link is None or strong is None:
            continue
        try:
            info = json.loads(html_lib.unescape(link["data-tracking-point"]))
        except (KeyError, json.JSONDecodeError):
            continue
        broadcast_time = info.get("broadcastTime")
        if not broadcast_time:
            continue
        try:
            uhrzeit = datetime.fromisoformat(broadcast_time).time()
        except ValueError:
            continue
        genre_teile = [t for t in (info.get("category1"), info.get("category2")) if t]
        eintraege.append(
            ProgrammEintrag(
                quelle=QUELLE,
                sender=sender,
                datum=tag,
                uhrzeit=uhrzeit,
                titel=strong.get_text(strip=True),
                genre=" / ".join(genre_teile) or None,
            )
        )
    return eintraege


def fetch() -> list[ProgrammEintrag]:
    """Holt das Programm aller vier Sender fuer die naechsten TAGE_IM_VORAUS Tage."""
    session = neue_session()
    alle_eintraege: list[ProgrammEintrag] = []
    heute = date.today()

    for sender, slug in SENDER_SLUGS.items():
        for offset in range(TAGE_IM_VORAUS):
            tag = heute + timedelta(days=offset)
            url = f"https://www.tvspielfilm.de/tv-programm/sendungen/{slug}.html?date={tag.isoformat()}"
            try:
                html_text = get_html(session, url)
            except ScraperFehler as exc:
                logger.warning("%s: Tag %s fuer %s konnte nicht geladen werden (%s)", QUELLE, tag, sender, exc)
                continue
            alle_eintraege.extend(_parse_tag(html_text, sender, tag))
            time_module.sleep(WARTEZEIT_ZWISCHEN_REQUESTS_SEK)

    if not alle_eintraege:
        raise ScraperFehler(f"{QUELLE}: keine Daten von keinem Sender erhalten")

    return alle_eintraege
