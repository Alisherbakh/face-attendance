"""SQLite bilan ishlash: davomat jadvali."""
import sqlite3
from datetime import datetime

from config import DB_PATH


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day TEXT NOT NULL,          -- 2026-10-30
            time TEXT NOT NULL,         -- 09:12:45
            distance REAL,              -- LBPH masofasi (kichik = ishonchli)
            UNIQUE(name, day)           -- bir kishi kuniga bir marta
        )"""
    )
    return conn


def mark_attendance(conn, name: str, distance: float) -> bool:
    """Davomat yozadi. Yangi yozuv bo'lsa True, bugun allaqachon bor bo'lsa False."""
    now = datetime.now()
    cur = conn.execute(
        "INSERT OR IGNORE INTO attendance (name, day, time, distance) VALUES (?, ?, ?, ?)",
        (name, now.date().isoformat(), now.strftime("%H:%M:%S"), round(float(distance), 1)),
    )
    conn.commit()
    return cur.rowcount == 1


def get_attendance(conn, day: str):
    rows = conn.execute(
        "SELECT name, day, time, distance FROM attendance WHERE day = ? ORDER BY time", (day,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_days(conn):
    rows = conn.execute(
        "SELECT day, COUNT(*) AS count FROM attendance GROUP BY day ORDER BY day DESC LIMIT 30"
    ).fetchall()
    return [dict(r) for r in rows]
