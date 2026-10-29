"""simple sqlite3 unanswered (queries) logging database"""
import sqlite3
from pathlib import Path

DB_PATH = Path("logs/unanswered.db")  # not data/, that folder is your PDFs
DB_PATH.parent.mkdir(exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS unanswered (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asked_at TEXT NOT NULL,
            question TEXT NOT NULL,
            search_query TEXT,
            top_score REAL
        )"""
    )
    return conn


def log_unanswered(question, search_query, top_score):
    """Never raises: a logging failure must not break a student's chat."""
    try:
        conn = _connect()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO unanswered (asked_at, question, search_query, top_score) "
                    "VALUES (datetime('now'), ?, ?, ?)",
                    (question[:500], (search_query or "")[:500], top_score),
                )
        finally:
            conn.close()
    except Exception as e:
        print(f"Could not log unanswered question: {e}")