#!/usr/bin/env bash
# Einzige Datei, die man ausfuehren muss: installiert/richtet alles automatisch
# ein (Python-Check, venv, Abhaengigkeiten, Cronjob, erster Datenabruf) und
# startet danach die Web-App. Bei jedem weiteren Aufruf werden bereits
# erledigte Schritte uebersprungen.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "=== Reality-TV Programmuebersicht ==="
echo

# --- 1. Python3 vorhanden? Sonst automatisch per apt installieren ---
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 wurde nicht gefunden. Versuche automatische Installation..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y python3 python3-venv python3-pip cron
    else
        echo "Fehler: kein unterstuetzter Paketmanager (apt-get) gefunden."
        echo "Bitte Python 3 manuell installieren und dieses Skript erneut starten."
        exit 1
    fi
fi

# venv-Modul ist auf manchen Distros ein separates Paket
if ! python3 -m venv --help >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installiere python3-venv nach..."
        sudo apt-get update -qq && sudo apt-get install -y python3-venv
    fi
fi

# --- 2. Virtuelle Umgebung + Abhaengigkeiten, falls noch nicht vorhanden ---
if [ ! -x "venv/bin/python" ]; then
    echo "Richte virtuelle Umgebung ein (einmalig, dauert etwas)..."
    python3 -m venv venv || { echo "Fehler beim Anlegen der virtuellen Umgebung."; exit 1; }
    ./venv/bin/pip install --quiet --upgrade pip || { echo "Fehler beim pip-Upgrade."; exit 1; }
    ./venv/bin/pip install --quiet -r requirements.txt || { echo "Fehler beim Installieren der Abhaengigkeiten."; exit 1; }
fi

PROJEKT_PFAD="$(pwd)"
VENV_PYTHON="$PROJEKT_PFAD/venv/bin/python"

# --- 3. Automatische Aktualisierung einrichten, falls noch nicht vorhanden ---
MARKER="# RealityTV_Scraper"
if ! crontab -l 2>/dev/null | grep -q "$MARKER"; then
    echo "Richte automatische Aktualisierung ein (Montag + Donnerstag, 06:00 Uhr)..."
    CRON_ZEILE="0 6 * * 1,4 $VENV_PYTHON $PROJEKT_PFAD/scraper/run.py >> $PROJEKT_PFAD/logs/cron.log 2>&1"
    ( crontab -l 2>/dev/null | grep -v "$MARKER" || true ; echo "$CRON_ZEILE $MARKER" ) | crontab -
fi

# Cron-Dienst best-effort starten, falls installiert aber nicht aktiv (z.B. frischer Container/VM)
if command -v systemctl >/dev/null 2>&1; then
    systemctl is-active --quiet cron 2>/dev/null || sudo systemctl start cron 2>/dev/null || true
elif command -v service >/dev/null 2>&1; then
    service cron status >/dev/null 2>&1 || sudo service cron start >/dev/null 2>&1 || true
fi

# --- 4. Beim allerersten Start: einmal sofort Daten holen, damit direkt etwas zu sehen ist ---
if [ ! -f "data/programm.db" ]; then
    echo "Erster Start: hole aktuelle Programmdaten (dauert 1-2 Minuten)..."
    "$VENV_PYTHON" -m scraper.run
fi

# --- 5. Web-App starten und Browser oeffnen ---
echo
echo "Oeffne http://127.0.0.1:5000 im Browser ..."
echo "Zum Beenden Strg+C druecken."
echo
( sleep 1 && xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 || true ) &
"$VENV_PYTHON" webapp/app.py
