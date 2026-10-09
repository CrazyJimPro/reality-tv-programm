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

import json
import logging
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

from scraper.entdecken import STUFE_REALITY, STUFE_SOAP, fuer_anzeige  # noqa: E402
from scraper.folgen import gesehen_schluessel, hauptausstrahlung_von, hauptausstrahlungen  # noqa: E402
from scraper.filter import CONFIG_PFAD, lade_shows_config, passt_zu_namen, speichere_shows_config  # noqa: E402
from scraper.sicherung import (  # noqa: E402
    SicherungsFehler,
    erstelle_sicherung,
    sicherungs_dateiname,
    spiele_sicherung_ein,
)
from scraper.sources import tmdb  # noqa: E402
from scraper.sources.tvspielfilm import SENDER_SLUGS  # noqa: E402
from scraper.storage import (  # noqa: E402
    DB_PFAD,
    hole_demnaechst,
    hole_entdeckungen,
    hole_folgen_verlauf,
    hole_gesehen,
    hole_programme,
    hole_quellen_status,
    init_db,
    setze_gesehen,
    uebernehme_entdeckungen,
)
from vorschlaege import VORSCHLAEGE  # noqa: E402

app = Flask(__name__)

# Eine Sicherung ist wenige Kilobyte gross. Das Limit faengt nur den Fall ab,
# dass versehentlich etwas ganz anderes hochgeladen wird - ohne es wuerde
# Flask die Datei erst komplett annehmen und dann verwerfen.
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

VORSCHAU_TAGE = 14
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WOCHENTAGE_KURZ = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

# Ab wann gelten die Daten einer Quelle als veraltet (Warnhinweis in der
# Uebersicht)? Im Normalfall - App starten, Daten werden geholt - wird das
# nie erreicht; der Hinweis schlaegt also nur an, wenn eine Quelle beim
# Start nicht erreichbar war und noch alte Daten angezeigt werden, oder
# wenn die App sehr lange durchlaeuft.
VERALTET_AB_STUNDEN = 24

STAFFEL_MUSTER = re.compile(r"Staffel\s*(\d+)", re.IGNORECASE)
# Auch Bereiche: TMDB fasst Folgen vom selben Tag zu "Folge 19–20" zusammen
FOLGE_MUSTER = re.compile(r"Folge\s*(\d+(?:\s*[–-]\s*\d+)?)", re.IGNORECASE)

VERSION_PFAD = PROJEKT_ROOT / "VERSION"
LOG_PFAD = PROJEKT_ROOT / "logs" / "webapp.log"


def _version() -> str:
    """Versionsnummer aus der Datei VERSION im Projektordner. Wird oben in
    der Kopfzeile angezeigt, damit man sieht, welcher Stand gerade laeuft -
    das Selbst-Update frischt den ganzen Ordner auf, also kommt die Datei
    immer passend zum restlichen Code mit."""
    try:
        return VERSION_PFAD.read_text(encoding="utf-8").strip() or "unbekannt"
    except OSError:
        return "unbekannt"

# Status des Scrape-Laufs, damit die Oberflaeche zeigen kann, dass gerade
# aktualisiert wird - und vor allem, wenn es schiefgegangen ist (frueher gab
# es immer eine Erfolgsmeldung, egal wie der Lauf ausging).
_scrape_sperre = threading.Lock()
_scrape_status: dict[str, object] = {"laeuft": False, "fehler": None, "fertig_am": None}
# Wird waehrend eines laufenden Abrufs etwas gespeichert (Sendungsliste,
# TMDB-Schluessel), hat der laufende Abruf die Aenderung womoeglich schon
# hinter sich - dann folgt danach genau ein weiterer.
_nachlauf = threading.Event()
# Referenz auf den gerade laufenden Scraper-Prozess, damit "Beenden" ihn
# mitnehmen kann - sonst liefe er als Waise weiter, obwohl die App zu ist.
_laufender_prozess: subprocess.Popen | None = None


