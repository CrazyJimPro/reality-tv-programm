# Reality-TV Programmübersicht (RTL / VOX / Sat.1 / ProSieben / RTL2 / Kabel Eins)

Ein privates, lokales Tool: scraped 2x pro Woche automatisch die Programmdaten
von RTL, VOX, Sat.1, ProSieben, RTL2 und Kabel Eins, filtert bekannte
Reality-TV-Formate heraus und zeigt sie in einer lokalen Web-App an — mit
einer Vorschau auf die nächste und übernächste Woche.

Läuft unter **Windows und Linux**.

## Installation: nur eine Datei herunterladen und ausführen

Es reicht, **eine einzige Datei** herunterzuladen — nicht das ganze Repo.
Der Rest des Projekts wird beim ersten Start automatisch von GitHub
nachgeladen.

**Windows:** [`start.bat`](start.bat) herunterladen (Rechtsklick auf den Link
→ "Ziel speichern unter" bzw. auf GitHub den "Raw"-Button → Strg+S) und
doppelklicken.
**Linux:** [`start.sh`](start.sh) herunterladen und ausführen:
```bash
chmod +x start.sh && ./start.sh
```

Egal von wo die Datei gestartet wird (Downloads-Ordner, USB-Stick, ...): Beim
ersten Lauf lädt sie automatisch das komplette Projekt nach
`%USERPROFILE%\reality-tv-programm` (Windows) bzw. `~/reality-tv-programm`
(Linux) herunter und macht dort weiter. Danach: Python-Check, virtuelle
Umgebung, Abhängigkeiten, automatische Aktualisierung (Mo + Do, 06:00 Uhr)
und der erste Datenabruf — alles automatisch, ca. 1-2 Minuten beim
allerersten Mal. Danach öffnet sich automatisch der Browser mit der
Übersicht unter http://127.0.0.1:5000

**Beim ersten Lauf wird außerdem automatisch eine Desktop-Verknüpfung
angelegt** ("Reality-TV Programm") — ab dann reicht ein Doppelklick darauf,
komplett **ohne sichtbares Konsolen-/Terminalfenster**. Alle Meldungen
landen dabei in `logs/start.log`, falls doch mal etwas schiefgeht. Läuft die
Web-App schon (z.B. weil die Verknüpfung versehentlich zweimal angeklickt
wurde), öffnet ein erneuter Klick einfach nur den Browser erneut, statt
einen zweiten Prozess zu starten. Zum Beenden: Python-Prozess im
Task-Manager (Windows) bzw. `pkill -f webapp/app.py` (Linux) — oder einfach
laufen lassen, das ist unproblematisch.

Die App muss nicht dauerhaft laufen: einfach starten, wenn du reinschauen
willst.

Was das Skript im Detail automatisch macht:
- lädt bei Bedarf den Rest des Projekts von GitHub herunter (nur beim
  allerersten Mal, wenn nur diese eine Datei vorhanden ist)
- prüft, ob Python vorhanden ist — falls nicht: installiert es selbst
  (Windows: `winget`, Linux: `apt-get`, braucht dort `sudo`)
- legt eine virtuelle Umgebung an und installiert die Abhängigkeiten
- richtet die automatische Aktualisierung ein (Windows-Aufgabenplanung
  bzw. Cronjob, jeweils montags + donnerstags 06:00 Uhr)
- holt beim allerersten Start einmalig sofort die aktuellen Programmdaten,
  damit direkt etwas zu sehen ist
- legt eine Desktop-Verknüpfung an (falls noch nicht vorhanden)
- startet die Web-App und öffnet den Browser (ohne sichtbares Fenster, wenn
  über die Desktop-Verknüpfung gestartet)

*(Wer lieber das ganze Repo selbst klont/als ZIP lädt, kann das natürlich
auch tun — `start.bat`/`start.sh` erkennen dann, dass der Rest schon da ist,
und überspringen den Download.)*

## Danach: Sendungen hinzufügen oder entfernen

