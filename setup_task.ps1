# Richtet die Windows-Aufgabenplanung ein: fuehrt scraper/run.py
# jeden Montag und Donnerstag um 06:00 Uhr automatisch aus.
#
# Einmalig ausfuehren (PowerShell, im Projektverzeichnis):
#   .\setup_task.ps1

$ProjektPfad = $PSScriptRoot
$VenvPython = Join-Path $ProjektPfad "venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Keine venv unter $VenvPython gefunden."
    Write-Host "Bitte zuerst einrichten:"
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

$RunScript = Join-Path $ProjektPfad "scraper\run.py"
$Aktion = "`"$VenvPython`" `"$RunScript`""

schtasks /Create /TN "RealityTV_Scraper" /TR $Aktion /SC WEEKLY /D MON,THU /ST 06:00 /RL LIMITED /F

Write-Host "Aufgabe 'RealityTV_Scraper' eingerichtet: laeuft montags + donnerstags um 06:00 Uhr."
Write-Host "Manuell testen: schtasks /Run /TN RealityTV_Scraper"
Write-Host "Wieder entfernen: schtasks /Delete /TN RealityTV_Scraper /F"