def _logging_einrichten() -> None:
    """Meldungen zusaetzlich nach logs/webapp.log schreiben.

    start.bat startet die App ueber pythonw.exe, damit kein Konsolenfenster
    offen bleibt - dann gibt es aber auch keine sichtbare Ausgabe mehr.
    Ohne diese Datei waere ein Startproblem nicht mehr nachvollziehbar."""
    LOG_PFAD.parent.mkdir(parents=True, exist_ok=True)
    handler: list[logging.Handler] = [logging.FileHandler(LOG_PFAD, encoding="utf-8")]
    # Zusaetzlich auf den Bildschirm nur, wenn wirklich ein Terminal dranhaengt:
    # unter pythonw.exe gibt es gar keinen stderr, und start.sh leitet stderr
    # bereits in dieselbe Logdatei um - dann stuende jede Zeile doppelt drin.
    if sys.stderr is not None and getattr(sys.stderr, "isatty", lambda: False)():
        handler.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handler,
    )

    def _unbehandelt(typ, wert, spur):
        logging.getLogger("webapp").critical("Unbehandelter Fehler", exc_info=(typ, wert, spur))

    sys.excepthook = _unbehandelt


@app.context_processor
def _vorlagen_kontext() -> dict:
    """Stellt die Versionsnummer allen Vorlagen zur Verfuegung."""
    return {"version": _version()}


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


def _scraper_ausfuehren() -> bool:
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
        return False
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
    return True


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
        _nachlauf.set()
        return False
    threading.Thread(target=_scrape_mit_nachlauf, name="rtv-scrape", daemon=True).start()
    return True


def _scrape_mit_nachlauf() -> None:
    while True:
        _nachlauf.clear()
        if not _scraper_ausfuehren():
            # Ein anderer Strang laeuft schon (zwei Klicks fast gleichzeitig) -
            # der uebernimmt den Nachlauf
            _nachlauf.set()
            return
        if not _nachlauf.is_set():
            return


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
    haupt = hauptausstrahlungen(hole_folgen_verlauf(uebernaechste_woche_bis, db_pfad=DB_PFAD))
    gesehen = hole_gesehen(db_pfad=DB_PFAD)
    for row in rows:
        # Folgenangabe der Detailseite zuerst, sonst wie bisher aus dem
        # Untertitel von rtl.de
        row["staffel_folge"] = _staffel_folge(row.get("folge")) or _staffel_folge(row.get("beschreibung"))
        row["schluessel"] = gesehen_schluessel(row)
        row["gesehen"] = row["schluessel"] in gesehen
        hauptrow = hauptausstrahlung_von(row, haupt)
        row["hauptausstrahlung"] = f"{_termin_filter(_zeitpunkt(hauptrow))} auf {hauptrow['sender']}" if hauptrow else None

    naechste_woche = _woche_gruppieren(rows, heute, naechste_woche_bis)
    uebernaechste_woche = _woche_gruppieren(rows, uebernaechste_woche_ab, uebernaechste_woche_bis)

    status = _status_aufbereiten(hole_quellen_status(db_pfad=DB_PFAD))

    # Einmaliger Wegweiser nach einer frischen Installation. Es gibt kein
    # Installationsprogramm, das beim Aufsetzen nach einer vorhandenen
    # Sicherung fragen koennte, und der uebliche Start ueber die
    # Desktop-Verknuepfung zeigt gar kein Fenster - also fragt die App selbst,
    # sichtbar auf der Startseite.
    # Der Merker steht in der Sendungsliste selbst, nicht im Arbeitsspeicher:
    # sonst waere der Hinweis nach dem ersten Neustart weg, obwohl noch nichts
    # eingerichtet ist.
    config = lade_shows_config(CONFIG_PFAD)
    einrichtung_offen = not config.get("einrichtung_erledigt")

    entdeckt = fuer_anzeige(
        # Die TMDB-Vorschlaege reichen weiter als die zwei Wochen
        hole_entdeckungen(heute, heute + timedelta(days=tmdb.TAGE_ENTDECKEN), db_pfad=DB_PFAD),
        show_namen=_show_namen(config),
        ausgeblendet=config.get("ausgeblendet", []),
    )

    bilder = tmdb.lade_bilder()
    demnaechst = [d for d in hole_demnaechst(heute, db_pfad=DB_PFAD) if d["datum"] > uebernaechste_woche_bis.isoformat()]
    for d in demnaechst:
        d["in_tagen"] = (date.fromisoformat(d["datum"]) - heute).days

    return render_template(
        "index.html",
        naechste_woche=naechste_woche,
        uebernaechste_woche=uebernaechste_woche,
        status=status,
        heute=heute,
        anzahl_gesamt=len(rows),
        scrape=_scrape_status,
        einrichtung_offen=einrichtung_offen,
        sender_liste=list(SENDER_SLUGS),
        entdeckt_reality=entdeckt[STUFE_REALITY],
        entdeckt_soap=entdeckt[STUFE_SOAP],
        hinzugefuegt=request.args.get("hinzugefuegt"),
        hinzugefuegt_termine=request.args.get("termine"),
        # Staffelstarts nach den zwei Wochen; was inzwischen hineingerutscht
        # ist, steht schon in der Wochenansicht
        demnaechst=demnaechst,
        tmdb_aktiv=tmdb.lade_schluessel() is not None,
        # Vorschaubilder von TMDB (data/tmdb_bilder.json, vom Datenabruf
        # gefuellt); None = Platzhalter in der Senderfarbe
        bild=lambda titel, art="backdrop": tmdb.bild_url(bilder, titel, art),
        heute_iso=heute.isoformat(),
    )


