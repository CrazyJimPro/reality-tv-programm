@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
    echo Keine venv gefunden. Bitte zuerst einrichten:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
start "" http://127.0.0.1:5000
venv\Scripts\python.exe webapp\app.py
