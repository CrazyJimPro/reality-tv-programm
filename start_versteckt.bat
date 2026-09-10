@echo off
rem Wird von der Desktop-Verknuepfung (per start_versteckt.vbs, versteckt)
rem aufgerufen. Leitet alle Meldungen von start.bat in logs\start.log um,
rem da bei versteckter Ausfuehrung kein Konsolenfenster sichtbar ist.
rem
rem WICHTIG: start.bat wird hier ueber den vollen Pfad (%~dp0) aufgerufen,
rem nicht als blosser Dateiname. Ist auf dem System die Sicherheitsrichtlinie
rem "NoDefaultCurrentDirectoryInExePath" gesetzt (deaktiviert die Suche im
rem aktuellen Verzeichnis fuer Befehle ohne expliziten Pfad), wuerde ein
rem blosses "call start.bat" sonst faelschlich "Datei nicht gefunden" melden,
rem obwohl sie direkt daneben liegt - per Test auf einem System mit dieser
rem Richtlinie reproduziert und verifiziert.
cd /d "%~dp0"
if not exist logs mkdir logs
call "%~dp0start.bat" > logs\start.log 2>&1
