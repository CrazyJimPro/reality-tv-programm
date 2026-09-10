#!/usr/bin/env bash
# Einzige Datei, die man ausfuehren muss: installiert/richtet alles automatisch
# ein (Python-Check, venv, Abhaengigkeiten, Cronjob, erster Datenabruf) und
# startet danach die Web-App. Bei jedem weiteren Aufruf werden bereits
# erledigte Schritte uebersprungen.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
SELBST="$(pwd)/$(basename "${BASH_SOURCE[0]}")"

# Alles, was ab hier ausgegeben wird, landet zusaetzlich in logs/start.log -
# wichtig, wenn per Desktop-Verknuepfung ohne sichtbares Terminal gestartet
# wird (dann gibt es sonst gar keine Rueckmeldung mehr bei einem Fehler).
mkdir -p logs
exec > >(tee logs/start.log) 2>&1

echo "=== Reality-TV Programmuebersicht ==="
echo

ZIEL_ORDNER="$HOME/reality-tv-programm"

# Laedt eine Datei aus dem Repository nach $2 (leise, curl oder wget).
hole_datei() {
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL -o "$2" "https://raw.githubusercontent.com/CrazyJimPro/reality-tv-programm/main/$1" 2>/dev/null
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "$2" "https://raw.githubusercontent.com/CrazyJimPro/reality-tv-programm/main/$1" 2>/dev/null
    fi
}

# Beendet eine noch laufende Instanz - erst hoeflich ueber /beenden, danach
# notfalls hart. Versionen vor v1.4.0 kennen /beenden noch nicht.
alte_instanz_beenden() {
    curl -s -o /dev/null --connect-timeout 1 http://127.0.0.1:5000/ 2>/dev/null || return 0
    echo "Beende die noch laufende Version (sonst liefe der alte Code weiter)..."
    curl -s -o /dev/null -X POST --max-time 10 http://127.0.0.1:5000/beenden 2>/dev/null || true
    for _ in $(seq 1 10); do
        curl -s -o /dev/null --connect-timeout 1 http://127.0.0.1:5000/ 2>/dev/null || return 0
        sleep 1
    done
    pkill -f "webapp/app.py" 2>/dev/null || true
    sleep 1
}

# --- -1. Pruefen, ob auf GitHub eine neuere Version liegt. Verglichen wird
# die Versionsnummer aus der Datei VERSION - und aufgefrischt wird nur, wenn
# die dort WIRKLICH neuer ist.
#
# Frueher wurde stattdessen start.sh byteweise mit der Fassung auf GitHub
# verglichen. Das hatte zwei Nachteile: Aenderungen am uebrigen Code fielen
# gar nicht auf, und da raw.githubusercontent.com fuenf Minuten
# zwischenspeichert (einzelne Server liefern auch laenger alte Staende aus),
# schlug der Vergleich staendig an und frischte bei jedem Start alles auf -
# samt der unsinnigen Meldung "neu: 1.4.4, installiert: 1.4.5". Wird
# aufgefrischt, kommen alle Dateien ohnehin in ihrer neuen Fassung mit. ---
NEUERE_VERSION_GEFUNDEN=""

# Rechnet "1.4.7" in eine vergleichbare Zahl um; leer, wenn die Angabe nicht
# dem Muster Zahl.Zahl.Zahl entspricht.
version_zu_zahl() {
    case "$1" in
        ''|*[!0-9.]*) return 1 ;;
    esac
    _rest="${1#*.}"
    _a="${1%%.*}"; _b="${_rest%%.*}"; _c="${_rest#*.}"
    case "$_c" in ''|*[!0-9]*) return 1 ;; esac
    case "$_b" in ''|*[!0-9]*) return 1 ;; esac
    case "$_a" in ''|*[!0-9]*) return 1 ;; esac
    echo $(( _a * 1000000 + _b * 1000 + _c ))
}

