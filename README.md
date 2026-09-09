# Reality-TV Programmübersicht (RTL / VOX / Sat.1 / ProSieben)

Ein privates, lokales Tool: scraped 2x pro Woche automatisch die Programmdaten
von RTL, VOX, Sat.1 und ProSieben, filtert bekannte Reality-TV-Formate heraus
und zeigt sie in einer lokalen Web-App an — mit einer Vorschau auf die
nächste und übernächste Woche.

Läuft unter **Windows und Linux**.

## Einmaliges Setup

```bash
python3 -m venv venv
```

Windows:
```powershell
venv\Scripts\pip install -r requirements.txt
```

Linux:
```bash
./venv/bin/pip install -r requirements.txt
```

## Manuell testen

```bash
# Windows
venv\Scripts\python.exe -m scraper.run

# Linux
./venv/bin/python -m scraper.run
```

Prüfen, ob Daten angekommen sind: `data/programm.db` sollte danach existieren
und wachsen; Details/Fehler stehen in `logs/scraper.log`.

## Web-App starten

Windows: Doppelklick auf `start.bat` (oder `venv\Scripts\python.exe webapp\app.py`)
Linux: `./start.sh` (oder `./venv/bin/python webapp/app.py`)

Danach im Browser: http://127.0.0.1:5000

## Automatische Aktualisierung einrichten (2x pro Woche, Mo + Do 06:00 Uhr)

Windows (PowerShell, im Projektverzeichnis):
```powershell
.\setup_task.ps1
```
Alternativ per GUI: Aufgabenplanung öffnen → Aufgabe erstellen → Trigger
"Wöchentlich", Montag + Donnerstag, 06:00 Uhr → Aktion "Programm starten":
`venv\Scripts\python.exe` mit Argument `scraper\run.py` und Startverzeichnis
= Projektordner.

Linux:
```bash
./setup_cron.sh
```
Trägt automatisch einen Cronjob ein (`crontab -l` zum Prüfen).

## Reality-Show-Liste erweitern

Neue Sendung hinzufügen: Zeile in `config/reality_shows.json` ergänzen, z.B.

```json
{ "name": "Neue Show", "aliases": ["Alternative Schreibweise"] }
```

Wird beim nächsten Lauf automatisch berücksichtigt — kein Neustart nötig.

## Architektur (kurz)

- `scraper/sources/rtl.py` — RTL + VOX direkt von rtl.de (nur ~6-7 Tage Vorschau)
- `scraper/sources/tvspielfilm.py` — Aggregator, deckt alle 4 Sender bis zu 14 Tage ab
  (Sat.1/ProSieben laufen inzwischen über Joyn, das selbst keine brauchbare
  mehrtägige Programmübersicht mehr bietet — deshalb hier die einzige Quelle für diese beiden)
- `scraper/merge.py` — führt Duplikate aus beiden Quellen zusammen
- `scraper/filter.py` — Abgleich gegen `config/reality_shows.json`
- `scraper/storage.py` — SQLite (`data/programm.db`)
- `webapp/` — Flask-App, liest nur aus der DB

Jede Quelle scheitert isoliert (siehe `logs/scraper.log` und die
Status-Anzeige oben in der Web-App): Schlägt eine Quelle fehl, bleiben die
zuletzt erfolgreich gespeicherten Daten unangetastet.

## Wichtige Hinweise

- **Rechtlich:** Automatisiertes Abrufen von rtl.de und tvspielfilm.de kann
  gegen deren Nutzungsbedingungen verstoßen, auch bei rein privatem Gebrauch.
  Das ist ein bewusst eingegangenes Risiko — keine Rechtsberatung. Nur 2x pro
  Woche abrufen hält die Serverlast gering.
- **Wartung:** Ändern die Seiten ihr Layout, muss der jeweilige Scraper in
  `scraper/sources/` angepasst werden (Selektoren sind zentral an einer
  Stelle pro Datei).
- Ausschließlich lokale Speicherung, kein Versand an Dritte.
