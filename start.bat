@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === Reality-TV Programmuebersicht ===
echo.

rem --- 1. Python vorhanden? Sonst automatisch per winget installieren ---
where python >nul 2>nul
if errorlevel 1 (
    echo Python wurde nicht gefunden. Versuche automatische Installation per winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo Fehler: winget ist nicht verfuegbar.
        echo Bitte Python manuell von https://www.python.org/downloads/ installieren
        echo und dieses Skript danach erneut starten.
        pause
        exit /b 1
    )
    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo Python-Installation fehlgeschlagen. Bitte manuell installieren: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo Python wurde installiert. Bitte dieses Fenster schliessen, ein NEUES Terminal
    echo oeffnen und start.bat erneut starten ^(damit Windows den neuen PATH kennt^).
    pause
    exit /b 0
)

rem --- 2. Virtuelle Umgebung + Abhaengigkeiten, falls noch nicht vorhanden ---
if not exist "venv\Scripts\python.exe" (
    echo Richte virtuelle Umgebung ein ^(einmalig, dauert etwas^)...
    python -m venv venv
    if errorlevel 1 (
        echo Fehler beim Anlegen der virtuellen Umgebung.
        pause
        exit /b 1
    )
    venv\Scripts\python.exe -m pip install --quiet --upgrade pip
    venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo Fehler beim Installieren der Abhaengigkeiten.
        pause
        exit /b 1
    )
)

rem --- 3. Automatische Aktualisierung einrichten, falls noch nicht vorhanden ---
schtasks /Query /TN "RealityTV_Scraper" >nul 2>nul
if errorlevel 1 (
    echo Richte automatische Aktualisierung ein ^(Montag + Donnerstag, 06:00 Uhr^)...
    schtasks /Create /TN "RealityTV_Scraper" /TR "\"%~dp0venv\Scripts\python.exe\" \"%~dp0scraper\run.py\"" /SC WEEKLY /D MON,THU /ST 06:00 /RL LIMITED /F >nul
)

rem --- 4. Beim allerersten Start: einmal sofort Daten holen, damit direkt etwas zu sehen ist ---
if not exist "data\programm.db" (
    echo Erster Start: hole aktuelle Programmdaten ^(dauert 1-2 Minuten^)...
    venv\Scripts\python.exe -m scraper.run
)

rem --- 5. Web-App starten und Browser oeffnen ---
echo.
echo Oeffne http://127.0.0.1:5000 im Browser ...
echo Zum Beenden dieses Fenster schliessen oder Strg+C druecken.
echo.
start "" http://127.0.0.1:5000
venv\Scripts\python.exe webapp\app.py
