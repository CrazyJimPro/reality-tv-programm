# Reality-TV Programmübersicht (RTL / VOX / Sat.1 / ProSieben)

Ein privates, lokales Tool: scraped 2x pro Woche automatisch die Programmdaten
von RTL, VOX, Sat.1 und ProSieben, filtert bekannte Reality-TV-Formate heraus
und zeigt sie in einer lokalen Web-App an — mit einer Vorschau auf die
nächste und übernächste Woche.

Läuft unter **Windows und Linux**.

## Installation

**1. Virtuelle Umgebung anlegen und Abhängigkeiten installieren**

Windows (PowerShell, im Projektordner):
```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Linux:
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

**2. Automatische Aktualisierung einrichten** (2x pro Woche, Mo + Do 06:00 Uhr)

Windows (PowerShell, im Projektordner):
```powershell
.\setup_task.ps1
```
Alternativ per GUI: Aufgabenplanung öffnen → Aufgabe erstellen → Trigger
"Wöchentlich", Montag + Donnerstag, 06:00 Uhr → Aktion "Programm starten":
`venv\Scripts\python.exe` mit Argument `scraper\run.py` und Startverzeichnis
= Projektordner.

Linux:
```bash
chmod +x setup_cron.sh && ./setup_cron.sh
```
Trägt automatisch einen Cronjob ein (mit `crontab -l` prüfbar). Voraussetzung:
ein laufender `cron`-Dienst (bei Ubuntu/Debian/Raspberry Pi OS standardmäßig
vorhanden).

Das war's mit der Installation — ab jetzt aktualisieren sich die Daten von
selbst. Alles Weitere unten ist optional / für den täglichen Gebrauch.

---

## Nach der Installation: Wie sehe ich etwas?

Die Datenbank ist direkt nach der Installation noch leer — der erste
automatische Lauf ist frühestens am nächsten Montag/Donnerstag 06:00 Uhr.
Für sofortige Daten den Scraper **einmal manuell** anstoßen:

```bash
# Windows
venv\Scripts\python.exe -m scraper.run

# Linux
./venv/bin/python -m scraper.run
```

Das dauert ca. 1-2 Minuten (viele Einzelseiten werden abgerufen). Ergebnis
prüfen: `data/programm.db` sollte danach existieren, Details/Fehler stehen
in `logs/scraper.log`.

**Dann die Web-App starten**, um die Übersicht im Browser zu sehen:

Windows: Doppelklick auf `start.bat` (oder `venv\Scripts\python.exe webapp\app.py`)
Linux: `./start.sh` (oder `./venv/bin/python webapp/app.py`)

Danach im Browser öffnen: **http://127.0.0.1:5000**

Die Web-App muss nicht dauerhaft laufen — sie liest bei jedem Seitenaufruf
einfach die aktuelle `data/programm.db`. Einfach starten, wenn du reinschauen
willst, und mit `Strg+C` im Terminal wieder beenden.

## Nach der Installation: Wie füge ich eine neue Sendung hinzu?

Die Liste der erkannten Reality-Formate steht in `config/reality_shows.json`.
Neue Zeile nach folgendem Muster ergänzen:

```json
{ "name": "Neue Show", "aliases": ["Alternative Schreibweise"] }
```

Speichern reicht — die Datei wird bei **jedem** Scraper-Lauf neu eingelesen,
kein Neustart, kein Neu-Deployen nötig. Die neue Show taucht dann ab dem
nächsten Lauf (automatisch oder manuell per `python -m scraper.run`) in der
Web-App auf, sofern sie im gewählten 2-Wochen-Zeitraum läuft.

---

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

## Automatisierung wieder entfernen

Windows:
```powershell
schtasks /Delete /TN RealityTV_Scraper /F
```

Linux:
```bash
crontab -l | grep -v '# RealityTV_Scraper' | crontab -
```

## Wichtige Hinweise

- **Rechtlich:** Automatisiertes Abrufen von rtl.de und tvspielfilm.de kann
  gegen deren Nutzungsbedingungen verstoßen, auch bei rein privatem Gebrauch.
  Das ist ein bewusst eingegangenes Risiko — keine Rechtsberatung. Nur 2x pro
  Woche abrufen hält die Serverlast gering.
- **Wartung:** Ändern die Seiten ihr Layout, muss der jeweilige Scraper in
  `scraper/sources/` angepasst werden (Selektoren sind zentral an einer
  Stelle pro Datei).
- Ausschließlich lokale Speicherung, kein Versand an Dritte.
