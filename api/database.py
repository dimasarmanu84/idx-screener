"""SQLite database for user accounts and portfolio holdings."""

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "data" / "idxscreener.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                name TEXT NOT NULL,
                picture TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                lot INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_holdings_user ON holdings(user_id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google ON users(google_id);
        """)
        conn.commit()
    finally:
        conn.close()


def get_or_create_user(google_id: str, email: str, name: str, picture: str) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE google_id = ?", (google_id,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET name=?, picture=?, email=? WHERE id=?",
                (name, picture, email, row["id"]),
            )
            conn.commit()
            user_id = row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO users (google_id, email, name, picture) VALUES (?, ?, ?, ?)",
                (google_id, email, name, picture),
            )
            conn.commit()
            user_id = cur.lastrowid

        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(user)
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_holdings(user_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT ticker, lot, avg_price FROM holdings WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_holdings(user_id: int, holdings: list) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
        for h in holdings:
            conn.execute(
                "INSERT INTO holdings (user_id, ticker, lot, avg_price) VALUES (?, ?, ?, ?)",
                (user_id, h["ticker"], h["lot"], h["avg_price"]),
            )
        conn.commit()
    finally:
        conn.close()
