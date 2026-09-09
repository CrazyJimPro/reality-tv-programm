"""Gemeinsame Datenstrukturen und Hilfsfunktionen fuer alle Scraper-Quellen."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 RealityTV-Privatscraper/1.0"
)
REQUEST_TIMEOUT = 15


@dataclass
class ProgrammEintrag:
    """Eine rohe Ausstrahlung, wie sie von genau einer Quelle geliefert wurde."""

    quelle: str
    sender: str
    datum: date
    uhrzeit: time
    titel: str
    beschreibung: str | None = None
    genre: str | None = None


class ScraperFehler(Exception):
    """Wird geworfen, wenn eine einzelne Quelle nicht gelesen werden konnte."""


def neue_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"})
    return session


def get_html(session: requests.Session, url: str) -> str:
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise ScraperFehler(f"Netzwerkfehler bei {url}: {exc}") from exc
    if response.status_code == 404:
        raise ScraperFehler(f"Seite nicht gefunden (404): {url}")
    if response.status_code >= 400:
        raise ScraperFehler(f"HTTP {response.status_code} bei {url}")
    return response.text
