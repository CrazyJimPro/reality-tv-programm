"""Lokale Flask-Web-App: zeigt die gespeicherten Reality-TV-Termine an.

Start (aus dem Projektverzeichnis):
    python webapp/app.py
Danach im Browser: http://127.0.0.1:5000
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJEKT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJEKT_ROOT))

from flask import Flask, redirect, render_template, request, url_for  # noqa: E402

from scraper.filter import CONFIG_PFAD, lade_shows_config, speichere_shows_config  # noqa: E402
from scraper.storage import DB_PFAD, hole_programme, hole_quellen_status  # noqa: E402
from vorschlaege import VORSCHLAEGE  # noqa: E402

app = Flask(__name__)

VORSCHAU_TAGE = 14
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

STAFFEL_MUSTER = re.compile(r"Staffel\s*(\d+)", re.IGNORECASE)
FOLGE_MUSTER = re.compile(r"Folge\s*(\d+)", re.IGNORECASE)


def _staffel_folge(beschreibung: str | None) -> str | None:
    """Extrahiert 'Staffel X'/'Folge Y' aus dem Beschreibungstext, falls
    vorhanden (z.B. rtl.de liefert oft "Folge 2" als Untertitel). Liefert
    None, wenn nichts davon im Text erkennbar ist - es wird nichts erfunden,
    nur vorhandene Information sichtbarer gemacht."""
    if not beschreibung:
        return None
    teile = []
    staffel = STAFFEL_MUSTER.search(beschreibung)
    if staffel:
        teile.append(f"Staffel {staffel.group(1)}")
    folge = FOLGE_MUSTER.search(beschreibung)
    if folge:
        teile.append(f"Folge {folge.group(1)}")
    return " · ".join(teile) if teile else None


def _scraper_jetzt_ausfuehren() -> bool:
    """Stoesst einen Scraper-Lauf synchron an (dauert ca. 1-2 Minuten).

    Nutzt denselben Python-Interpreter, unter dem die Web-App laeuft (die
    venv), und ruft scraper/run.py exakt so auf wie start.bat/cron es tun -
    damit gibt es nur einen Codepfad fuer "wie wird gescraped"."""
    ergebnis = subprocess.run(
        [sys.executable, "-m", "scraper.run"],
        cwd=PROJEKT_ROOT,
    )
    return ergebnis.returncode == 0


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
    for row in rows:
        row["staffel_folge"] = _staffel_folge(row.get("beschreibung"))

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
        aktualisiert=request.args.get("aktualisiert") == "1",
    )


@app.route("/aktualisieren", methods=["POST"])
def aktualisieren():
    """Manueller 'Jetzt aktualisieren'-Knopf: scraped sofort, statt auf den
    naechsten automatischen Mo/Do-06:00-Lauf zu warten."""
    _scraper_jetzt_ausfuehren()
    return redirect(url_for("index", aktualisiert=1))


@app.route("/einstellungen", methods=["GET", "POST"])
def einstellungen():
    daten = lade_shows_config(CONFIG_PFAD)
    aktive_shows = daten.get("shows", [])

    if request.method == "POST":
        # Jede Checkbox (Vorschlag oder per "Hinzufuegen"-Knopf clientseitig
        # neu erzeugt) bringt ihre Aliase in einem eigenen versteckten Feld
        # "aliases__<Name>" mit - deshalb reicht ein einziger Speichern-Klick
        # fuer beliebig viele zuvor hinzugefuegte eigene Sendungen.
        gesehen: set[str] = set()
        neue_shows = []
        for name in request.form.getlist("shows"):
            if name in gesehen:
                continue
            gesehen.add(name)
            aliases_raw = request.form.get(f"aliases__{name}", "")
            aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()]
            neue_shows.append({"name": name, "aliases": aliases})

        neue_shows.sort(key=lambda s: s["name"].lower())
        daten["shows"] = neue_shows
        speichere_shows_config(daten, CONFIG_PFAD)
        # Direkt neu scrapen, damit die geaenderte Auswahl sofort in der
        # Uebersicht auftaucht, statt bis zum naechsten Mo/Do-Lauf zu warten.
        _scraper_jetzt_ausfuehren()
        return redirect(url_for("einstellungen", gespeichert=1))

    aktive_namen = {s["name"] for s in aktive_shows}
    vorschlag_namen = {v["name"] for v in VORSCHLAEGE}
    zusaetzliche_aktive = [s for s in aktive_shows if s["name"] not in vorschlag_namen]

    anzeige_liste = list(VORSCHLAEGE) + zusaetzliche_aktive
    anzeige_liste.sort(key=lambda s: s["name"].lower())

    return render_template(
        "einstellungen.html",
        shows=anzeige_liste,
        aktive_namen=aktive_namen,
        gespeichert=request.args.get("gespeichert") == "1",
    )


if __name__ == "__main__":
    # use_reloader explizit aus: sonst startet Werkzeug beim Aufruf per
    # relativem Pfad (venv\Scripts\python.exe webapp\app.py, wie es
    # start.bat/start.sh tun) einen zweiten Python-Prozess zum Neuladen bei
    # Codeaenderungen - fuer eine fertig installierte lokale App unnoetig
    # und sorgt nur fuer einen verwaisten Zweitprozess.
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
