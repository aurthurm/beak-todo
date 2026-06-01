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
    if "updated_at" not in columns:
        cursor.execute(
            "ALTER TABLE todos ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS external_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            organisation TEXT NOT NULL,
            repository TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            sync_issues INTEGER DEFAULT 1,
            sync_prs INTEGER DEFAULT 1,
            last_synced_at TEXT,
            UNIQUE(provider, organisation, repository)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS external_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_number INTEGER NOT NULL,
            github_id TEXT,
            title TEXT NOT NULL,
            state TEXT NOT NULL,
            url TEXT NOT NULL,
            assignees_json TEXT,
            updated_at_remote TEXT,
            last_synced_at TEXT,
            FOREIGN KEY (source_id) REFERENCES external_sources (id),
            UNIQUE(source_id, item_type, item_number)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS todo_external_links (
            todo_id INTEGER PRIMARY KEY,
            external_item_id INTEGER NOT NULL,
            link_kind TEXT DEFAULT 'sync',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (todo_id) REFERENCES todos (id) ON DELETE CASCADE,
            FOREIGN KEY (external_item_id) REFERENCES external_items (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL COLLATE NOCASE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS todo_tags (
            todo_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (todo_id, tag_id),
            FOREIGN KEY (todo_id) REFERENCES todos (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_external_items_source_state "
        "ON external_items (source_id, state)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_todo_tags_tag ON todo_tags (tag_id)"
    )
    conn.commit()
    conn.close()


def ensure_db() -> None:
    init_db()


def get_db_connection() -> sqlite3.Connection:
    ensure_db()
    return sqlite3.connect(str(get_db_path()))
