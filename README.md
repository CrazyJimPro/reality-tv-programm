# Reality-TV Programmübersicht (RTL / VOX / Sat.1 / ProSieben)

Ein privates, lokales Tool: scraped 2x pro Woche automatisch die Programmdaten
von RTL, VOX, Sat.1 und ProSieben, filtert bekannte Reality-TV-Formate heraus
und zeigt sie in einer lokalen Web-App an — mit einer Vorschau auf die
nächste und übernächste Woche.

Läuft unter **Windows und Linux**.

## Installation: nur eine Datei ausführen

Kein manuelles Einrichten nötig — **eine** Datei erledigt alles automatisch:
Python-Check, virtuelle Umgebung, Abhängigkeiten, automatische Aktualisierung
(Mo + Do, 06:00 Uhr) und den ersten Datenabruf.

**Windows:** Doppelklick auf [`start.bat`](start.bat)
**Linux:** im Terminal `chmod +x start.sh && ./start.sh`

Beim allerersten Ausführen dauert es ca. 1-2 Minuten (venv wird angelegt,
Abhängigkeiten installiert, erste Programmdaten geholt). Danach öffnet sich
automatisch der Browser mit der Übersicht unter http://127.0.0.1:5000

**Jedes weitere Mal** einfach dieselbe Datei nochmal ausführen — bereits
erledigte Schritte (venv, automatische Aktualisierung, Erstabruf) werden
übersprungen, es öffnet sich nur die Web-App. Die App muss nicht dauerhaft
laufen: einfach starten, wenn du reinschauen willst, `Strg+C` zum Beenden.

Was das Skript im Detail automatisch macht:
- prüft, ob Python vorhanden ist — falls nicht: installiert es selbst
  (Windows: `winget`, Linux: `apt-get`, braucht dort `sudo`)
- legt eine virtuelle Umgebung an und installiert die Abhängigkeiten
- richtet die automatische Aktualisierung ein (Windows-Aufgabenplanung
  bzw. Cronjob, jeweils montags + donnerstags 06:00 Uhr)
- holt beim allerersten Start einmalig sofort die aktuellen Programmdaten,
  damit direkt etwas zu sehen ist
- startet die Web-App und öffnet den Browser

## Danach: eine neue Sendung hinzufügen

Die Liste der erkannten Reality-Formate steht in
[`config/reality_shows.json`](config/reality_shows.json). Neue Zeile nach
folgendem Muster ergänzen:

```json
{ "name": "Neue Show", "aliases": ["Alternative Schreibweise"] }
```

Speichern reicht — die Datei wird bei **jedem** Scraper-Lauf neu eingelesen,
kein Neustart nötig. Die neue Show taucht ab dem nächsten Lauf (automatisch
oder durch erneutes Ausführen von `start.bat`/`start.sh`) in der Web-App auf,
sofern sie im gewählten 2-Wochen-Zeitraum läuft.

## Architektur (kurz)

- `scraper/sources/rtl.py` — RTL + VOX direkt von rtl.de (nur ~6-7 Tage Vorschau)
- `scraper/sources/tvspielfilm.py` — Aggregator, deckt alle 4 Sender bis zu 14 Tage ab
  (Sat.1/ProSieben laufen inzwischen über Joyn, das selbst keine brauchbare
  mehrtägige Programmübersicht mehr bietet — deshalb hier die einzige Quelle für diese beiden)
- `scraper/merge.py` — führt Duplikate aus beiden Quellen zusammen
- `scraper/filter.py` — Abgleich gegen `config/reality_shows.json`
- `scraper/storage.py` — SQLite (`data/programm.db`)
- `webapp/` — Flask-App, liest nur aus der DB
- `start.bat` / `start.sh` — die einzige Datei, die man ausführt: Installation
  + automatische Aktualisierung einrichten + Web-App starten, alles in einem

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
