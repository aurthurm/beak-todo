"""Categories service."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from src.db.connection import get_db_connection


@dataclass
class CategoryRecord:
    id: int
    name: str
    todo_count: int


def list_categories() -> list[CategoryRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.id, c.name, COUNT(t.id)
        FROM categories c LEFT JOIN todos t ON c.id = t.category_id
        GROUP BY c.id ORDER BY c.name
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [CategoryRecord(id=r[0], name=r[1], todo_count=r[2]) for r in rows]


def add_category(name: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        cid = cursor.lastrowid
        conn.commit()
        conn.close()
        return cid
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Category '{name}' already exists")
