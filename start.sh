#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -x "venv/bin/python" ]; then
    echo "Keine venv gefunden. Bitte zuerst einrichten:"
    echo "  python3 -m venv venv"
    echo "  ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

( sleep 1 && xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 || true ) &
./venv/bin/python webapp/app.py