**Am einfachsten über die Web-App:** oben auf der Übersicht auf
"Sendungen verwalten" klicken (oder direkt http://127.0.0.1:5000/einstellungen
öffnen). Dort gibt es eine Liste bekannter Reality-Formate zum An-/Abhaken.
Eigene, nicht gelistete Sendungen: Namen (und optional alternative
Schreibweisen, mit Komma getrennt) eintragen und auf **"Hinzufügen"**
klicken — erscheint sofort angehakt in der Liste. Das lässt sich beliebig
oft wiederholen, um mehrere eigene Sendungen auf einmal zu ergänzen. Erst
**"Speichern"** übernimmt alles endgültig: schreibt die komplette Auswahl in
`config/reality_shows.json` **und stößt sofort einen neuen Datenabruf an**
(dauert 1-2 Minuten, der Knopf zeigt solange "Wird gespeichert und
aktualisiert..." an) — die Übersicht zeigt danach direkt den neuen Stand,
ohne auf den nächsten automatischen Mo/Do-Lauf warten zu müssen.

<details>
<summary>Alternative: die Datei config/reality_shows.json direkt bearbeiten</summary>

Das ist eine einfache Textdatei, die mit jedem Editor (z.B. Notepad, VS Code)
bearbeitet werden kann — nützlich für Formate, die nicht in der Vorschlagsliste
der Web-App stehen, oder um Aliase eines bestehenden Eintrags anzupassen.

**Sendung hinzufügen:** neue Zeile nach folgendem Muster ergänzen:

```json
{ "name": "Neue Show", "aliases": ["Alternative Schreibweise"] }
```

`aliases` ist optional (`[]` wenn keine Alternativschreibweise bekannt ist),
hilft aber bei Formaten, die mal mit und mal ohne Zusatz laufen (z.B.
`"Der Bachelor"` mit Alias `"Bachelor"`).

**Sendung entfernen:** den passenden Eintrag (die ganze `{ ... }`-Zeile)
löschen. Auf ein korrektes Komma zwischen den verbleibenden Einträgen achten
— bei der letzten Zeile vor der schließenden `]` darf **kein** Komma mehr
stehen, sonst meldet der nächste Lauf einen JSON-Fehler.

Beispiel — vorher:
```json
{ "name": "Big Brother", "aliases": ["Promi Big Brother"] },
{ "name": "Love Island", "aliases": ["Love Island VIP"] },
```
nachher (Love Island entfernt):
```json
{ "name": "Big Brother", "aliases": ["Promi Big Brother"] },
```

</details>

Die Datei wird bei **jedem** Scraper-Lauf neu eingelesen, kein Neustart
nötig. Bearbeitest du `config/reality_shows.json` direkt (statt über die
Web-App), wirkt sich das erst ab dem nächsten Lauf aus — entweder automatisch
am Mo/Do 06:00 Uhr, oder sofort per Klick auf **"Jetzt aktualisieren"** oben
auf der Übersichtsseite. Wichtig beim Entfernen: bereits in
`data/programm.db` gespeicherte, vergangene Treffer dieser Sendung
verschwinden nicht rückwirkend aus der Datenbank, sondern werden ab dem
nächsten Lauf einfach nicht mehr neu erkannt/aktualisiert.

## Architektur (kurz)

- `scraper/sources/rtl.py` — RTL + VOX direkt von rtl.de (nur ~6-7 Tage Vorschau)
- `scraper/sources/tvspielfilm.py` — Aggregator, deckt alle 6 Sender bis zu 14
  Tage ab (Sat.1/ProSieben laufen inzwischen über Joyn, das selbst keine
  brauchbare mehrtägige Programmübersicht mehr bietet; RTL2/Kabel Eins haben
  gar keine eigene EPG-Quelle wie rtl.de — deshalb hier die einzige Quelle
  für diese vier Sender)
- `scraper/merge.py` — führt Duplikate aus beiden Quellen zusammen
- `scraper/filter.py` — Abgleich gegen `config/reality_shows.json` (wird
  beim allerersten Mal automatisch aus `config/reality_shows.default.json`
  angelegt; die Live-Datei ist bewusst nicht im Git-Repo verfolgt, damit
  eine Projekt-Auffrischung durch das Selbst-Update sie nie überschreibt)
- `scraper/storage.py` — SQLite (`data/programm.db`)
- `webapp/` — Flask-App: `/` zeigt die Programmübersicht (liest nur aus der
  DB; extrahiert per Regex "Staffel X"/"Folge Y" aus dem Beschreibungstext,
  falls vorhanden, und zeigt es als kleines Badge neben dem Titel — keine
  zusätzliche Scraping-Quelle, nur vorhandene Daten sichtbarer gemacht),
  `/einstellungen` verwaltet `config/reality_shows.json` (Vorschläge aus
  `webapp/vorschlaege.py` an-/abwählen, eigene Sendungen per "Hinzufügen"
  beliebig oft ergänzen, dann einmal "Speichern"),
  `/aktualisieren` (POST) stößt `scraper/run.py` sofort als Subprozess an
  (Knopf "Jetzt aktualisieren" auf der Startseite; wird beim Speichern in
  `/einstellungen` automatisch mit ausgelöst)
- `start.bat` / `start.sh` — die einzige Datei, die man ausführt: Installation
  + automatische Aktualisierung einrichten + Desktop-Verknüpfung anlegen +
  Web-App starten, alles in einem
- `start_versteckt.bat` / `start_versteckt.vbs` (nur Windows) — Ziel der
  Desktop-Verknüpfung: ruft `start.bat` ohne sichtbares Konsolenfenster auf
  und leitet alle Meldungen nach `logs/start.log` um (unter Linux reicht
  dafür `Terminal=false` in der `.desktop`-Datei, kein Hilfsskript nötig)

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

## Problembehebung

- **"Python wurde nicht gefunden ... Microsoft Store ..." trotz Python-Check:**
  Windows legt standardmäßig einen `python`-Platzhalter an, der nur auf den
  Microsoft Store verweist, aber kein echtes Python ist. `start.bat` erkennt
  das inzwischen und installiert automatisch per `winget` — falls die
  Meldung trotzdem erscheint, hilft meist ein manueller Python-Download von
  https://www.python.org/downloads/ (dabei "Add python.exe to PATH"
  anhaken) und `start.bat` danach in einem neuen Terminal erneut starten.
