@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === Reality-TV Programmuebersicht ===
echo.

set "SELBST=%~f0"
set "ZIEL_ORDNER=%USERPROFILE%\reality-tv-programm"

rem --- -1. Pruefen, ob auf GitHub eine neuere start.bat liegt. Wird eine
rem     gefunden, wird NICHT nur diese eine Datei ersetzt, sondern (in
rem     Schritt 0) das GESAMTE Projekt frisch nachgeladen - sonst wuerde
rem     der Rest des Codes (webapp/, scraper/, ...) einer bereits
rem     installierten Kopie fuer immer auf dem Stand der Erstinstallation
rem     haengen bleiben, selbst wenn sich start.bat "selbst aktualisiert".
rem     Schlaegt nicht mehr lautlos fehl, sondern meldet sich, wenn kein
rem     Internet/TLS-Verbindung klappt. ---
set "NEUERE_VERSION_GEFUNDEN="
del "%TEMP%\rtv_start_latest.bat" >nul 2>nul
> "%TEMP%\rtv_selfupdate.ps1" (
    echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    echo try {
    echo     ^(New-Object System.Net.WebClient^).DownloadFile^('https://raw.githubusercontent.com/CrazyJimPro/reality-tv-programm/main/start.bat','%TEMP%\rtv_start_latest.bat'^)
    echo } catch {
    echo     Write-Host "SELBSTUPDATE-FEHLER: $_"
    echo }
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\rtv_selfupdate.ps1"
del "%TEMP%\rtv_selfupdate.ps1" >nul 2>nul
if exist "%TEMP%\rtv_start_latest.bat" (
    findstr /b /l /c:"@echo off" "%TEMP%\rtv_start_latest.bat" >nul 2>nul
    if not errorlevel 1 (
        fc /b "%TEMP%\rtv_start_latest.bat" "%SELBST%" >nul 2>nul
        if errorlevel 1 set "NEUERE_VERSION_GEFUNDEN=1"
    ) else (
        echo Selbst-Update-Pruefung: heruntergeladene Datei sieht beschaedigt aus, ignoriere sie.
    )
    del "%TEMP%\rtv_start_latest.bat" >nul 2>nul
) else (
    echo Selbst-Update-Pruefung fehlgeschlagen ^(kein Internet oder Netzwerk/Firewall blockiert^) - fahre mit der vorhandenen Version fort.
)

rem --- 0. Projektordner bestimmen und bei Bedarf (neu) laden: entweder weil
rem     hier noch gar kein komplettes Projekt liegt (nur diese eine Datei
rem     wurde heruntergeladen), oder weil Schritt -1 eine neuere Version
rem     gefunden hat. In beiden Faellen wird der KOMPLETTE Code von GitHub
rem     aufgefrischt (nicht nur start.bat), venv/data/logs bleiben dabei
rem     unberuehrt (die liegen nicht im heruntergeladenen Quellcode). ---
if exist "requirements.txt" (
    set "PROJEKT_ZIEL=%cd%"
) else (
    set "PROJEKT_ZIEL=%ZIEL_ORDNER%"
)

set "MUSS_LADEN="
if not exist "requirements.txt" set "MUSS_LADEN=1"
if defined NEUERE_VERSION_GEFUNDEN set "MUSS_LADEN=1"

if defined MUSS_LADEN (
    echo Lade aktuellen Projektstand von GitHub ^(Code + Web-App werden aufgefrischt^)...
    rem PowerShell-Logik in eine temporaere .ps1-Datei schreiben statt als
    rem Inline-Befehl - vermeidet fragile verschachtelte Anfuehrungszeichen.
    > "%TEMP%\rtv_download.ps1" (
        echo $ErrorActionPreference = 'Stop'
        echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        echo Invoke-WebRequest -Uri 'https://github.com/CrazyJimPro/reality-tv-programm/archive/refs/heads/main.zip' -OutFile "$env:TEMP\rtv.zip"
        echo Expand-Archive -Path "$env:TEMP\rtv.zip" -DestinationPath "$env:TEMP\rtv-extract" -Force
        echo New-Item -ItemType Directory -Force -Path '%PROJEKT_ZIEL%' ^| Out-Null
        echo Copy-Item -Path "$env:TEMP\rtv-extract\reality-tv-programm-main\*" -Destination '%PROJEKT_ZIEL%' -Recurse -Force
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

    if /I not "%cd%"=="%PROJEKT_ZIEL%" (
        echo Projekt liegt jetzt unter: %PROJEKT_ZIEL%
    ) else (
        echo Projekt aufgefrischt.
    )
    echo Starte neu ...
    echo.
    start "" cmd /c call "%PROJEKT_ZIEL%\start.bat"
    exit /b 0
)

rem --- 0.5 Welcher Stand laeuft hier? Steht auch in logs\start.log und
rem     oben in der Kopfzeile der Web-App. ---
if exist "%~dp0VERSION" (
    < "%~dp0VERSION" set /p RTV_VERSION=
    echo Version: !RTV_VERSION!
    echo.
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

rem --- 3. Frueher angelegte automatische Aufgabe wieder entfernen. Die Daten
rem     werden jetzt bei jedem Start der App geholt (die Web-App stoesst den
rem     Scrape-Lauf beim Hochfahren selbst an) - es soll nichts mehr im
rem     Hintergrund laufen, wenn die App beendet ist. Bei aelteren
rem     Installationen liegt die Aufgabe noch in der Aufgabenplanung. ---
schtasks /Query /TN "RealityTV_Scraper" >nul 2>nul
if not errorlevel 1 (
    echo Entferne die fruehere automatische Aufgabe ^(wird nicht mehr gebraucht^)...
    schtasks /Delete /TN "RealityTV_Scraper" /F >nul 2>nul
    if errorlevel 1 echo Hinweis: Aufgabe "RealityTV_Scraper" konnte nicht entfernt werden - ggf. manuell in der Aufgabenplanung loeschen.
)

rem --- 4.5 Desktop-Verknuepfung anlegen, falls noch nicht vorhanden -
rem     startet kuenftig per Doppelklick ohne sichtbares Konsolenfenster
rem     (siehe start_versteckt.bat/.vbs), Meldungen landen in logs\start.log.
rem
rem     Der Desktop-Ordner wird NICHT mehr als "%USERPROFILE%\Desktop"
rem     geraten: ist der Desktop nach OneDrive umgeleitet (auf Windows 11
rem     haeufig), gibt es diesen Ordner gar nicht - die Verknuepfung landete
rem     dann im Nichts bzw. schlug fehl, und der Fehler wurde auch noch nach
rem     nul geschluckt. [Environment]::GetFolderPath('Desktop') liefert immer
rem     den tatsaechlich benutzten Ordner; Erfolg wie Fehlschlag werden
rem     ausgegeben (und landen damit auch in logs\start.log). ---
> "%TEMP%\rtv_shortcut.ps1" (
    echo $ErrorActionPreference = 'Stop'
    echo try {
    echo     $desktop = [Environment]::GetFolderPath^('Desktop'^)
    echo     if ^(-not $desktop -or -not ^(Test-Path -LiteralPath $desktop^)^) { throw "Desktop-Ordner nicht gefunden (gemeldet: '$desktop')" }
    echo     $ziel = Join-Path $desktop 'Reality-TV Programm.lnk'
    echo     if ^(Test-Path -LiteralPath $ziel^) { Write-Host "Desktop-Verknuepfung vorhanden: $ziel"; exit 0 }
    echo     $WshShell = New-Object -ComObject WScript.Shell
    echo     $Shortcut = $WshShell.CreateShortcut^($ziel^)
    echo     $Shortcut.TargetPath = '%~dp0start_versteckt.vbs'
    echo     $Shortcut.WorkingDirectory = '%~dp0'
    echo     $Shortcut.Description = 'Reality-TV Programmuebersicht starten'
    echo     $Shortcut.Save^(^)
    echo     Write-Host "Desktop-Verknuepfung angelegt: $ziel"
    echo } catch {
    echo     Write-Host "Desktop-Verknuepfung konnte nicht angelegt werden: $_"
    echo }
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\rtv_shortcut.ps1"
del "%TEMP%\rtv_shortcut.ps1" >nul 2>nul

rem --- 5. Web-App starten und Browser oeffnen (nur falls nicht schon eine
rem     laeuft - sonst Port-Konflikt, z.B. bei erneutem Klick auf die
rem     Desktop-Verknuepfung waehrend die App schon offen ist). Der
rem     Zustandstext in der netstat-Ausgabe ist sprachabhaengig (z.B.
rem     "LISTENING" vs. "ABHOEREN" auf deutschem Windows) - deshalb wird
rem     stattdessen direkt geprueft, ob 5000 als LOKALE Adresse auftaucht
rem     (2. Spalte), unabhaengig vom Zustandstext. ---
netstat -ano | findstr /r /c:"^ *TCP *[^ ]*:5000 " >nul 2>nul
if not errorlevel 1 (
    echo Web-App laeuft bereits - stosse Aktualisierung an und oeffne Browser ...
    rem Auch beim Klick auf die Verknuepfung waehrend die App schon laeuft
    rem sollen frische Daten geholt werden. Der Aufruf kommt sofort zurueck,
    rem der Lauf selbst passiert im Hintergrund der App.
    rem Kein "| Out-Null" verwenden: das Pipe-Zeichen wird in einer
    rem Klammer-Gruppe von cmd.exe auch innerhalb der Anfuehrungszeichen
    rem zickig behandelt - Zuweisung an $null tut dasselbe ohne Pipe.
    powershell -NoProfile -Command "try { $null = Invoke-WebRequest -UseBasicParsing -Method POST -Uri 'http://127.0.0.1:5000/aktualisieren' -TimeoutSec 10 } catch { }" >nul 2>nul
    start "" http://127.0.0.1:5000
    exit /b 0
)

echo.
echo Oeffne http://127.0.0.1:5000 im Browser ...
echo Die Programmdaten werden dabei im Hintergrund frisch geholt ^(1-2 Minuten^),
echo die Seite aktualisiert sich von selbst, sobald der Lauf fertig ist.
echo Dieses Fenster schliesst sich gleich von selbst, die App laeuft dann
echo ohne Fenster weiter. Zum Beenden den Knopf "Beenden" oben auf der Seite
echo benutzen - danach laeuft nichts mehr im Hintergrund.
echo.
rem Die App wird mit pythonw.exe gestartet: die hat gar kein Konsolenfenster,
rem dadurch kann dieses Fenster hier sofort zugehen, waehrend die App
rem weiterlaeuft. Ihre Meldungen schreibt sie nach logs\webapp.log.
rem Browser erst danach oeffnen - vorher antwortet Port 5000 noch nicht und
rem der Browser zeigte kurz eine Fehlerseite. ping statt timeout, weil
rem timeout bei umgeleiteter Eingabe (versteckter Start) aussteigt.
if exist "%~dp0venv\Scripts\pythonw.exe" (
    start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0webapp\app.py"
) else (
    start "" "%~dp0venv\Scripts\python.exe" "%~dp0webapp\app.py"
)
ping -n 4 127.0.0.1 >nul
start "" http://127.0.0.1:5000
exit /b 0