TMP_VER="$(mktemp)"
# Der angehaengte Zufallswert umgeht den Zwischenspeicher von GitHub.
hole_datei "VERSION?nocache=$$$(date +%s)" "$TMP_VER"
if [ -s "$TMP_VER" ]; then
    VERSION_NEU="$(tr -d '\r' < "$TMP_VER" | head -1)"
    if [ -f VERSION ]; then
        VERSION_LOKAL="$(tr -d '\r' < VERSION | head -1)"
        ZAHL_NEU="$(version_zu_zahl "$VERSION_NEU" || true)"
        ZAHL_LOKAL="$(version_zu_zahl "$VERSION_LOKAL" || true)"
        if [ -n "$ZAHL_NEU" ] && [ -n "$ZAHL_LOKAL" ] && [ "$ZAHL_NEU" -gt "$ZAHL_LOKAL" ]; then
            echo "Neue Version verfuegbar: $VERSION_NEU (installiert: $VERSION_LOKAL)"
            NEUERE_VERSION_GEFUNDEN=1
        fi
    elif [ -f requirements.txt ]; then
        # Installation vor v1.4.1: noch gar keine VERSION-Datei vorhanden.
        echo "Installierte Fassung ohne Versionsangabe - frische auf $VERSION_NEU auf."
        NEUERE_VERSION_GEFUNDEN=1
    fi
else
    echo "Versionspruefung fehlgeschlagen (kein Internet oder Netzwerk blockiert) - fahre mit der vorhandenen Version fort."
fi
rm -f "$TMP_VER"

# --- 0. Projektordner bestimmen und bei Bedarf (neu) laden: entweder weil
# hier noch gar kein komplettes Projekt liegt (nur diese eine Datei wurde
# heruntergeladen), oder weil Schritt -1 eine neuere Version gefunden hat.
# In beiden Faellen wird der KOMPLETTE Code von GitHub aufgefrischt (nicht
# nur start.sh), venv/data/logs bleiben dabei unberuehrt (die liegen nicht
# im heruntergeladenen Quellcode). ---
# WICHTIG: Laeuft dieses Skript AUS dem Ordner, der aufgefrischt wird, darf
# es sich dabei nicht selbst ueberschreiben - die Shell liest ein Skript
# waehrend der Ausfuehrung weiter von der Platte (an der zuletzt erreichten
# Byte-Position). Wird es unter den Fuessen ausgetauscht, laeuft danach ein
# wilder Mix aus alter und neuer Datei. Deshalb wird start.sh in diesem Fall
# ausgelassen, die neue Fassung nach /tmp gelegt und von dort neu gestartet -
# die frischt den Ordner dann komplett auf (dann laeuft ja keine Datei mehr
# aus dem Zielordner).
if [ -f "requirements.txt" ]; then
    PROJEKT_ZIEL="$(pwd)"
    EIGENER_ORDNER=1
else
    PROJEKT_ZIEL="$ZIEL_ORDNER"
    EIGENER_ORDNER=""
fi

MUSS_LADEN=""
[ -f "requirements.txt" ] || MUSS_LADEN=1
[ -n "$NEUERE_VERSION_GEFUNDEN" ] && MUSS_LADEN=1