def _show_namen(config: dict) -> list[str]:
    namen = []
    for show in config.get("shows", []):
        namen.append(show["name"])
        namen.extend(show.get("aliases", []))
    return namen


def _zeitpunkt(row: dict) -> datetime:
    return datetime.combine(date.fromisoformat(row["datum"]), datetime.strptime(row["uhrzeit"], "%H:%M").time())


@app.template_filter("termin")
def _termin_filter(zeitpunkt: datetime | None) -> str:
    if zeitpunkt is None:
        return "heute schon gelaufen"
    return f"{WOCHENTAGE_KURZ[zeitpunkt.weekday()]} {zeitpunkt:%d.%m.}, {zeitpunkt:%H:%M}"


@app.template_filter("langtag")
def _langtag_filter(wert: date | str) -> str:
    """"Freitag, 9. Oktober" - fuer die Tagesueberschriften."""
    if isinstance(wert, str):
        wert = date.fromisoformat(wert)
    return f"{WOCHENTAGE[wert.weekday()]}, {wert.day}. {MONATE[wert.month - 1]}"


@app.template_filter("senderklasse")
def _senderklasse_filter(sender: str) -> str:
    """CSS-Klasse fuer die Senderfarbe: "Sat.1 Gold" -> "sender-sat1gold"."""
    return "sender-" + sender.lower().replace(".", "").replace(" ", "").replace("+", "plus")


@app.template_filter("tag")
def _tag_filter(wert: datetime | date | str | None) -> str:
    """Nur das Datum - fuer Termine laut TMDB, die keine Uhrzeit haben."""
    if wert is None:
        return "heute"
    if isinstance(wert, str):
        wert = date.fromisoformat(wert)
    return f"{WOCHENTAGE_KURZ[wert.weekday()]} {wert:%d.%m.}"


@app.route("/gesehen", methods=["POST"])
def gesehen_setzen():
    """Haekchen setzen/entfernen - per fetch aus der Uebersicht, ohne Neuladen."""
    daten = request.get_json(silent=True) or {}
    schluessel = str(daten.get("schluessel", "")).strip()
    if not schluessel:
        return jsonify({"ok": False}), 400
    setze_gesehen(schluessel, bool(daten.get("gesehen")), db_pfad=DB_PFAD)
    return jsonify({"ok": True})


