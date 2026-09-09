#!/usr/bin/env bash
# Richtet einen Cronjob ein: fuehrt scraper/run.py jeden Montag und
# Donnerstag um 06:00 Uhr automatisch aus.
#
# Einmalig ausfuehren (im Projektverzeichnis):
#   chmod +x setup_cron.sh && ./setup_cron.sh

set -euo pipefail

PROJEKT_PFAD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJEKT_PFAD/venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    echo "Keine venv unter $VENV_PYTHON gefunden."
    echo "Bitte zuerst einrichten:"
    echo "  python3 -m venv venv"
    echo "  ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

CRON_ZEILE="0 6 * * 1,4 $VENV_PYTHON $PROJEKT_PFAD/scraper/run.py >> $PROJEKT_PFAD/logs/cron.log 2>&1"
MARKER="# RealityTV_Scraper"

( crontab -l 2>/dev/null | grep -v "$MARKER" || true ; echo "$CRON_ZEILE $MARKER" ) | crontab -

echo "Cronjob eingerichtet: laeuft montags + donnerstags um 06:00 Uhr."
echo "Pruefen mit: crontab -l"
echo "Wieder entfernen: crontab -l | grep -v '$MARKER' | crontab -"
