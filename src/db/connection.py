"""Database connection and migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def get_data_dir() -> Path:
    return Path.home() / ".todos"


def get_db_path() -> Path:
    return get_data_dir() / "todos.db"


def init_db() -> None:
    db_dir = get_data_dir()
    db_dir.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(get_db_path()))
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        priority INTEGER DEFAULT 0,
        category_id INTEGER,
        completed BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date TIMESTAMP,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        todo_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (todo_id) REFERENCES todos (id)
    )
    """
    )

    cursor.execute('INSERT OR IGNORE INTO categories (id, name) VALUES (1, "General")')
    conn.commit()
    conn.close()
    migrate_db()


def migrate_db() -> None:
    """Idempotent schema migrations."""
    conn = sqlite3.connect(str(get_db_path()))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(todos)")
    columns = {row[1] for row in cursor.fetchall()}
    if "sort_order" not in columns:
        cursor.execute("ALTER TABLE todos ADD COLUMN sort_order INTEGER DEFAULT 0")
        conn.commit()
    conn.close()


def ensure_db() -> None:
    init_db()


def get_db_connection() -> sqlite3.Connection:
    ensure_db()
    return sqlite3.connect(str(get_db_path()))
