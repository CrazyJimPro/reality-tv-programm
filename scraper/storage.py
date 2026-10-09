"""SQLite-Speicherung der gemergten Programmdaten und des Quellen-Status."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

from scraper.merge import MergedEintrag

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
DB_PFAD = PROJEKT_ROOT / "data" / "programm.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS programme (
    sender TEXT NOT NULL,
    datum TEXT NOT NULL,
    uhrzeit TEXT NOT NULL,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    genre TEXT,
    quellen TEXT NOT NULL,
    konfidenz TEXT NOT NULL,
    aktualisiert_am TEXT NOT NULL,
    PRIMARY KEY (sender, datum, uhrzeit, titel)
);

-- Kandidaten fuer den Kasten "Neu entdeckt" (scraper/entdecken.py): alle
-- Fernseh-Ausstrahlungen mit Reality-/Doku-Soap-Genre, unabhaengig von der
-- Sendungsliste. Wird bei jedem erfolgreichen Lauf komplett ersetzt.
CREATE TABLE IF NOT EXISTS entdeckungen (
    sender TEXT NOT NULL,
    datum TEXT NOT NULL,
    uhrzeit TEXT NOT NULL,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    genre TEXT,
    quellen TEXT NOT NULL,
    konfidenz TEXT NOT NULL,
    stufe TEXT NOT NULL,
    PRIMARY KEY (sender, datum, uhrzeit, titel)
);

CREATE TABLE IF NOT EXISTS quellen_status (
    quelle TEXT PRIMARY KEY,
    letzter_erfolg_am TEXT,
    letzter_fehler TEXT,
    letzter_fehler_am TEXT
);
"""


def _verbindung(db_pfad: Path = DB_PFAD) -> sqlite3.Connection:
    db_pfad.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_pfad)
    conn.row_factory = sqlite3.Row
    return conn


def _schluessel_migrieren(conn: sqlite3.Connection) -> None:
    """Aeltere Datenbanken kennen den Titel nicht im Primaerschluessel. Mit RTL+
    (mehrere Sendungen starten dort gleichzeitig um 0 Uhr) wuerde das zu
    Schluesselkollisionen fuehren. Die Tabelle wird deshalb einmalig mit dem
    neuen Schluessel neu angelegt; vorhandene Zeilen bleiben erhalten."""
    spalten = conn.execute("PRAGMA table_info(programme)").fetchall()
    schluessel = {row["name"] for row in spalten if row["pk"]}
    if not spalten or "titel" in schluessel:
        return
    conn.execute("ALTER TABLE programme RENAME TO programme_alt")
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR IGNORE INTO programme SELECT * FROM programme_alt")
    conn.execute("DROP TABLE programme_alt")


def init_db(db_pfad: Path = DB_PFAD) -> None:
    with closing(_verbindung(db_pfad)) as conn, conn:
        # Bestehende Tabelle zuerst umbauen, sonst legt SCHEMA (IF NOT EXISTS) nichts neu an.
        _schluessel_migrieren(conn)
        conn.executescript(SCHEMA)