if [ -n "$MUSS_LADEN" ]; then
    echo "Lade aktuellen Projektstand von GitHub (Code + Web-App werden aufgefrischt)..."
    TMP_TAR="$(mktemp)"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL -o "$TMP_TAR" "https://github.com/CrazyJimPro/reality-tv-programm/archive/refs/heads/main.tar.gz"
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "$TMP_TAR" "https://github.com/CrazyJimPro/reality-tv-programm/archive/refs/heads/main.tar.gz"
    else
        echo "Fehler: weder curl noch wget gefunden."
        echo "Bitte eines davon installieren oder das Repo manuell laden:"
        echo "https://github.com/CrazyJimPro/reality-tv-programm"
        exit 1
    fi
    if [ ! -s "$TMP_TAR" ]; then
        echo "Fehler beim Herunterladen. Bitte Internetverbindung pruefen,"
        echo "oder das Repo manuell laden: https://github.com/CrazyJimPro/reality-tv-programm"
        rm -f "$TMP_TAR"
        exit 1
    fi
    mkdir -p "$PROJEKT_ZIEL"
    TMP_DIR="$(mktemp -d)"
    tar -xzf "$TMP_TAR" -C "$TMP_DIR" --strip-components=1
    rm -f "$TMP_TAR"
    if [ -n "$EIGENER_ORDNER" ]; then
        NEUSTART_DATEI="$(mktemp /tmp/rtv_start_neu.XXXXXX.sh)"
        cp "$TMP_DIR/start.sh" "$NEUSTART_DATEI"
        chmod +x "$NEUSTART_DATEI"
        rm -f "$TMP_DIR/start.sh"
    else
        NEUSTART_DATEI="$PROJEKT_ZIEL/start.sh"
    fi
    cp -r "$TMP_DIR/." "$PROJEKT_ZIEL/"
    rm -rf "$TMP_DIR"
    # Ausfuehrbar-Recht sicherstellen: aus einem heruntergeladenen Archiv kann
    # es fehlen, und dann startet die Desktop-Verknuepfung nicht mehr.
    chmod +x "$PROJEKT_ZIEL/start.sh" 2>/dev/null || true

    if [ "$(pwd)" != "$PROJEKT_ZIEL" ]; then
        echo "Projekt liegt jetzt unter: $PROJEKT_ZIEL"
    else
        echo "Projekt aufgefrischt."
    fi
    # Eine noch laufende Instanz haelt den ALTEN Code im Speicher - die frisch
    # heruntergeladenen Dateien wuerden erst beim naechsten Start wirksam.
    alte_instanz_beenden

    echo "Starte neu ..."
    echo
    chmod +x "$NEUSTART_DATEI"
    exec "$NEUSTART_DATEI" "$@"
fi

# --- 0.5 Welcher Stand laeuft hier? Steht auch in logs/start.log und oben
# in der Kopfzeile der Web-App. ---
if [ -f VERSION ]; then
    echo "Version: $(cat VERSION)"
    echo
fi

# --- 1. Python3 vorhanden? Sonst automatisch per apt installieren ---
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 wurde nicht gefunden. Versuche automatische Installation..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y python3 python3-venv python3-pip cron
    else
        echo "Fehler: kein unterstuetzter Paketmanager (apt-get) gefunden."
        echo "Bitte Python 3 manuell installieren und dieses Skript erneut starten."
        exit 1
    fi
fi

# venv-Modul ist auf manchen Distros ein separates Paket
if ! python3 -m venv --help >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installiere python3-venv nach..."
        sudo apt-get update -qq && sudo apt-get install -y python3-venv
    fi
fi

# --- 2. Virtuelle Umgebung + Abhaengigkeiten, falls noch nicht vorhanden ---
if [ ! -x "venv/bin/python" ]; then
    echo "Richte virtuelle Umgebung ein (einmalig, dauert etwas)..."
    python3 -m venv venv || { echo "Fehler beim Anlegen der virtuellen Umgebung."; exit 1; }
    ./venv/bin/pip install --quiet --upgrade pip || { echo "Fehler beim pip-Upgrade."; exit 1; }
    ./venv/bin/pip install --quiet -r requirements.txt || { echo "Fehler beim Installieren der Abhaengigkeiten."; exit 1; }
fi

PROJEKT_PFAD="$(pwd)"
VENV_PYTHON="$PROJEKT_PFAD/venv/bin/python"

