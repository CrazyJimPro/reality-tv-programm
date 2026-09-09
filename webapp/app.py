"""Lokale Flask-Web-App: zeigt die gespeicherten Reality-TV-Termine an.

Start (aus dem Projektverzeichnis):
    python webapp/app.py
Danach im Browser: http://127.0.0.1:5000
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJEKT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJEKT_ROOT))

from flask import Flask, render_template  # noqa: E402

from scraper.storage import DB_PFAD, hole_programme, hole_quellen_status  # noqa: E402

app = Flask(__name__)

VORSCHAU_TAGE = 14
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _woche_gruppieren(rows: list[dict], ab: date, bis: date) -> list[dict]:
    """Gruppiert Zeilen nach Tag, sortiert und mit lesbarem Wochentag."""
    nach_tag: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        nach_tag[row["datum"]].append(row)

    tage = []
    tag = ab
    while tag <= bis:
        iso = tag.isoformat()
        eintraege = sorted(nach_tag.get(iso, []), key=lambda r: (r["uhrzeit"], r["sender"]))
        tage.append(
            {
                "datum": tag,
                "wochentag": WOCHENTAGE[tag.weekday()],
                "eintraege": eintraege,
            }
        )
        tag += timedelta(days=1)
    return tage


@app.route("/")
def index():
    heute = date.today()
    naechste_woche_bis = heute + timedelta(days=6)
    uebernaechste_woche_ab = heute + timedelta(days=7)
    uebernaechste_woche_bis = heute + timedelta(days=VORSCHAU_TAGE - 1)

    rows = hole_programme(ab_datum=heute, bis_datum=uebernaechste_woche_bis, db_pfad=DB_PFAD)

    naechste_woche = _woche_gruppieren(rows, heute, naechste_woche_bis)
    uebernaechste_woche = _woche_gruppieren(rows, uebernaechste_woche_ab, uebernaechste_woche_bis)

    status = hole_quellen_status(db_pfad=DB_PFAD)

    return render_template(
        "index.html",
        naechste_woche=naechste_woche,
        uebernaechste_woche=uebernaechste_woche,
        status=status,
        heute=heute,
        anzahl_gesamt=len(rows),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
