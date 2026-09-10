# Reality-TV Programmübersicht (RTL / VOX / Sat.1 / ProSieben / RTL2 / Kabel Eins)

Ein privates, lokales Tool: holt bei jedem Start die Programmdaten von RTL,
VOX, Sat.1, ProSieben, RTL2 und Kabel Eins, filtert bekannte
Reality-TV-Formate heraus und zeigt sie in einer lokalen Web-App an — mit
einer Vorschau auf die nächste und übernächste Woche.

Es läuft **nichts im Hintergrund**: die Daten werden geholt, wenn die App
gestartet wird — und mit dem Knopf **„Beenden"** auf der Seite ist alles
wieder aus. Kein Dienst, keine geplante Aufgabe, kein Cronjob.

Läuft unter **Windows und Linux**. In Kurzform:

| | Einmalig installieren | Danach starten |
|---|---|---|
| **Windows** | `start.bat` herunterladen und doppelklicken | Desktop-Verknüpfung „Reality-TV Programm" |
| **Linux** | `start.sh` herunterladen, `chmod +x`, ausführen | Desktop-Verknüpfung „Reality-TV Programm" |

Ausführlich mit allen Schritten steht das gleich unten.

## Erstmalige Installation

Heruntergeladen wird **eine einzige Datei** — nicht das ganze Repository.
Alles Weitere (Projektcode, Python, Abhängigkeiten, Desktop-Verknüpfung)
richtet diese Datei selbst ein.

### Windows

1. **Datei herunterladen:**
   [start.bat](https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.bat)
   — Rechtsklick auf den Link → *Ziel speichern unter …*, z.B. in `Downloads`.
   Der Ordner ist egal, die Datei sucht sich ihren Platz selbst.
2. **Doppelklick auf `start.bat`.** Warnt Windows mit *„Der Computer wurde
   durch Windows geschützt"*: auf *Weitere Informationen* → *Trotzdem
   ausführen* klicken (die Datei stammt aus dem Internet und ist nicht
   signiert).
3. **Warten.** Beim allerersten Mal dauert es ca. 2–5 Minuten: fehlt Python,
   wird es per `winget` mitinstalliert, dann folgen virtuelle Umgebung und
   Abhängigkeiten. Das Fenster zeigt, was gerade passiert, und **schließt
   sich am Ende von selbst**.
4. **Fertig.** Der Browser öffnet http://127.0.0.1:5000, die Programmdaten
   werden dabei im Hintergrund geholt (1–2 Minuten — die Seite zeigt so lange
   einen Hinweis und lädt sich danach von selbst neu). Auf dem Desktop liegt
   jetzt die Verknüpfung **„Reality-TV Programm"**.

Installiert wird nach `%USERPROFILE%\reality-tv-programm`
(also z.B. `C:\Users\DeinName\reality-tv-programm`). Die heruntergeladene
`start.bat` aus `Downloads` wird danach nicht mehr gebraucht.

### Linux

1. **Terminal öffnen** und diese drei Zeilen ausführen:

```bash
curl -fsSL -O https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.sh
chmod +x start.sh
./start.sh
```

2. **Warten.** Fehlt Python, wird es per `apt-get` nachinstalliert — dabei
   fragt das Skript nach dem `sudo`-Passwort. Danach folgen virtuelle
   Umgebung und Abhängigkeiten (beim allerersten Mal ca. 2–5 Minuten).
3. **Fertig.** Der Browser öffnet http://127.0.0.1:5000, die Programmdaten
   werden im Hintergrund geholt. Auf dem Desktop liegt die Verknüpfung
   **„Reality-TV Programm"** (sofern eine Desktop-Umgebung vorhanden ist —
   auf einem reinen Server entfällt sie). Manche Dateimanager fragen beim
   ersten Doppelklick einmalig nach *„Ausführen erlauben"* bzw.
   *„Vertrauen"*.

Installiert wird nach `~/reality-tv-programm`. Die heruntergeladene
`start.sh` wird danach nicht mehr gebraucht.

## Jedes weitere Mal starten

**Doppelklick auf die Desktop-Verknüpfung „Reality-TV Programm"** — unter
Windows wie unter Linux. Es öffnet sich **kein Konsolen- oder
Terminalfenster**; nach ein paar Sekunden geht der Browser auf.