@app.route("/entdeckung/hinzufuegen", methods=["POST"])
def entdeckung_hinzufuegen():
    """Nimmt einen Titel aus "Neu entdeckt" in die Sendungsliste auf und
    kopiert seine schon bekannten Termine direkt in die Uebersicht - ohne
    neuen Datenabruf, deshalb klappen auch mehrere Klicks hintereinander."""
    titel = request.form.get("titel", "").strip()
    if not titel:
        return redirect(url_for("index"))
    daten = lade_shows_config(CONFIG_PFAD)
    shows = daten.setdefault("shows", [])
    if not any(s["name"].lower() == titel.lower() for s in shows):
        shows.append({"name": titel, "aliases": []})
        shows.sort(key=lambda s: s["name"].lower())
        speichere_shows_config(daten, CONFIG_PFAD)

    heute = date.today()
    rows = hole_entdeckungen(heute, heute + timedelta(days=VORSCHAU_TAGE - 1), db_pfad=DB_PFAD)
    passende = [r for r in rows if passt_zu_namen(r["titel"], [titel])]
    uebernehme_entdeckungen(passende, db_pfad=DB_PFAD)
    return redirect(url_for("index", hinzugefuegt=titel, termine=len(passende), _anchor="entdeckungen"))


@app.route("/entdeckung/ausblenden", methods=["POST"])
def entdeckung_ausblenden():
    titel = request.form.get("titel", "").strip()
    if titel:
        daten = lade_shows_config(CONFIG_PFAD)
        ausgeblendet = daten.setdefault("ausgeblendet", [])
        if titel.lower() not in (t.lower() for t in ausgeblendet):
            ausgeblendet.append(titel)
            ausgeblendet.sort(key=str.lower)
            speichere_shows_config(daten, CONFIG_PFAD)
    return redirect(url_for("index", _anchor="entdeckungen"))


@app.route("/entdeckung/einblenden", methods=["POST"])
def entdeckung_einblenden():
    titel = request.form.get("titel", "").strip()
    daten = lade_shows_config(CONFIG_PFAD)
    daten["ausgeblendet"] = [t for t in daten.get("ausgeblendet", []) if t.lower() != titel.lower()]
    speichere_shows_config(daten, CONFIG_PFAD)
    return redirect(url_for("einstellungen", _anchor="ausgeblendet"))


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


@app.route("/sicherung")
def sicherung_herunterladen():
    """Laedt die persoenliche Sendungsliste als JSON-Datei herunter.

    Bewusst ein Download statt einer Datei irgendwo im Projektordner: so
    landet die Sicherung dort, wo der Browser hinspeichert, und laesst sich
    von dort auf einen USB-Stick oder einen anderen Rechner mitnehmen.
    """
    inhalt = json.dumps(erstelle_sicherung(_version()), ensure_ascii=False, indent=2) + "\n"
    return app.response_class(
        inhalt,
        mimetype="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{sicherungs_dateiname()}"',
            "Cache-Control": "no-store",
        },
    )


