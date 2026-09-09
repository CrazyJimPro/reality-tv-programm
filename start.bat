@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === Reality-TV Programmuebersicht ===
echo.

rem --- 0. Falls das Projekt (noch) nicht komplett vorhanden ist (z.B. weil nur
rem     diese eine Datei heruntergeladen wurde): kompletten Code von GitHub
rem     laden und von dort aus weitermachen. ---
set "ZIEL_ORDNER=%USERPROFILE%\reality-tv-programm"
if not exist "requirements.txt" (
    if /I not "%cd%"=="%ZIEL_ORDNER%" (
        if not exist "%ZIEL_ORDNER%\requirements.txt" (
            echo Projekt-Dateien nicht gefunden - lade komplettes Projekt von GitHub herunter...
            rem PowerShell-Logik in eine temporaere .ps1-Datei schreiben statt als
            rem Inline-Befehl - vermeidet fragile verschachtelte Anfuehrungszeichen.
            > "%TEMP%\rtv_download.ps1" (
                echo $ErrorActionPreference = 'Stop'
                echo Invoke-WebRequest -Uri 'https://github.com/CrazyJimPro/reality-tv-programm/archive/refs/heads/main.zip' -OutFile "$env:TEMP\rtv.zip"
                echo Expand-Archive -Path "$env:TEMP\rtv.zip" -DestinationPath "$env:TEMP\rtv-extract" -Force
                echo New-Item -ItemType Directory -Force -Path '%ZIEL_ORDNER%' ^| Out-Null
                echo Copy-Item -Path "$env:TEMP\rtv-extract\reality-tv-programm-main\*" -Destination '%ZIEL_ORDNER%' -Recurse -Force
                echo Remove-Item "$env:TEMP\rtv.zip","$env:TEMP\rtv-extract" -Recurse -Force
            )
            powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\rtv_download.ps1"
            if errorlevel 1 (
                del "%TEMP%\rtv_download.ps1" >nul 2>nul
                echo Fehler beim Herunterladen/Entpacken. Bitte Internetverbindung pruefen,
                echo oder das Repo manuell laden: https://github.com/CrazyJimPro/reality-tv-programm
                pause
                exit /b 1
            )
            del "%TEMP%\rtv_download.ps1" >nul 2>nul
        )
        echo Projekt liegt jetzt unter: %ZIEL_ORDNER%
        echo Starte von dort weiter ...
        echo.
        call "%ZIEL_ORDNER%\start.bat"
        exit /b %errorlevel%
    )
)

rem --- 1. Python vorhanden? Sonst automatisch per winget installieren ---
rem Ein blosses "where python" reicht nicht: Windows legt standardmaessig
rem einen "python"-Platzhalter an, der nur auf den Microsoft Store verweist
rem und dabei erfolgreich gefunden wird, aber kein echtes Python ist. Daher
rem hier ein echter Funktionstest per Ausgabe-Pruefung.
set "PYTHON_EXE="
for /f "delims=" %%v in ('python -c "print(1)" 2^>nul') do if "%%v"=="1" set "PYTHON_EXE=python"
if not defined PYTHON_EXE (
    for /f "delims=" %%v in ('py -3 -c "print(1)" 2^>nul') do if "%%v"=="1" set "PYTHON_EXE=py -3"
)

if not defined PYTHON_EXE (
    echo Python wurde nicht gefunden ^(oder "python" ist nur der Microsoft-Store-Platzhalter^).
    echo Versuche automatische Installation per winget...
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

    rem Frisch installiertes Python direkt am typischen Installationsort suchen,
    rem statt auf ein neues Terminal zu hoffen - der "python"-Befehl kann
    rem weiterhin auf den Microsoft-Store-Platzhalter zeigen, je nach PATH-Reihenfolge.
    for /d %%d in ("%LocalAppData%\Programs\Python\Python3*") do (
        if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
    )
    if not defined PYTHON_EXE (
        for /f "delims=" %%v in ('python -c "print(1)" 2^>nul') do if "%%v"=="1" set "PYTHON_EXE=python"
    )
    if not defined PYTHON_EXE (
        echo Python wurde installiert, konnte aber nicht automatisch gefunden werden.
        echo Bitte dieses Fenster schliessen, ein NEUES Terminal oeffnen und
        echo start.bat erneut starten ^(damit Windows den neuen PATH kennt^).
        pause
        exit /b 0
    )
    echo Python gefunden unter: %PYTHON_EXE%
)

rem --- 2. Virtuelle Umgebung + Abhaengigkeiten, falls noch nicht vorhanden ---
if not exist "venv\Scripts\python.exe" (
    echo Richte virtuelle Umgebung ein ^(einmalig, dauert etwas^)...
    %PYTHON_EXE% -m venv venv
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