# --- 3. Frueher angelegten Cron-Eintrag wieder entfernen. Die Daten werden
# jetzt bei jedem Start der App geholt (die Web-App stoesst den Scrape-Lauf
# beim Hochfahren selbst an) - es soll nichts mehr im Hintergrund laufen,
# wenn die App beendet ist. Bei aelteren Installationen steht der Eintrag
# noch in der Crontab. ---
MARKER="# RealityTV_Scraper"
if crontab -l 2>/dev/null | grep -q "$MARKER"; then
    echo "Entferne den frueheren Cron-Eintrag (wird nicht mehr gebraucht)..."
    # grep liefert 1, wenn nach dem Filtern nichts uebrig bleibt - ohne
    # "|| true" wuerde die Pipeline dann eine leere Crontab verhindern.
    ( crontab -l 2>/dev/null | grep -v "$MARKER" || true ) | crontab -
fi

# --- 4.5 Desktop-Verknuepfung anlegen, falls noch nicht vorhanden - startet
# kuenftig per Doppelklick ohne sichtbares Terminal (Terminal=false), alle
# Meldungen landen trotzdem in logs/start.log (siehe oben). ---
DESKTOP_ORDNER="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
DESKTOP_DATEI="$DESKTOP_ORDNER/reality-tv-programm.desktop"
if [ -d "$DESKTOP_ORDNER" ] && [ ! -f "$DESKTOP_DATEI" ]; then
    echo "Richte Desktop-Verknuepfung ein..."
    cat > "$DESKTOP_DATEI" <<EOF
[Desktop Entry]
Type=Application
Name=Reality-TV Programm
Comment=Reality-TV Programmuebersicht starten
Exec=$PROJEKT_PFAD/start.sh
Path=$PROJEKT_PFAD
Terminal=false
Icon=video-television
EOF
    chmod +x "$DESKTOP_DATEI"
    # Manche Dateimanager (z.B. GNOME Files) verlangen beim ersten Start
    # zusaetzlich eine "Vertrauen"-Markierung, sonst kommt eine Rueckfrage.
    gio set "$DESKTOP_DATEI" metadata::trusted true 2>/dev/null || true
fi

# --- 5. Web-App starten und Browser oeffnen (nur falls nicht schon eine
# laeuft - sonst Port-Konflikt, z.B. bei erneutem Klick auf die
# Desktop-Verknuepfung waehrend die App schon offen ist) ---
if curl -s -o /dev/null --connect-timeout 1 http://127.0.0.1:5000/ 2>/dev/null; then
    echo "Web-App laeuft bereits - stosse Aktualisierung an und oeffne Browser ..."
    # Auch beim Klick auf die Verknuepfung waehrend die App schon laeuft
    # sollen frische Daten geholt werden. Der Aufruf kommt sofort zurueck,
    # der Lauf selbst passiert im Hintergrund der App.
    curl -s -o /dev/null -X POST --max-time 10 http://127.0.0.1:5000/aktualisieren || true
    xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 || true
    exit 0
fi

echo
echo "Oeffne http://127.0.0.1:5000 im Browser ..."
echo "Die Programmdaten werden dabei im Hintergrund frisch geholt (1-2 Minuten),"
echo "die Seite aktualisiert sich von selbst, sobald der Lauf fertig ist."
echo "Die App laeuft im Hintergrund weiter, dieses Terminal wird nicht belegt."
echo "Zum Beenden den Knopf \"Beenden\" oben auf der Seite benutzen - danach"
echo "laeuft nichts mehr im Hintergrund."
echo
# Die App laeuft im Hintergrund weiter, damit dieses Terminal nicht belegt
# bleibt (per Desktop-Verknuepfung gibt es ohnehin keins). Ihre Meldungen
# schreibt sie nach logs/webapp.log. Der Browser wird erst geoeffnet, wenn
# Port 5000 wirklich antwortet - sonst zeigt er kurz eine Fehlerseite.
nohup "$VENV_PYTHON" webapp/app.py >> logs/webapp.log 2>&1 &
for _ in $(seq 1 20); do
    if curl -s -o /dev/null --connect-timeout 1 http://127.0.0.1:5000/ 2>/dev/null; then break; fi
    sleep 1
done
xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 || true