def speichere_eintraege(
    eintraege: list[MergedEintrag],
    ab_datum: date,
    bis_datum: date,
    db_pfad: Path = DB_PFAD,
    behalte_sender: tuple[str, ...] = (),
) -> None:
    """Ersetzt alle gespeicherten Sendungen im Zeitraum [ab_datum, bis_datum]
    durch die frisch gemergten Eintraege. Wird nur aufgerufen, wenn der
    Scrape-Lauf ueberhaupt Daten geliefert hat (siehe run.py).

    behalte_sender: Sender, deren bisherige Zeilen NICHT geloescht werden -
    gebraucht, wenn deren Quelle in diesem Lauf ausgefallen ist (sonst wuerden
    ihre zuletzt guten Daten mit einem Fehlschlag verschwinden)."""
    jetzt = datetime.now().isoformat(timespec="seconds")
    with closing(_verbindung(db_pfad)) as conn, conn:
        loeschen = "DELETE FROM programme WHERE datum >= ? AND datum <= ?"
        parameter: list = [ab_datum.isoformat(), bis_datum.isoformat()]
        if behalte_sender:
            loeschen += f" AND sender NOT IN ({','.join('?' * len(behalte_sender))})"
            parameter.extend(behalte_sender)
        conn.execute(loeschen, parameter)
        conn.executemany(
            """
            INSERT OR REPLACE INTO programme (sender, datum, uhrzeit, titel, beschreibung, genre, quellen, konfidenz, aktualisiert_am)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    e.sender,
                    e.datum.isoformat(),
                    e.uhrzeit.strftime("%H:%M"),
                    e.titel,
                    e.beschreibung,
                    e.genre,
                    ",".join(e.quellen),
                    e.konfidenz,
                    jetzt,
                )
                for e in eintraege
            ],
        )


def markiere_quelle_erfolg(quelle: str, db_pfad: Path = DB_PFAD) -> None:
    jetzt = datetime.now().isoformat(timespec="seconds")
    with closing(_verbindung(db_pfad)) as conn, conn:
        conn.execute(
            """
            INSERT INTO quellen_status (quelle, letzter_erfolg_am, letzter_fehler, letzter_fehler_am)
            VALUES (?, ?, NULL, NULL)
            ON CONFLICT(quelle) DO UPDATE SET letzter_erfolg_am = excluded.letzter_erfolg_am
            """,
            (quelle, jetzt),
        )


def markiere_quelle_fehler(quelle: str, fehlertext: str, db_pfad: Path = DB_PFAD) -> None:
    jetzt = datetime.now().isoformat(timespec="seconds")
    with closing(_verbindung(db_pfad)) as conn, conn:
        conn.execute(
            """
            INSERT INTO quellen_status (quelle, letzter_erfolg_am, letzter_fehler, letzter_fehler_am)
            VALUES (?, NULL, ?, ?)
            ON CONFLICT(quelle) DO UPDATE SET letzter_fehler = excluded.letzter_fehler, letzter_fehler_am = excluded.letzter_fehler_am
            """,
            (quelle, fehlertext, jetzt),
        )


def hole_quellen_status(db_pfad: Path = DB_PFAD) -> list[dict]:
    with closing(_verbindung(db_pfad)) as conn:
        rows = conn.execute("SELECT * FROM quellen_status ORDER BY quelle").fetchall()
        return [dict(row) for row in rows]


def hole_programme(ab_datum: date, bis_datum: date, db_pfad: Path = DB_PFAD) -> list[dict]:
    with closing(_verbindung(db_pfad)) as conn:
        rows = conn.execute(
            """
            SELECT * FROM programme
            WHERE datum >= ? AND datum <= ?
            ORDER BY datum, uhrzeit, sender
            """,
            (ab_datum.isoformat(), bis_datum.isoformat()),
        ).fetchall()
        return [dict(row) for row in rows]


def speichere_entdeckungen(kandidaten: list[tuple[MergedEintrag, str]], db_pfad: Path = DB_PFAD) -> None:
    """Ersetzt alle gespeicherten Kandidaten durch die des aktuellen Laufs."""
    with closing(_verbindung(db_pfad)) as conn, conn:
        conn.execute("DELETE FROM entdeckungen")
        conn.executemany(
            """
            INSERT OR REPLACE INTO entdeckungen (sender, datum, uhrzeit, titel, beschreibung, genre, quellen, konfidenz, stufe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    e.sender,
                    e.datum.isoformat(),
                    e.uhrzeit.strftime("%H:%M"),
                    e.titel,
                    e.beschreibung,
                    e.genre,
                    ",".join(e.quellen),
                    e.konfidenz,
                    stufe,
                )
                for e, stufe in kandidaten
            ],
        )


def hole_entdeckungen(ab_datum: date, bis_datum: date, db_pfad: Path = DB_PFAD) -> list[dict]:
    with closing(_verbindung(db_pfad)) as conn:
        rows = conn.execute(
            "SELECT * FROM entdeckungen WHERE datum >= ? AND datum <= ? ORDER BY datum, uhrzeit, sender",
            (ab_datum.isoformat(), bis_datum.isoformat()),
        ).fetchall()
        return [dict(row) for row in rows]


def uebernehme_entdeckungen(rows: list[dict], db_pfad: Path = DB_PFAD) -> None:
    """Kopiert Kandidaten-Termine in die Uebersicht - damit eine aus "Neu
    entdeckt" hinzugefuegte Sendung sofort erscheint, ohne 1-2 Minuten auf
    einen neuen Datenabruf zu warten. Der naechste Lauf ersetzt sie ohnehin
    durch frische Daten (dann ueber den normalen Filter)."""
    jetzt = datetime.now().isoformat(timespec="seconds")
    with closing(_verbindung(db_pfad)) as conn, conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO programme (sender, datum, uhrzeit, titel, beschreibung, genre, quellen, konfidenz, aktualisiert_am)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (r["sender"], r["datum"], r["uhrzeit"], r["titel"], r["beschreibung"], r["genre"], r["quellen"], r["konfidenz"], jetzt)
                for r in rows
            ],
        )
