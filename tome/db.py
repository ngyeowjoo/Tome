"""
modules/db.py — SQLite database layer for Tome Knowledge Base
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tome.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source_file TEXT NOT NULL,
            file_type TEXT,
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'published',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            chunk_index INTEGER DEFAULT 0,
            embedding_index INTEGER,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        );

        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'published',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            results_found INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            result_snippet TEXT,
            rating INTEGER NOT NULL,
            comment TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewed INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()


# ── Documents ──────────────────────────────────────────────────────────────────

def insert_document(title: str, source_file: str, file_type: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO documents (title, source_file, file_type) VALUES (?, ?, ?)",
        (title, source_file, file_type),
    )
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def get_all_documents():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM documents ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_document(doc_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()


# ── Chunks ─────────────────────────────────────────────────────────────────────

def insert_chunk(document_id: int, content: str, chunk_index: int, embedding_index: int):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chunks (document_id, content, chunk_index, embedding_index) VALUES (?, ?, ?, ?)",
        (document_id, content, chunk_index, embedding_index),
    )
    conn.commit()
    conn.close()


def get_chunks_by_ids(embedding_indices: list[int]) -> list[dict]:
    if not embedding_indices:
        return []
    conn = get_connection()
    placeholders = ",".join("?" * len(embedding_indices))
    rows = conn.execute(
        f"""SELECT c.id, c.content, c.embedding_index, d.title, d.source_file
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.embedding_index IN ({placeholders})""",
        embedding_indices,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_chunks() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.id, c.content, c.embedding_index, c.chunk_index, c.document_id, d.title
           FROM chunks c JOIN documents d ON c.document_id = d.id
           ORDER BY d.title, c.chunk_index"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_chunk_count() -> int:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    conn.close()
    return count


# ── FAQs ───────────────────────────────────────────────────────────────────────

def insert_faq(question: str, answer: str, category: str = "General"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)",
        (question, answer, category),
    )
    conn.commit()
    conn.close()


def get_all_faqs() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM faqs ORDER BY category, question").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_faq(faq_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    conn.commit()
    conn.close()


# ── Search logs ────────────────────────────────────────────────────────────────

def log_search(query: str, results_found: int):
    conn = get_connection()
    conn.execute(
        "INSERT INTO search_logs (query, results_found) VALUES (?, ?)",
        (query, results_found),
    )
    conn.commit()
    conn.close()


# ── Feedback ───────────────────────────────────────────────────────────────────

def insert_feedback(query: str, result_snippet: str, rating: int, comment: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO feedback (query, result_snippet, rating, comment) VALUES (?, ?, ?, ?)",
        (query, result_snippet, rating, comment),
    )
    conn.commit()
    conn.close()


def get_all_feedback() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM feedback ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_feedback_reviewed(feedback_id: int):
    conn = get_connection()
    conn.execute("UPDATE feedback SET reviewed = 1 WHERE id = ?", (feedback_id,))
    conn.commit()
    conn.close()


# ── Analytics ──────────────────────────────────────────────────────────────────

def get_top_queries(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT query, COUNT(*) as count
           FROM search_logs
           GROUP BY LOWER(query)
           ORDER BY count DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_no_result_queries(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT query, COUNT(*) as count
           FROM search_logs
           WHERE results_found = 0
           GROUP BY LOWER(query)
           ORDER BY count DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feedback_summary() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    positive = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = 1").fetchone()[0]
    negative = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = -1").fetchone()[0]
    unreviewed = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = -1 AND reviewed = 0").fetchone()[0]
    conn.close()
    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "unreviewed_negative": unreviewed,
    }


def get_search_volume_by_day(days: int = 14) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT DATE(timestamp) as day, COUNT(*) as count
           FROM search_logs
           WHERE timestamp >= DATE('now', ?)
           GROUP BY DATE(timestamp)
           ORDER BY day""",
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
