# Reality-TV Programmübersicht

**RTL · VOX · Sat.1 · ProSieben · RTL2 · Kabel Eins · sixx · RTLup · VOXup ·
Nitro · Pro7 Maxx · Sat.1 Gold · TLC · DMAX · RTL+ (Streaming)**

Ein privates, lokales Tool. Es holt die Programmdaten der 14 Sender, sucht
darin deine Reality-TV-Formate heraus und zeigt sie in einer kleinen Web-App
im Browser — als Vorschau auf die **nächste und übernächste Woche**.

Welche Sendungen dich interessieren, bestimmst du selbst: aus einer Liste
bekannter Formate zum Anhaken, oder von Hand ergänzt.

Es läuft **nichts im Hintergrund**: Die Daten werden geholt, wenn du die App
startest — und mit dem Knopf **„Beenden"** ist alles wieder aus. Kein Dienst,
keine geplante Aufgabe, kein Cronjob.

## Inhalt

| Ich möchte … | Abschnitt |
|---|---|
| das Tool zum ersten Mal einrichten | [Installieren](#installieren) |
| es täglich benutzen | [Starten und beenden](#starten-und-beenden) |
| festlegen, welche Sendungen angezeigt werden | [Sendungen verwalten](#sendungen-verwalten) |
| Reality-Formate finden, die ich noch nicht kenne | [Neue Formate entdecken](#neue-formate-entdecken) |
| Gesehenes abhaken, Wiederholungen ausblenden | [Gesehen und Wiederholungen](#gesehen-und-wiederholungen) |
| Starts bei Joyn, Prime Video, Netflix sehen | [Streaming-Starts (TMDB)](#streaming-starts-tmdb) |
| meine Sendungsliste sichern | [Sendungsliste sichern](#sendungsliste-sichern) |
| meine Liste auf einen anderen Rechner holen | [Sicherung einspielen](#sicherung-einspielen) |
| ein Problem lösen | [Wenn etwas nicht klappt](#wenn-etwas-nicht-klappt) |
| wissen, wie es funktioniert | [Technisches](#technisches) |

---

# Installieren

Du lädst **eine einzige Datei** herunter — nicht das ganze Projekt. Alles
Weitere (Programmcode, Python, Zubehör, Desktop-Verknüpfung) richtet diese
Datei selbst ein. Einen Schlüssel oder ein Konto brauchst du nicht.

## Windows

1. **Datei herunterladen:** Rechtsklick auf
   [start.bat](https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.bat)
   → *Ziel speichern unter …* → z.B. in `Downloads`. Wo genau, ist egal.
2. **Doppelklick auf `start.bat`.**
3. Erscheint das blaue Fenster **„Der Computer wurde durch Windows
   geschützt"**: auf *Weitere Informationen* klicken, dann auf *Trotzdem
   ausführen*. (Die Datei kommt aus dem Internet und ist nicht signiert —
   deshalb fragt Windows nach.)
4. **Warten.** Beim allerersten Mal dauert es etwa 2–5 Minuten. Fehlt Python
   auf dem Rechner, wird es automatisch mitinstalliert. Das schwarze Fenster
   zeigt, was gerade passiert, und **schließt sich am Ende von selbst**.
5. **Fertig.** Der Browser öffnet sich, und auf dem Desktop liegt jetzt die
   Verknüpfung **„Reality-TV Programm"**.

Das Programm liegt danach unter `%USERPROFILE%\reality-tv-programm` (also
z.B. `C:\Users\DeinName\reality-tv-programm`). Die heruntergeladene
`start.bat` in `Downloads` brauchst du nicht mehr.

## Linux

1. **Terminal öffnen** und diese drei Zeilen nacheinander ausführen:

```bash
curl -fsSL -O https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.sh
chmod +x start.sh
./start.sh
```

2. **Warten.** Fehlt Python oder ein Zubehörpaket, installiert das Skript es
   nach und **fragt dabei nach deinem Passwort** (`sudo`). Beim allerersten
   Mal dauert alles zusammen etwa 2–5 Minuten.
3. **Fertig.** Der Browser öffnet sich, und auf dem Desktop liegt die
   Verknüpfung **„Reality-TV Programm"**. Manche Dateimanager fragen beim
   ersten Doppelklick einmalig nach *„Ausführen erlauben"* bzw. *„Vertrauen"*.

Das Programm liegt danach unter `~/reality-tv-programm`. Die heruntergeladene
`start.sh` brauchst du nicht mehr.

> **Wichtig beim allerersten Mal unter Linux:** Führe `start.sh` einmal im
> **Terminal** aus, nicht per Doppelklick. Nur dort kann die Passwortabfrage
> erscheinen, falls noch etwas nachinstalliert werden muss. Ab dem zweiten Mal
> geht die Desktop-Verknüpfung.

## Beim ersten Start

Die Übersicht ist zunächst leer oder dünn besetzt — die Programmdaten werden
im Hintergrund geholt, und das **dauert 1–2 Minuten**. Die Seite zeigt so
lange einen Hinweis und lädt sich danach von selbst neu. Danach lohnt sich
der Blick in [Sendungen verwalten](#sendungen-verwalten): Dort legst du fest,
wonach überhaupt gesucht wird.

---

# Starten und beenden

**Starten:** Doppelklick auf die Desktop-Verknüpfung **„Reality-TV
Programm"** — unter Windows wie unter Linux. Es öffnet sich **kein** schwarzes
Fenster; nach ein paar Sekunden geht der Browser auf.

Bei jedem Start passiert automatisch:

1. Es wird geprüft, ob es eine **neuere Version** gibt, und falls ja, wird sie
   installiert. Deine Sendungsliste bleibt dabei unangetastet.
2. Die **Programmdaten werden frisch geholt** (1–2 Minuten, im Hintergrund —
   die Seite ist sofort da und lädt sich nach, sobald der Lauf fertig ist).
3. Der Browser öffnet die Übersicht.

Läuft die App schon, startet ein erneuter Klick nichts doppelt — er frischt
nur die Daten auf und holt das Browserfenster zurück.

**Ohne Desktop-Verknüpfung** geht es genauso, direkt im Projektordner:

| System | Datei |
|---|---|
| Windows | `%USERPROFILE%\reality-tv-programm\start.bat` |
| Linux | `~/reality-tv-programm/start.sh` |

**Beenden:** Oben auf der Seite den Knopf **„Beenden"** anklicken. Erst dann
läuft nichts mehr im Hintergrund — kein Task-Manager nötig, auch wenn ohne
sichtbares Fenster gestartet wurde. Nur das Browserfenster zu schließen
genügt **nicht**; die App läuft dann weiter. Schlimm ist das nicht, sie
kostet nur unnötig Speicher.

**Zwischendurch aktualisieren:** Der Knopf **„Jetzt aktualisieren"** oben auf
der Übersicht holt die Programmdaten neu, ohne die App neu zu starten.

**Welche Version läuft?** Oben in der Kopfzeile steht ein kleines Abzeichen,
z.B. `v1.4.10`; beim Start landet die Nummer auch in `logs/start.log`. Die
neueste steht unter
[Releases](https://github.com/CrazyJimPro/reality-tv-programm/releases).

**Zugriff von einem anderen Rechner im Netzwerk:** Läuft die App z.B. in einer
VM, erreichst du sie auch über `http://<IP-der-VM>:5000` von einem anderen
Gerät im selben Netzwerk — nicht nur über `localhost` auf der VM selbst. Ohne
Login-Schutz: nur in einem vertrauenswürdigen (Heim-)Netzwerk nutzen.

---

# Sendungen verwalten

Hier bestimmst du, wonach das Tool überhaupt sucht. Alles andere aus dem
Fernsehprogramm wird ignoriert.

## So geht's

1. Oben auf der Übersicht auf **„Sendungen verwalten →"** klicken
   (oder direkt http://127.0.0.1:5000/einstellungen öffnen).
2. In der Liste bekannter Reality-Formate die **Häkchen setzen oder
   entfernen**.
3. Unten auf **„Speichern"** klicken. **Ohne diesen Klick ist nichts
   gespeichert.**

Nach dem Speichern läuft automatisch ein neuer Datenabruf (1–2 Minuten, im
Hintergrund). Die Übersicht zeigt danach direkt den neuen Stand — die App
muss dafür nicht neu gestartet werden.

## Eine eigene Sendung ergänzen

Läuft dein Format nicht in der Vorschlagsliste:

1. Auf der Seite **„Sendungen verwalten"** zum Abschnitt **„Eigene Sendung
   hinzufügen"**.
2. Den **Namen** eintragen, so wie er im Fernsehprogramm steht.
3. Optional **alternative Schreibweisen** ergänzen, mit Komma getrennt. Das
   lohnt sich bei Formaten, die mal mit und mal ohne Zusatz laufen — etwa
   `Der Bachelor` mit dem Alias `Bachelor`.
4. Auf **„Hinzufügen"** klicken. Die Sendung erscheint sofort angehakt in der
   Liste.
5. Schritte 2–4 beliebig oft wiederholen, wenn du mehrere ergänzen willst.
6. Zum Schluss **einmal** auf **„Speichern"**.

Der Umweg über „Hinzufügen" ist Absicht: So löst du am Ende **einen**
Datenabruf aus statt einen pro Sendung.

## Was du erwarten kannst

- Die Sendungsliste wird bei **jedem** Datenabruf neu eingelesen, ein
  Neustart ist nie nötig.
- Beim **Entfernen** einer Sendung verschwinden bereits gespeicherte,
  vergangene Termine nicht rückwirkend aus der Datenbank — sie werden ab dem
  nächsten Lauf einfach nicht mehr neu erkannt.
- Steht eine Sendung trotz Häkchen nicht in der Übersicht, läuft sie in den
  erfassten zwei Wochen schlicht nicht — oder sie steht im Programm unter
  einer anderen Schreibweise. Dann hilft ein Alias (siehe oben).
- **Sendungen, die nur im Streaming starten** (z. B. Temptation Island VIP oder
  CoupleChallenge auf RTL+) stehen in keinem Fernsehprogramm. Sie erscheinen
  mit dem Sender **RTL+**, sobald sie in deiner Liste stehen und die
  RTL+-Seite einen Starttermin nennt. Dabei wird nichts hochgerechnet: Nennt
  die Seite keinen Termin, erscheint auch nichts. Steht keine Uhrzeit dabei,
  zeigt die Übersicht 00:00 und sagt in der Beschreibung ausdrücklich, dass das
  nur ein Platzhalter ist.

<details>
<summary>Alternative: die Datei <code>config/reality_shows.json</code> direkt bearbeiten</summary>

Das ist eine einfache Textdatei, die sich mit jedem Editor (Notepad, VS Code)
bearbeiten lässt.

**Sendung hinzufügen** — neue Zeile nach diesem Muster ergänzen:

```json
{ "name": "Neue Show", "aliases": ["Alternative Schreibweise"] }
```

`aliases` ist optional (`[]`, wenn keine Alternativschreibweise bekannt ist).

**Sendung entfernen** — den passenden Eintrag (die ganze `{ … }`-Zeile)
löschen. Dabei auf die Kommas achten: Bei der letzten Zeile vor der
schließenden `]` darf **kein** Komma mehr stehen, sonst meldet der nächste
Lauf einen JSON-Fehler.

Beispiel, vorher:
```json
{ "name": "Big Brother", "aliases": ["Promi Big Brother"] },
{ "name": "Love Island", "aliases": ["Love Island VIP"] },
```
nachher (Love Island entfernt):
```json
{ "name": "Big Brother", "aliases": ["Promi Big Brother"] },
```

Änderungen von Hand wirken sich erst beim nächsten Datenabruf aus — also beim
nächsten Start der App oder sofort per **„Jetzt aktualisieren"**.

</details>

---

# Neue Formate entdecken

Die Übersicht zeigt nur, was in deiner Liste steht — von einem neuen Format
würdest du so nie erfahren. Deshalb sucht jeder Datenabruf zusätzlich im
gesamten Programm aller 14 Sender nach Sendungen, die **nach ihrem Genre**
Reality-TV sind, aber noch nicht in deiner Liste stehen.

## So geht's

1. Auf der Übersicht, oberhalb von „Nächste Woche", steht der Kasten
   **„Neu entdeckt: … Reality-Formate"**. Draufklicken klappt ihn auf.
2. Zu jedem Titel siehst du Sender, Genre, wie oft er in den zwei Wochen läuft
   und den nächsten Termin.
3. **„Hinzufügen"** nimmt die Sendung in deine Liste auf. Ihre Termine stehen
   **sofort** in der Übersicht — ohne Warten auf einen neuen Datenabruf, du
   kannst also mehrere hintereinander hinzufügen.
4. **„Ausblenden"** schlägt einen Titel nicht mehr vor.

Darunter gibt es einen zweiten, zugeklappten Kasten **„Weitere
Doku-Soaps"** — Auswanderer-, Renovier-, Pfandleiher-Soaps und Ähnliches.
Der ist bewusst getrennt, weil er deutlich mehr und gemischtere Treffer hat.

## Was du erwarten kannst

- **Woran erkannt wird:** am Genre, das tvspielfilm.de zu jeder Sendung
  vergibt. Im ersten Kasten landet alles mit „Reality", „Dating" oder
  „Kuppel" im Genre (z. B. „Realitysoap", „Datingshow"). Im zweiten alles mit
  „…soap" — ohne fiktionale Serien wie GZSZ und ohne gespielte Gerichts- und
  Ermittler-Formate (Barbara Salesch, K11), die sonst alles überdecken würden.
- RTL+-Sendungen tauchen hier nicht auf: RTL+ hat keine Genres, dort wird nur
  gezielt nach den Namen aus deiner Liste gesucht.
- **Ausgeblendetes zurückholen:** unter **„Sendungen verwalten"** im
  Abschnitt **„Ausgeblendete Vorschläge"** → **„Wieder anzeigen"**.
- Hinzugefügt wird der Titel genau so, wie er im Programm steht (z. B.
  „Verpfuscht – Ein Fall für die Beauty Docs"). Läuft das Format auch unter
  anderen Titeln, kannst du in „Sendungen verwalten" zusätzlich eine kürzere
  Schreibweise als eigene Sendung ergänzen.

---

# Gesehen und Wiederholungen

## Eine Folge als gesehen markieren

1. Rechts in der Zeile der Sendung auf das **✓** klicken.
2. Der Knopf wird grün, die Zeile blasser.
3. Nochmal klicken nimmt das Häkchen wieder weg.

Das Häkchen gilt für die **Folge**, nicht nur für den einen Termin: Läuft
dieselbe Folge noch einmal (etwa nachts), ist sie dort automatisch mit
abgehakt. Gespeichert wird es in der App selbst — am PC und am Handy siehst
du also denselben Stand.

## Wiederholungen erkennen und ausblenden

Läuft dieselbe Folge mehrmals, steht bei allen Terminen bis auf einen ein
gestricheltes **„Wiederholung"**. Fährst du mit der Maus darüber, steht da,
wann die Hauptausstrahlung läuft.

Über der Übersicht gibt es zwei Schalter:

- **„Wiederholungen ausblenden"** — zeigt jede Folge nur noch einmal
- **„Gesehenes ausblenden"** — blendet abgehakte Folgen aus

Die Schalter merkt sich der jeweilige Browser, sie bleiben also auch nach dem
Neustart der App an. Ist an einem Tag alles ausgeblendet, steht dort ein
Hinweis statt einer leeren Liste.

## Was du erwarten kannst

- **Woran eine Wiederholung erkannt wird:** Die Programmseiten kennzeichnen
  Wiederholungen nicht. Das Tool liest aber für jede gefundene Sendung
  Staffel/Folge und den Folgentitel nach (z. B. „Staffel 11, Folge 16" oder
  „Kanada: Alexander und Melanie"). Gleiche Folge = gleiche Sendung.
- **Welcher Termin als Hauptausstrahlung gilt:** der früheste **außerhalb der
  Nacht** (0–6 Uhr). Spartensender zeigen eine Folge oft nachts um 01:25 und
  dieselbe abends um 18:35 — ausgeblendet wird dann der Nachttermin, nicht der
  Abendtermin.
- Auch Folgen der **Vorwoche** zählen: Läuft eine Folge, die vor einer Woche
  schon kam, erneut, ist sie eine Wiederholung. Was schon gelaufen ist, bevor
  du die App das erste Mal gestartet hast, kann das Tool nicht wissen.
- Manche Sendungen haben weder Folgennummer noch Folgentitel (z. B. einige
  Magazine). Die werden nie als Wiederholung markiert, das Häkchen gilt bei
  ihnen nur für den einen Termin.
- Beim **ersten Datenabruf nach dem Update** dauert es einmalig etwa eine
  halbe Minute länger, weil die Folgenangaben aller Termine gelesen werden.
  Danach kommen nur noch neue Termine dazu.
- Die Häkchen sind **nicht** Teil der Sicherung (sie stehen in
  `data/programm.db`, nicht in der Sendungsliste).

---

# Streaming-Starts (TMDB)

Viele Reality-Formate starten zuerst im Streaming und erst Wochen später — oder
nie — im Fernsehen. Joyn und Prime Video selbst lassen sich dafür nicht sinnvoll
auslesen. Die Film- und Seriendatenbank **TMDB** (themoviedb.org) führt aber die
kommenden Folgen mit Datum. Mit einem kostenlosen TMDB-Schlüssel zeigt die App:

- **Starts, die in keinem Fernsehprogramm stehen**, direkt in der Wochenübersicht
  (Sender z. B. „Joyn" oder „Prime Video", statt Uhrzeit ein „—")
- **Demnächst:** Staffelstarts deiner Sendungen in den drei Monaten nach den zwei
  Wochen, ganz unten auf der Übersicht
- **Neu entdeckt:** zusätzlich kommende deutsche Reality-Formate bei Joyn, RTL+,
  Prime Video und Netflix

Ohne Schlüssel funktioniert alles andere wie bisher.

## Einrichten — wenn die Streaming-Info-App auf demselben Rechner läuft

1. Oben auf **„Sendungen verwalten →"**.
2. Nach unten zum Abschnitt **„Streaming-Starts (TMDB)"**.
3. Auf **„Schlüssel aus Streaming-Info übernehmen"** klicken.

Der Knopf erscheint nur, wenn die Streaming-Info-App am üblichen Ort installiert
ist (`%USERPROFILE%\streaming-info` bzw. `~/streaming-info`) und dort ein
Schlüssel eingetragen ist.

## Einrichten — mit einem eigenen Schlüssel

1. Auf [themoviedb.org](https://www.themoviedb.org/signup) ein kostenloses Konto
   anlegen und anmelden.
2. Oben rechts auf das Profilbild → **Einstellungen** → links **API**.
3. Einen API-Schlüssel anfordern (Typ „Developer", private Nutzung). Kopiert
   wird der **„API-Schlüssel"** (32 Zeichen), nicht das lange Lesezugriffstoken.
4. In der App unter **„Sendungen verwalten"** → **„Streaming-Starts (TMDB)"**
   einfügen und **„Schlüssel speichern"** klicken.

Die App probiert den Schlüssel vor dem Speichern aus. Passt er nicht, steht dort
sofort eine Meldung. Klappt es, startet ein neuer Datenabruf; nach 1–2 Minuten
erscheinen die ersten TMDB-Termine.

## Was du erwarten kannst

- Termine von TMDB sind mit **„laut TMDB"** markiert. Die Daten pflegt die
  TMDB-Gemeinschaft: **ein Tag Abweichung kommt vor**, eine Uhrzeit gibt es nicht.
- Die Senderangabe bei TMDB ist manchmal veraltet. Nennt TMDB keinen
  Streamingdienst, steht als Sender schlicht „TMDB", die Beschreibung nennt dann
  die Sender laut TMDB.
- Steht eine Sendung am selben Tag (±1) schon im Fernsehprogramm oder bei RTL+,
  zeigt die App nur diesen Termin — mit Uhrzeit und Sender — und nicht noch
  einmal den von TMDB.
- Gesucht werden die Namen und alternativen Schreibweisen aus deiner Liste,
  **nur unter deutschen Produktionen** (sonst landet „Love Island" bei der
  tschechischen Fassung). Findet TMDB zu einem Namen nichts, fehlt diese Sendung
  einfach.
- Der Schlüssel liegt in `config/tmdb.json` und ist **nicht** Teil der Sicherung
  — die darf man ja gefahrlos weitergeben. Auf einem neuen Rechner also einmal
  neu eintragen.
- Entfernen: im selben Abschnitt **„Schlüssel entfernen"**. Danach verschwinden
  die TMDB-Termine mit dem nächsten Datenabruf.

---

# Sendungsliste sichern

Deine Sendungsauswahl ist das Einzige am ganzen Tool, was Handarbeit ist —
alles andere holt sich das Programm selbst wieder. Die Sendetermine sind
deshalb **nicht** Teil der Sicherung; die holt der nächste Datenabruf ohnehin
neu.

## So geht's

1. Oben auf der Übersicht auf **„Sendungen verwalten →"**.
2. Falls du gerade etwas geändert hast: erst auf **„Speichern"**. Gesichert
   wird immer der *gespeicherte* Stand.
3. Ganz nach unten scrollen zum Abschnitt **„Sicherung"**.
4. Auf **„Sicherung erstellen"** klicken.

Der Browser lädt eine Datei namens `reality-tv-programm-2026-09-28.json`
herunter — normalerweise in deinen Ordner *Downloads*. Das ist die komplette
Sicherung, mehr braucht es nicht. Sie enthält auch die Titel, die du unter
„Neu entdeckt" ausgeblendet hast. Sie enthält keine Zugangsdaten und lässt
sich gefahrlos weitergeben.

**Wann sichern?** Immer dann, wenn du deine Sendungsliste spürbar geändert
hast. Für ein Update brauchst du **keine** Sicherung: Die Liste ist bewusst
kein Teil des heruntergeladenen Programmcodes, eine Auffrischung kann sie
strukturell nicht überschreiben. Vor dem **Löschen des Projektordners** ist
eine Sicherung aber Pflicht — sonst ist die Liste weg.

# Sicherung einspielen

Damit holst du deine Sendungsliste zurück — auf denselben Rechner nach einem
Missgeschick oder auf einen neuen.

1. Oben auf der Übersicht auf **„Sendungen verwalten →"**.
2. Ganz nach unten zum Abschnitt **„Sicherung einspielen"**.
3. Auf **„Datei auswählen"** klicken und deine
   `reality-tv-programm-….json` heraussuchen. Sie darf überall liegen:
   *Downloads*, USB-Stick, Netzlaufwerk — es öffnet sich der normale
   Dateidialog deines Systems.
4. Auf **„Sicherung einspielen"** klicken und die Rückfrage bestätigen.

Oben erscheint eine Meldung, was übernommen wurde, und die Programmdaten
werden automatisch neu geholt (1–2 Minuten), damit die Übersicht zur
eingespielten Liste passt.

## Das Sicherheitsnetz

Bevor etwas ersetzt wird, legt das Tool deine **bisherige** Liste automatisch
als `config/vor-wiederherstellung-<Zeit>.json` ab — in demselben Format. Hast
du also die falsche Datei erwischt, kannst du diese Kopie genauso wieder
einspielen und bist zurück, wo du warst. Die letzten zehn dieser Kopien
bleiben liegen.

Eine Datei, die gar keine Reality-TV-Sicherung ist oder aus einer **neueren**
Programmversion stammt, wird abgelehnt — deine Liste bleibt dann unberührt.
Das gilt auch für eine Sicherung des Schwesterprojekts Streaming-Info: Die
beiden Formate werden auseinandergehalten.

## Umzug auf einen neuen Rechner

1. Auf dem alten Rechner eine Sicherung erstellen.
2. Die Datei auf einen USB-Stick kopieren (oder ins Netzlaufwerk, per Mail an
   dich selbst, wie du magst).
3. Auf dem neuen Rechner [installieren](#installieren).
4. Die Startseite weist dort von sich aus darauf hin, dass sich eine Sicherung
   einspielen lässt — dem Link folgen und die Datei einspielen.

Die Datei liegt übrigens weiterhin auch direkt im Projektordner unter
`config/reality_shows.json`; wer möchte, kann sie genauso gut von Hand
kopieren.

---

# Wenn etwas nicht klappt

## Eine Streaming-Sendung fehlt

- Steht sie in der Sendungsliste? Der Name muss so geschrieben sein, wie RTL+ ihn
  führt, oder als Alias eingetragen sein (z. B. „Couple Challenge" und
  „CoupleChallenge").
- Nennt die Programmseite auf plus.rtl.de schon einen Starttermin? Davor gibt es
  hier nichts zu zeigen. Die Übersicht erfindet keine Termine.
- Liegt der Termin mehr als zwei Wochen voraus, erscheint er erst, wenn er in den
  Anzeigezeitraum rückt.
- In `logs/scraper.log` steht unter `plus.rtl.de`, welche Seiten gefunden wurden
  und wie viele Termine sie ergaben.
- Läuft sie bei Joyn, Prime Video oder Netflix, braucht es den
  [TMDB-Schlüssel](#streaming-starts-tmdb). Welcher Name bei TMDB welcher Serie
  zugeordnet wurde, steht in `data/tmdb_zuordnung.json` (`null` = nichts
  gefunden). Hilft ein anderer Name, ihn als alternative Schreibweise eintragen.

## „themoviedb.org: Schlüssel ungültig"

Der eingetragene TMDB-Schlüssel wird nicht (mehr) angenommen.

1. Auf themoviedb.org unter **Einstellungen → API** nachsehen, ob der Schlüssel
   noch existiert.
2. In der App unter **„Sendungen verwalten" → „Streaming-Starts (TMDB)"** neu
   eintragen.

Alles andere läuft unterdessen weiter, die zuletzt geholten TMDB-Termine bleiben
stehen.

## Die Übersicht bleibt leer

- **Läuft gerade noch der Datenabruf?** Er dauert 1–2 Minuten; die Seite
  zeigt das oben an und lädt sich von selbst neu.
- **Sind überhaupt Sendungen ausgewählt?** Siehe
  [Sendungen verwalten](#sendungen-verwalten).
- **Steht oben ein Fehler bei einer Quelle?** Dann kam dieser Abruf nicht
  durch. Die zuletzt erfolgreich geholten Daten bleiben erhalten; ein Klick
  auf „Jetzt aktualisieren" versucht es erneut. Einzelheiten stehen in
  `logs/scraper.log`.

## Der Browser zeigt „Verbindung fehlgeschlagen"

Dann ist die App nicht gestartet. Schau ins Protokoll — dort steht der Grund
im Klartext:

- **Windows:** `%USERPROFILE%\reality-tv-programm\logs\webapp.log`
- **Linux:** `~/reality-tv-programm/logs/webapp.log`

Abstürze der App landen **nur** in dieser Datei. In `logs/start.log` steht
ergänzend, wie weit das Startskript gekommen ist.

## Linux: Es passiert nichts oder es fehlt etwas

Starte einmal **im Terminal** statt per Doppelklick:

```bash
~/reality-tv-programm/start.sh
```

Nur dort siehst du alle Meldungen, und nur dort kann die Passwortabfrage
erscheinen, falls noch ein Paket nachinstalliert werden muss.

## Windows: „Python wurde nicht gefunden … Microsoft Store …"

Windows legt standardmäßig einen `python`-Platzhalter an, der nur auf den
Microsoft Store verweist, aber kein echtes Python ist. `start.bat` erkennt das
inzwischen und installiert automatisch per `winget`. Kommt die Meldung
trotzdem: Python von [python.org](https://www.python.org/downloads/) von Hand
installieren (dabei **„Add python.exe to PATH" anhaken**) und `start.bat` in
einem neuen Fenster erneut starten.

## „Versionsprüfung fehlgeschlagen"

Meist ein TLS-Problem auf älteren Windows-Installationen — wird inzwischen
automatisch umgangen. Bleibt die Meldung: prüfen, ob
`raw.githubusercontent.com` erreichbar ist (Internetverbindung, Firewall,
Proxy).

## Ein Klick auf die Verknüpfung bewirkt gar nichts

Kein Browser, kein neuer Eintrag in `logs/start.log`? Das betrifft
Installationen **vor v1.4.6**: Dort hielt die laufende App die Logdatei offen,
wodurch jeder weitere Start sofort abbrach. Abhilfe: die App über **„Beenden"**
schließen (oder den Rechner neu starten) und die Verknüpfung erneut anklicken.
Damit wird auf die aktuelle Version aufgefrischt, und danach tritt es nicht
mehr auf.

## Die angezeigte Version bleibt auf altem Stand

Bis v1.4.2 löste nur eine geänderte `start.bat` eine Auffrischung aus;
Releases, die nur den übrigen Code änderten, kamen nicht an. Seit v1.4.8
entscheidet die Versionsnummer.

Als Notlösung hilft immer: die aktuelle
[start.bat](https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.bat)
bzw. [start.sh](https://github.com/CrazyJimPro/reality-tv-programm/raw/main/start.sh)
herunterladen, den installierten Ordner löschen und die Datei erneut
ausführen. **Vorher unbedingt `config/reality_shows.json` wegkopieren** —
sonst ist deine Sendungsliste weg (siehe
[Sendungsliste sichern](#sendungsliste-sichern)).

---

# Technisches

## Wo liegt was?

Alles unterhalb von `%USERPROFILE%\reality-tv-programm` bzw.
`~/reality-tv-programm`:

| Pfad | Inhalt |
|---|---|
| `config/reality_shows.json` | deine persönliche Sendungsliste (bleibt bei Updates erhalten) |
| `config/vor-wiederherstellung-*.json` | der Stand vor dem letzten Einspielen einer Sicherung (die letzten zehn) |
| `data/programm.db` | die geholten Sendetermine |
| `data/rtlplus_katalog.json` | Zwischenspeicher der RTL+-Suche (darf gelöscht werden) |
| `data/folgen_cache.json` | Zwischenspeicher der Folgenangaben (darf gelöscht werden) |
| `config/tmdb.json` | dein TMDB-Schlüssel (nicht in der Sicherung) |
| `data/tmdb_zuordnung.json` | welcher Listenname zu welcher TMDB-Serie gehört (darf gelöscht werden) |
| `logs/start.log` | Meldungen des Startskripts |
| `logs/webapp.log` | Meldungen der Web-App — **hier stehen Abstürze** |
| `logs/scraper.log` | Protokoll der Datenabrufe |
| `VERSION` | installierte Versionsnummer |

## Was das Startskript automatisch erledigt

- lädt beim allerersten Mal den Rest des Projekts von GitHub nach
- prüft, ob Python vorhanden ist — falls nicht, installiert es nach
  (Windows: `winget`, Linux: `apt-get`, dort mit `sudo`)
- legt eine virtuelle Umgebung an und installiert die Abhängigkeiten
- entfernt eine früher angelegte automatische Aufgabe bzw. den früheren
  Cron-Eintrag (siehe unten)
- legt die Desktop-Verknüpfung an, falls noch keine da ist; der Desktop-Ordner
  wird beim System erfragt, damit sie auch bei einem nach OneDrive
  umgeleiteten Desktop sichtbar landet
- startet die Web-App ohne Fenster und öffnet den Browser, sobald sie
  antwortet

*(Wer lieber das ganze Repository klont oder als ZIP lädt, kann das tun —
`start.bat`/`start.sh` erkennen dann, dass der Rest schon da ist, und
überspringen den Download.)*

## Updates

Bei jedem Start wird die Datei `VERSION` mit der auf GitHub verglichen. Ist
die dort **wirklich neuer**, wird der komplette Code aufgefrischt und die App
neu gestartet. `config/reality_shows.json` ist davon nicht betroffen: Die
Datei ist bewusst nicht im Repository verfolgt, sondern wird beim ersten Mal
aus `config/reality_shows.default.json` erzeugt — eine Auffrischung kann sie
deshalb gar nicht überschreiben.

## Woher die Daten kommen

- `scraper/sources/rtl.py` — RTL + VOX direkt von rtl.de (nur ~6–7 Tage
  Vorschau)
- `scraper/sources/tvspielfilm.py` — Aggregator, deckt alle 14 Sender bis
  zu 14 Tage ab. Sat.1/ProSieben laufen inzwischen über Joyn, das selbst keine
  brauchbare mehrtägige Programmübersicht mehr bietet; die übrigen Sender haben
  gar keine eigene Quelle — für alle außer RTL und VOX ist das hier die einzige.
  Je drei Sender werden gleichzeitig abgefragt, damit der Abruf trotz der
  vielen Sender bei 1–2 Minuten bleibt. Ein weiterer Sender ist ein Eintrag in
  `SENDER_SLUGS` (Kennung aus der Adresse seiner Programmseite auf
  tvspielfilm.de) plus eine Farbe `.sender-<name>` in `webapp/static/style.css`
- `scraper/sources/rtlplus.py` — Streaming-Start auf plus.rtl.de für Sendungen,
  die in keinem Fernsehprogramm stehen. Sucht die Namen aus deiner Liste in der
  öffentlichen Sitemap von RTL+ (Zwischenspeicher `data/rtlplus_katalog.json`,
  höchstens einmal pro Woche neu gelesen), liest je Sendung die Programmseite
  und übernimmt nur Termine, die dort ausdrücklich stehen: die Folgentabelle
  (Temptation Island VIP) oder Angaben wie „Staffel 7 ab 12. Oktober". Hörbücher
  und Podcasts mit gleichem Namen werden ausgesondert
- Folgenangaben: `tvspielfilm.folgen_ergaenzen()` liest für jede **gefundene**
  Sendung (nicht fürs ganze Programm) die Detailseite und übernimmt Staffel/Folge
  und Folgentitel; Zwischenspeicher `data/folgen_cache.json`, Einträge fallen
  sieben Tage nach der Ausstrahlung heraus. Daraus erkennt `scraper/folgen.py`
  Wiederholungen und bildet den Schlüssel für das Gesehen-Häkchen (Tabelle
  `gesehen`)
- `scraper/sources/tmdb.py` — Streaming- und Staffelstarts über die TMDB-API
  (nur mit Schlüssel). Je Name/Alias der Liste die beste deutschsprachige Serie
  (`search/tv`, gleicher Name vor Bekanntheit; Zuordnung 30 Tage
  zwischengespeichert), dann `tv/{id}` und die Folgen der laufenden Staffel.
  Termine im Zeitraum, die schon als Fernseh-/RTL+-Termin dastehen (±1 Tag),
  sortiert `scraper/run.py` aus; spätere Folge-1-Termine landen in der Tabelle
  `demnaechst`; `discover/tv` (Genre Reality, deutsch, Netzwerke Joyn 3155,
  RTL+ 5428, Prime Video 1024, Netflix 213) liefert Vorschläge für „Neu
  entdeckt". Joyn und Prime Video direkt wurden geprüft und verworfen: Joyn
  führt nur bereits verfügbare Folgen, Amazon sperrt seine Schnittstelle in der
  robots.txt
- `scraper/merge.py` — führt Duplikate aus den Quellen zusammen
- `scraper/filter.py` — Abgleich gegen `config/reality_shows.json`
- `scraper/storage.py` — SQLite (`data/programm.db`)

Jede Quelle scheitert **isoliert**: Schlägt eine fehl, bleiben die zuletzt
erfolgreich gespeicherten Daten unangetastet. Sichtbar wird das an der
Status-Anzeige oben in der Web-App und in `logs/scraper.log`.

Das Abzeichen „Staffel X · Folge Y" neben einem Titel wird per Regex aus dem
vorhandenen Beschreibungstext gezogen — keine zusätzliche Quelle, nur
vorhandene Daten sichtbarer gemacht. Diese Angabe liefert derzeit **nur
rtl.de**, also nur für RTL und VOX.

## Aufbau der Web-App

Flask, erreichbar unter **Port 5000**:

- `/` — Programmübersicht, liest ausschließlich aus der Datenbank
- `/einstellungen` — verwaltet `config/reality_shows.json`; die Vorschläge
  kommen aus `webapp/vorschlaege.py`
- `/aktualisieren` (POST) — stößt `scraper/run.py` als Hintergrundprozess an
  (Knopf „Jetzt aktualisieren"; läuft auch beim Speichern der Sendungsliste
  und einmal beim Start der App)
- `/scrape-status` (JSON) — meldet, ob ein Lauf noch läuft; damit lädt sich
  die Übersicht selbst neu, sobald er fertig ist
- `/tmdb-schluessel` (POST) — TMDB-Schlüssel speichern (vorher geprüft), aus
  Streaming-Info übernehmen oder entfernen
- `/gesehen` (POST, JSON) — Gesehen-Häkchen setzen/entfernen; die Schalter
  über der Übersicht steuert `webapp/static/uebersicht.js` (Stand im
  localStorage des Browsers)
- `/entdeckung/hinzufuegen`, `/entdeckung/ausblenden`, `/entdeckung/einblenden`
  (POST) — Kasten „Neu entdeckt". Die Kandidaten berechnet
  `scraper/entdecken.py` bei jedem Lauf aus dem ungefilterten Programm und legt
  sie samt Terminen in der Tabelle `entdeckungen` ab; abgeglichen mit der
  Sendungsliste wird erst beim Anzeigen. „Hinzufügen" kopiert die Termine von
  dort direkt in die Übersicht. Ausgeblendete Titel stehen unter
  `"ausgeblendet"` in `config/reality_shows.json`
- `/beenden` (POST) — beendet die App vollständig

`start_versteckt.bat` / `start_versteckt.vbs` (nur Windows) sind das Ziel der
Desktop-Verknüpfung: Sie rufen `start.bat` ohne sichtbares Konsolenfenster auf
und leiten alle Meldungen nach `logs/start.log` um. Unter Linux genügt dafür
`Terminal=false` in der `.desktop`-Datei.

## Frühere Hintergrund-Automatisierung

Bis Version 1.3.0 hat sich das Tool per Windows-Aufgabenplanung bzw. Cronjob
zweimal wöchentlich (Mo + Do, 06:00 Uhr) selbst aktualisiert. Das gibt es
nicht mehr — aktualisiert wird bei jedem Start. `start.bat`/`start.sh`
**entfernen einen noch vorhandenen Alt-Eintrag automatisch** beim nächsten
Lauf. Von Hand ginge es so:

Windows:
```powershell
schtasks /Delete /TN RealityTV_Scraper /F
```

Linux:
```bash
crontab -l | grep -v '# RealityTV_Scraper' | crontab -
```

## Wichtige Hinweise

- **Rechtlich:** Automatisiertes Abrufen von rtl.de, tvspielfilm.de und plus.rtl.de kann
  gegen deren Nutzungsbedingungen verstoßen, auch bei rein privatem Gebrauch.
  Das ist ein bewusst eingegangenes Risiko — keine Rechtsberatung. Abgerufen
  wird nur beim Start der App und auf Knopfdruck, das hält die Serverlast
  gering.
- **Wartung:** Ändern die Seiten ihr Layout, muss der jeweilige Scraper in
  `scraper/sources/` angepasst werden (die Selektoren stehen zentral an einer
  Stelle pro Datei).
- Alles wird ausschließlich lokal gespeichert, nichts an Dritte gesendet.
