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
    PRIMARY KEY (sender, datum, uhrzeit)
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


def init_db(db_pfad: Path = DB_PFAD) -> None:
    with closing(_verbindung(db_pfad)) as conn, conn:
        conn.executescript(SCHEMA)


def speichere_eintraege(
    eintraege: list[MergedEintrag], ab_datum: date, bis_datum: date, db_pfad: Path = DB_PFAD
) -> None:
    """Ersetzt alle gespeicherten Sendungen im Zeitraum [ab_datum, bis_datum]
    durch die frisch gemergten Eintraege. Wird nur aufgerufen, wenn der
    Scrape-Lauf ueberhaupt Daten geliefert hat (siehe run.py)."""
    jetzt = datetime.now().isoformat(timespec="seconds")
    with closing(_verbindung(db_pfad)) as conn, conn:
        conn.execute(
            "DELETE FROM programme WHERE datum >= ? AND datum <= ?",
            (ab_datum.isoformat(), bis_datum.isoformat()),
        )
        conn.executemany(
            """
            INSERT INTO programme (sender, datum, uhrzeit, titel, beschreibung, genre, quellen, konfidenz, aktualisiert_am)
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