Bei jedem Start passiert automatisch:

1. Es wird geprüft, ob auf GitHub eine **neuere Version** vorliegt. Wenn ja,
   wird der komplette Code aufgefrischt und die App neu gestartet (eine noch
   laufende Instanz wird vorher beendet).
2. Die **Programmdaten werden frisch geholt** (1–2 Minuten, im Hintergrund).
3. Der Browser öffnet die Übersicht.

Läuft die App bereits, startet ein erneuter Klick keinen zweiten Prozess,
sondern stößt nur eine Aktualisierung an und öffnet den Browser wieder.

**Ohne Desktop-Verknüpfung** geht es genauso — direkt im Projektordner:

| System  | Datei                                             |
|---------|---------------------------------------------------|
| Windows | `%USERPROFILE%\reality-tv-programm\start.bat`     |
| Linux   | `~/reality-tv-programm/start.sh`                  |

## Beenden

Oben auf der Seite den Knopf **„Beenden"** anklicken. Danach läuft nichts
mehr im Hintergrund — kein Task-Manager nötig, auch wenn ohne sichtbares
Fenster gestartet wurde. Das Browser-Fenster kann man anschließend
schließen.

Nur das Browser-Fenster zu schließen beendet die App **nicht** — sie läuft
dann weiter und ist unter http://127.0.0.1:5000 weiter erreichbar. Das ist
unproblematisch, kostet aber unnötig Speicher.

## Welche Version läuft gerade?

