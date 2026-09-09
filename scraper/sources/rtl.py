"""Scraper fuer die sender-eigene Programmseite von RTL und VOX (rtl.de).

rtl.de zeigt nur ca. 6-7 Tage im Voraus an; bei laenger in der Zukunft
liegenden Datumsangaben liefert die Seite HTTP 404. Das ist erwartetes
Verhalten (keine Fehlermeldung) und wird als normales Ende der verfuegbaren
Tage behandelt, nicht als Scraping-Fehler.

Struktur (Stand September 2026, per Browser verifiziert):
  https://www.rtl.de/fernsehprogramm/2026-09-11/          -> RTL
  https://www.rtl.de/fernsehprogramm/vox/2026-09-11/       -> VOX

Jede Sendung steckt in einem <button class="EpgItem_item__xxxx">, darin:
  <div class="EpgItem_time__xxxx">18:45</div>
  <span class="EpgItem_title__xxxx">RTL Aktuell</span>
  <span class="EpgItem_subtitle__xxxx">Sendung vom 11.09.2026</span>  (meist kein echter Beschreibungstext)

Die Hash-Suffixe der CSS-Modul-Klassen aendern sich bei jedem Build - deshalb
wird per "Klassenname enthaelt Praefix" gesucht statt exakter Klassenvergleich.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup

from scraper.base import ProgrammEintrag, ScraperFehler, get_html, neue_session

logger = logging.getLogger(__name__)

QUELLE = "rtl.de"

# sender-name -> URL-Pfadsegment auf rtl.de (leer = RTL selbst)
SENDER_PFADE = {
    "RTL": "",
    "VOX": "vox/",
}

TAGE_IM_VORAUS = 7
GENERISCHE_SUBTITLE = re.compile(r"^Sendung vom \d{2}\.\d{2}\.\d{4}$")


def _find_by_class_prefix(tag, name, prefix):
    return tag.find(name, class_=lambda c: bool(c) and prefix in c)


def _parse_tag(html: str, sender: str, tag: date) -> list[ProgrammEintrag]:
    soup = BeautifulSoup(html, "html.parser")
    eintraege: list[ProgrammEintrag] = []
    for item in soup.find_all("button", class_=lambda c: bool(c) and "EpgItem_item" in c):
        zeit_el = _find_by_class_prefix(item, "div", "EpgItem_time")
        titel_el = _find_by_class_prefix(item, "span", "EpgItem_title")
        subtitle_el = _find_by_class_prefix(item, "span", "EpgItem_subtitle")
        if zeit_el is None or titel_el is None:
            continue
        zeit_text = zeit_el.get_text(strip=True)
        try:
            uhrzeit = datetime.strptime(zeit_text, "%H:%M").time()
        except ValueError:
            continue
        beschreibung = None
        if subtitle_el is not None:
            subtitle_text = subtitle_el.get_text(strip=True)
            if subtitle_text and not GENERISCHE_SUBTITLE.match(subtitle_text):
                beschreibung = subtitle_text
        eintraege.append(
            ProgrammEintrag(
                quelle=QUELLE,
                sender=sender,
                datum=tag,
                uhrzeit=uhrzeit,
                titel=titel_el.get_text(strip=True),
                beschreibung=beschreibung,
            )
        )
    return eintraege


def fetch() -> list[ProgrammEintrag]:
    """Holt das Programm von RTL und VOX fuer die naechsten TAGE_IM_VORAUS Tage.

    Wirft ScraperFehler nur, wenn *gar keine* Daten geholt werden konnten
    (z.B. Netzwerkausfall am ersten Tag). Erreicht ein Sender lediglich das
    Ende seiner verfuegbaren Vorschau (404), wird das stillschweigend als
    Ende der Schleife gewertet.
    """
    session = neue_session()
    alle_eintraege: list[ProgrammEintrag] = []
    heute = date.today()

    for sender, pfad in SENDER_PFADE.items():
        for offset in range(TAGE_IM_VORAUS):
            tag = heute + timedelta(days=offset)
            url = f"https://www.rtl.de/fernsehprogramm/{pfad}{tag.isoformat()}/"
            try:
                html = get_html(session, url)
            except ScraperFehler as exc:
                if offset == 0:
                    # schon der erste Tag schlaegt fehl -> vermutlich echter Ausfall
                    logger.warning("%s: Sender %s liefert auch am ersten Tag keine Daten (%s)", QUELLE, sender, exc)
                else:
                    logger.info("%s: Sender %s hat ab Tag %s keine weitere Vorschau (%s)", QUELLE, sender, tag, exc)
                break
            alle_eintraege.extend(_parse_tag(html, sender, tag))

    if not alle_eintraege:
        raise ScraperFehler(f"{QUELLE}: keine Daten von keinem Sender erhalten")

    return alle_eintraege
