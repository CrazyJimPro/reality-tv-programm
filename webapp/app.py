"""Lokale Flask-Web-App: zeigt die gespeicherten Reality-TV-Termine an.

Start (aus dem Projektverzeichnis):
    python webapp/app.py
Danach im Browser: http://127.0.0.1:5000

Die Programmdaten werden bei jedem Start der App einmal frisch geholt (im
Hintergrund, damit die Seite sofort da ist) - es laeuft also nichts mehr,
sobald die App beendet ist. Frueher gab es dafuer eine Windows-Aufgabe bzw.
einen Cronjob (Mo + Do, 06:00 Uhr); die werden von start.bat/start.sh
inzwischen wieder entfernt.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJEKT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJEKT_ROOT))

from flask import Flask, jsonify, redirect, render_template, request, url_for  # noqa: E402

from scraper.filter import CONFIG_PFAD, lade_shows_config, speichere_shows_config  # noqa: E402
from scraper.storage import DB_PFAD, hole_programme, hole_quellen_status, init_db  # noqa: E402
from vorschlaege import VORSCHLAEGE  # noqa: E402

app = Flask(__name__)

VORSCHAU_TAGE = 14
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# Ab wann gelten die Daten einer Quelle als veraltet (Warnhinweis in der
# Uebersicht)? Im Normalfall - App starten, Daten werden geholt - wird das
# nie erreicht; der Hinweis schlaegt also nur an, wenn eine Quelle beim
# Start nicht erreichbar war und noch alte Daten angezeigt werden, oder
# wenn die App sehr lange durchlaeuft.
VERALTET_AB_STUNDEN = 24

STAFFEL_MUSTER = re.compile(r"Staffel\s*(\d+)", re.IGNORECASE)
FOLGE_MUSTER = re.compile(r"Folge\s*(\d+)", re.IGNORECASE)

# Status des Scrape-Laufs, damit die Oberflaeche zeigen kann, dass gerade
# aktualisiert wird - und vor allem, wenn es schiefgegangen ist (frueher gab
# es immer eine Erfolgsmeldung, egal wie der Lauf ausging).
_scrape_sperre = threading.Lock()
_scrape_status: dict[str, object] = {"laeuft": False, "fehler": None, "fertig_am": None}
# Referenz auf den gerade laufenden Scraper-Prozess, damit "Beenden" ihn
# mitnehmen kann - sonst liefe er als Waise weiter, obwohl die App zu ist.
_laufender_prozess: subprocess.Popen | None = None


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


def _scraper_ausfuehren() -> None:
    """Fuehrt einen Scrape-Lauf aus (dauert ca. 1-2 Minuten) und haelt das
    Ergebnis in _scrape_status fest.

    Nutzt denselben Python-Interpreter, unter dem die Web-App laeuft (die
    venv), und ruft scraper/run.py exakt so auf wie start.bat/start.sh es
    frueher taten - damit gibt es nur einen Codepfad fuer "wie wird
    gescraped". Durch die Sperre laeuft immer nur ein Lauf gleichzeitig
    (z.B. wenn beim Start schon gescraped wird und man zusaetzlich auf
    "Jetzt aktualisieren" klickt)."""
    global _laufender_prozess
    if not _scrape_sperre.acquire(blocking=False):
        return
    try:
        _scrape_status["laeuft"] = True
        _scrape_status["fehler"] = None
        # Unter Linux eine eigene Prozessgruppe, damit "Beenden" den Lauf
        # samt eventueller Kindprozesse killen kann (Windows: taskkill /T).
        extra = {} if os.name == "nt" else {"start_new_session": True}
        _laufender_prozess = subprocess.Popen(
            [sys.executable, "-m", "scraper.run"],
            cwd=PROJEKT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **extra,
        )
        stdout, stderr = _laufender_prozess.communicate()
        if _laufender_prozess.returncode != 0:
            # Die volle Ausgabe steht ohnehin in logs/scraper.log - hier nur
            # die letzten Zeilen, damit die Meldung im Browser lesbar bleibt.
            ausgabe = (stderr or stdout or "").strip()
            letzte_zeilen = " / ".join(ausgabe.splitlines()[-3:])
            _scrape_status["fehler"] = (
                letzte_zeilen or f"Scraper endete mit Code {_laufender_prozess.returncode}"
            )
    except Exception as exc:  # z.B. Interpreter/Pfad kaputt
        _scrape_status["fehler"] = str(exc)
    finally:
        _laufender_prozess = None
        _scrape_status["laeuft"] = False
        _scrape_status["fertig_am"] = datetime.now().isoformat(timespec="seconds")
        _scrape_sperre.release()


def _laufenden_scrape_beenden() -> None:
    """Beendet einen noch laufenden Scraper-Prozess mitsamt seiner
    Kindprozesse. Ohne das bliebe er nach "Beenden" als Waise zurueck und es
    liefe eben doch noch etwas im Hintergrund (unter Windows startet die
    python.exe mancher venvs zusaetzlich einen eigenen Kindprozess, deshalb
    dort taskkill mit /T statt eines einfachen terminate)."""
    prozess = _laufender_prozess
    if prozess is None or prozess.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(prozess.pid)],
                capture_output=True,
                check=False,
            )
        else:
            os.killpg(os.getpgid(prozess.pid), signal.SIGTERM)
    except Exception:
        try:
            prozess.kill()
        except Exception:
            pass


def _scrape_im_hintergrund_starten() -> bool:
    """Stoesst einen Scrape-Lauf in einem Hintergrund-Thread an, damit die
    Seite sofort antwortet statt 1-2 Minuten zu haengen. Liefert False,
    wenn bereits einer laeuft."""
    if _scrape_status["laeuft"]:
        return False
    threading.Thread(target=_scraper_ausfuehren, name="rtv-scrape", daemon=True).start()
    return True


def _alter_text(alter: timedelta) -> str:
    tage = alter.days
    stunden = int(alter.total_seconds() // 3600)
    if tage >= 1:
        return f"vor {tage} Tag" + ("en" if tage != 1 else "")
    if stunden >= 1:
        return f"vor {stunden} Stunde" + ("n" if stunden != 1 else "")
    return "gerade eben"


def _status_aufbereiten(status: list[dict]) -> list[dict]:
    """Macht aus den rohen ISO-Zeitstempeln lesbare Angaben und markiert
    Quellen, deren letzter Erfolg zu lange her ist. Ohne das war der
    Status-Chip ab dem ersten Erfolg fuer immer gruen - eine spaeter
    weggebrochene Quelle fiel nur auf, wenn man das Datum selbst nachlas."""
    jetzt = datetime.now()
    aufbereitet = []
    for roh_eintrag in status:
        eintrag = dict(roh_eintrag)
        eintrag["erfolg_text"] = None
        eintrag["alter_text"] = None
        eintrag["veraltet"] = False
        roh = eintrag.get("letzter_erfolg_am")
        if roh:
            try:
                zeitpunkt = datetime.fromisoformat(str(roh))
            except ValueError:
                eintrag["erfolg_text"] = str(roh)
            else:
                eintrag["erfolg_text"] = zeitpunkt.strftime("%d.%m.%Y, %H:%M")
                alter = jetzt - zeitpunkt
                eintrag["veraltet"] = alter > timedelta(hours=VERALTET_AB_STUNDEN)
                eintrag["alter_text"] = _alter_text(alter)
        aufbereitet.append(eintrag)
    return aufbereitet


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

    status = _status_aufbereiten(hole_quellen_status(db_pfad=DB_PFAD))

    return render_template(
        "index.html",
        naechste_woche=naechste_woche,
        uebernaechste_woche=uebernaechste_woche,
        status=status,
        heute=heute,
        anzahl_gesamt=len(rows),
        scrape=_scrape_status,
    )


@app.route("/scrape-status")
def scrape_status():
    """Wird von der Uebersichtsseite abgefragt, solange ein Lauf laeuft -
    die Seite laedt sich dann einmal neu, sobald er fertig ist."""
    return jsonify(laeuft=bool(_scrape_status["laeuft"]), fehler=_scrape_status["fehler"])


@app.route("/aktualisieren", methods=["POST"])
def aktualisieren():
    """Manueller 'Jetzt aktualisieren'-Knopf - fuer den Fall, dass die App
    laenger laeuft und man zwischendurch neue Daten will (beim Start wird
    ohnehin automatisch aktualisiert)."""
    _scrape_im_hintergrund_starten()
    return redirect(url_for("index"))


@app.route("/beenden", methods=["POST"])
def beenden():
    """Beendet die App komplett - danach laeuft nichts mehr im Hintergrund.
    Noetig, weil die App per Desktop-Verknuepfung ohne sichtbares Fenster
    startet und sich sonst nur ueber den Task-Manager beenden liesse."""

    def _stoppen() -> None:
        time.sleep(0.5)  # kurz warten, damit die Antwort noch rausgeht
        _laufenden_scrape_beenden()
        os._exit(0)

    threading.Thread(target=_stoppen, name="rtv-stop", daemon=True).start()
    return render_template("beendet.html")


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
        # Direkt neu scrapen, damit die geaenderte Auswahl in der Uebersicht
        # auftaucht - im Hintergrund, die Seite antwortet sofort.
        _scrape_im_hintergrund_starten()
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
    # Tabellen anlegen, falls die App vor dem allerersten Scrape-Lauf
    # geoeffnet wird - sonst wuerde die Uebersicht ueber eine noch leere
    # Datenbank stolpern.
    init_db(DB_PFAD)
    # Beim Start einmal frische Daten holen. Laeuft im Hintergrund, damit
    # der Browser sofort etwas zu sehen bekommt (die Seite zeigt so lange
    # einen Hinweis und laedt sich neu, sobald der Lauf fertig ist).
    _scrape_im_hintergrund_starten()
    # use_reloader explizit aus: sonst startet Werkzeug beim Aufruf per
    # relativem Pfad (venv\Scripts\python.exe webapp\app.py, wie es
    # start.bat/start.sh tun) einen zweiten Python-Prozess zum Neuladen bei
    # Codeaenderungen - fuer eine fertig installierte lokale App unnoetig
    # und sorgt nur fuer einen verwaisten Zweitprozess.
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