Oben in der Kopfzeile der Web-App steht ein kleines Abzeichen, z.B. `v1.4.9`;
beim Start landet die Nummer auch in `logs/start.log`. Sie kommt aus der
Datei `VERSION` im Projektordner und zeigt damit immer den tatsächlich
installierten Stand. Die neueste Version steht unter
[Releases](https://github.com/CrazyJimPro/reality-tv-programm/releases).

Verglichen wird bei jedem Start genau diese Nummer mit der auf GitHub —
aufgefrischt wird nur, wenn die dort **wirklich neuer** ist.

## Wo liegt was?

Alles unterhalb von `%USERPROFILE%\reality-tv-programm` bzw.
`~/reality-tv-programm`:

| Pfad                          | Inhalt                                              |
|-------------------------------|-----------------------------------------------------|
| `config/reality_shows.json`   | die persönliche Sendungsliste (bleibt bei Updates erhalten) |
| `data/programm.db`            | die geholten Sendetermine                           |
| `logs/start.log`              | Meldungen des Startskripts                          |
| `logs/webapp.log`             | Meldungen der Web-App                               |
| `logs/scraper.log`            | Protokoll der Datenabrufe                           |
| `VERSION`                     | installierte Versionsnummer                         |

Was das Startskript im Einzelnen automatisch erledigt:
- lädt beim allerersten Mal den Rest des Projekts von GitHub nach
- prüft, ob Python vorhanden ist — falls nicht: installiert es selbst
  (Windows: `winget`, Linux: `apt-get`, braucht dort `sudo`)
- legt eine virtuelle Umgebung an und installiert die Abhängigkeiten
- entfernt eine früher angelegte automatische Aufgabe bzw. den früheren
  Cron-Eintrag („RealityTV_Scraper", Mo + Do 06:00 Uhr) — seit die
  Aktualisierung beim Start läuft, wird der nicht mehr gebraucht
- legt die Desktop-Verknüpfung an (falls noch nicht vorhanden); der
  Desktop-Ordner wird beim System erfragt, damit sie auch bei einem nach
  OneDrive umgeleiteten Desktop sichtbar landet
- startet die Web-App ohne Fenster und öffnet den Browser, sobald sie
  antwortet

*(Wer lieber das ganze Repository klont oder als ZIP lädt, kann das tun —
`start.bat`/`start.sh` erkennen dann, dass der Rest schon da ist, und
überspringen den Download.)*

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
(läuft im Hintergrund, dauert 1-2 Minuten) — die Übersicht zeigt danach
direkt den neuen Stand, ohne dass die App neu gestartet werden muss.

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
Web-App), wirkt sich das erst ab dem nächsten Lauf aus — also beim nächsten
Start der App, oder sofort per Klick auf **"Jetzt aktualisieren"** oben auf
der Übersichtsseite. Wichtig beim Entfernen: bereits in
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
  `/aktualisieren` (POST) stößt `scraper/run.py` als Subprozess in einem
  Hintergrund-Thread an (Knopf "Jetzt aktualisieren" auf der Startseite;
  wird beim Speichern in `/einstellungen` automatisch mit ausgelöst und
  außerdem einmal beim Start der App). `/scrape-status` (JSON) meldet, ob
  ein Lauf noch läuft — die Übersicht lädt sich damit von selbst neu, sobald
  er fertig ist, und zeigt eine Fehlermeldung, wenn er fehlgeschlagen ist.
  `/beenden` (POST) beendet die App komplett (Knopf "Beenden")
- `VERSION` — installierte Versionsnummer, wird in der Kopfzeile der Web-App
  angezeigt (bei jedem Release mit hochzählen)
- `start.bat` / `start.sh` — die einzige Datei, die man ausführt: Installation
  + Desktop-Verknüpfung anlegen + Web-App starten, alles in einem. Die App
  läuft danach ohne Fenster weiter (Windows: `pythonw.exe`, Linux: `nohup`),
  der Browser wird erst geöffnet, wenn Port 5000 wirklich antwortet
- `start_versteckt.bat` / `start_versteckt.vbs` (nur Windows) — Ziel der
  Desktop-Verknüpfung: ruft `start.bat` ohne sichtbares Konsolenfenster auf
  und leitet alle Meldungen nach `logs/start.log` um (unter Linux reicht
  dafür `Terminal=false` in der `.desktop`-Datei, kein Hilfsskript nötig)

Jede Quelle scheitert isoliert (siehe `logs/scraper.log` und die
Status-Anzeige oben in der Web-App): Schlägt eine Quelle fehl, bleiben die
zuletzt erfolgreich gespeicherten Daten unangetastet.

## Frühere Hintergrund-Automatisierung

Bis Version 1.3.0 hat sich das Tool per Windows-Aufgabenplanung bzw. Cronjob
zweimal wöchentlich (Mo + Do, 06:00 Uhr) selbst aktualisiert. Das gibt es
nicht mehr: aktualisiert wird bei jedem Start der App. `start.bat`/`start.sh`
**entfernen einen noch vorhandenen Alt-Eintrag automatisch** beim nächsten
Lauf. Von Hand geht es so —

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
  Das ist ein bewusst eingegangenes Risiko — keine Rechtsberatung. Abgerufen
  wird nur beim Start der App (und auf Knopfdruck), das hält die Serverlast
  gering.
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
- **"Versionsprüfung fehlgeschlagen":** meist ein TLS-Problem auf
  älteren Windows-Installationen (Windows nutzt für HTTPS-Verbindungen aus
  der Kommandozeile standardmäßig teils noch TLS 1.0/1.1, GitHub verlangt
  aber TLS 1.2 — wird inzwischen automatisch erzwungen). Zeigt die Meldung
  trotzdem "fehlgeschlagen": Internetverbindung/Firewall/Proxy prüfen, ob
  `raw.githubusercontent.com` erreichbar ist.
- **Klick auf die Verknüpfung bewirkt gar nichts** (kein Browser, kein
  neuer Eintrag in `logs/start.log`): das betrifft Installationen vor
  v1.4.6. Dort hielt die laufende App die Logdatei offen, wodurch jeder
  weitere Start sofort abbrach. Abhilfe: die App über den Knopf **„Beenden"**
  schließen (oder den Rechner neu starten) und die Verknüpfung dann erneut
  anklicken — damit wird auf die aktuelle Version aufgefrischt, und danach
  tritt das nicht mehr auf.
- **Angezeigte Version bleibt auf einem alten Stand:** bis v1.4.2 löste nur
  eine geänderte `start.bat` eine Auffrischung aus; Releases, die nur den
  übrigen Code änderten, kamen nicht an. Seit v1.4.8 entscheidet die
  Versionsnummer. Als Notlösung hilft immer: aktuelle
  [start.bat](https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.bat)
  bzw. [start.sh](https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.sh)
  herunterladen, den installierten Ordner (`%USERPROFILE%\reality-tv-programm`
  bzw. `~/reality-tv-programm`) löschen und die Datei erneut ausführen — die
  persönliche Sendungsliste geht dabei allerdings mit verloren
  (`config/reality_shows.json` vorher sichern).