@app.route("/sicherung-einspielen", methods=["POST"])
def sicherung_einspielen():
    """Spielt eine hochgeladene Sicherungsdatei ein.

    Der Weg ueber den Datei-Dialog des Browsers ist Absicht: so laesst sich
    eine Sicherung von ueberall holen - Downloads, USB-Stick, Netzlaufwerk -,
    ohne dass das Programm Suchpfade fest verdrahtet.
    """
    datei = request.files.get("datei")
    if datei is None or not datei.filename:
        return redirect(url_for("einstellungen", fehler="Keine Datei ausgewählt."))

    try:
        bericht = spiele_sicherung_ein(datei.read(), version=_version())
    except SicherungsFehler as fehler:
        return redirect(url_for("einstellungen", fehler=str(fehler)))
    except OSError as fehler:
        logging.getLogger("webapp").exception("Sicherung konnte nicht eingespielt werden")
        return redirect(url_for("einstellungen", fehler=f"Die Sendungsliste ließ sich nicht schreiben: {fehler}"))

    meldung = f"{bericht['sendungen']} Sendungen übernommen"
    if bericht["erstellt_am"]:
        meldung += f" (Sicherung vom {bericht['erstellt_am'][:10]})"
    if bericht["notizen"]:
        meldung += " – " + ", ".join(bericht["notizen"])
    if bericht["sicherheitskopie"]:
        meldung += f". Der bisherige Stand liegt als {bericht['sicherheitskopie']} im Ordner config."

    logging.getLogger("webapp").info("Sicherung eingespielt: %s", meldung)
    # Wie beim Speichern der Auswahl: direkt neu scrapen, damit die Uebersicht
    # zur eingespielten Liste passt.
    _scrape_im_hintergrund_starten()
    return redirect(url_for("einstellungen", eingespielt=meldung))


@app.route("/einrichtung-erledigt", methods=["POST"])
def einrichtung_erledigt():
    """Blendet den Wegweiser fuer frische Installationen dauerhaft aus."""
    daten = lade_shows_config(CONFIG_PFAD)
    daten["einrichtung_erledigt"] = True
    speichere_shows_config(daten, CONFIG_PFAD)
    return redirect(url_for("index"))


@app.errorhandler(413)
def _datei_zu_gross(_fehler):
    """Ohne diesen Handler bekaeme der Nutzer Flasks nackte Fehlerseite zu
    sehen und muesste selbst zurueckfinden."""
    return redirect(url_for("einstellungen", fehler="Die Datei ist zu groß für eine Sicherung (über 5 MB)."))


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
        # Wer hier speichert, hat sich eingerichtet - der Wegweiser auf der
        # Startseite hat sich damit erledigt.
        daten["einrichtung_erledigt"] = True
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
        eingespielt=request.args.get("eingespielt"),
        fehler=request.args.get("fehler"),
        ausgeblendet=daten.get("ausgeblendet", []),
        tmdb_endung=(tmdb.lade_schluessel() or "")[-4:],
        tmdb_aus_streaming_info=tmdb.schluessel_aus_streaming_info() not in (None, tmdb.lade_schluessel()),
        tmdb_meldung=request.args.get("tmdb"),
        tmdb_fehler=request.args.get("tmdb_fehler"),
    )


@app.route("/tmdb-schluessel", methods=["POST"])
def tmdb_schluessel():
    """Schluessel eintragen, aus Streaming-Info uebernehmen oder entfernen.
    Ein neuer Schluessel wird vor dem Speichern bei TMDB ausprobiert - ein
    Tippfehler soll hier auffallen, nicht erst als roter Status-Chip."""
    aktion = request.form.get("aktion")
    if aktion == "entfernen":
        tmdb.speichere_schluessel(None)
        _scrape_im_hintergrund_starten()
        return redirect(url_for("einstellungen", tmdb="entfernt", _anchor="tmdb"))
    if aktion == "uebernehmen":
        schluessel = tmdb.schluessel_aus_streaming_info() or ""
    else:
        schluessel = request.form.get("schluessel", "").strip()
    if not schluessel:
        return redirect(url_for("einstellungen", tmdb_fehler="Bitte einen TMDB-Schlüssel eintragen.", _anchor="tmdb"))
    fehler = tmdb.pruefe_schluessel(schluessel)
    if fehler:
        return redirect(url_for("einstellungen", tmdb_fehler=fehler, _anchor="tmdb"))
    tmdb.speichere_schluessel(schluessel)
    _scrape_im_hintergrund_starten()
    return redirect(url_for("einstellungen", tmdb="gespeichert", _anchor="tmdb"))


if __name__ == "__main__":
    _logging_einrichten()
    logging.getLogger("webapp").info("Reality-TV Programm Version %s startet", _version())
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
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