- **"Selbst-Update-Prüfung fehlgeschlagen":** meist ein TLS-Problem auf
  älteren Windows-Installationen (Windows nutzt für HTTPS-Verbindungen aus
  der Kommandozeile standardmäßig teils noch TLS 1.0/1.1, GitHub verlangt
  aber TLS 1.2 — wird inzwischen automatisch erzwungen). Zeigt die Meldung
  trotzdem "fehlgeschlagen": Internetverbindung/Firewall/Proxy prüfen, ob
  `raw.githubusercontent.com` erreichbar ist.
- **Skript wirkt "wie eingefroren" auf altem Stand, obwohl start.bat/
  start.sh neu heruntergeladen wurde:** ab dieser Version wird bei
  erkannter neuerer Version nicht mehr nur die Einstiegsdatei ersetzt,
  sondern das **komplette Projekt** (`%USERPROFILE%\reality-tv-programm`
  bzw. `~/reality-tv-programm`) frisch nachgeladen — vorher blieb eine
  bereits installierte Kopie für immer auf dem Stand der Erstinstallation
  hängen, egal wie oft man die einzelne Datei erneut herunterlud. Als
  Notlösung hilft immer: aktuelle `start.bat`/`start.sh` manuell neu
  herunterladen (https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.bat)
  und den installierten Ordner (`%USERPROFILE%\reality-tv-programm` bzw.
  `~/reality-tv-programm`) zur Sicherheit einmal komplett löschen, bevor
  man sie erneut ausführt.
