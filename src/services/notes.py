"""Notes service."""

from __future__ import annotations

from dataclasses import dataclass

from src.db.connection import get_db_connection


@dataclass
class NoteRecord:
    id: int
    todo_id: int
    content: str
    created_at: str


def list_notes(todo_id: int) -> list[NoteRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, todo_id, content, created_at FROM notes WHERE todo_id = ? ORDER BY created_at",
        (todo_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [NoteRecord(id=r[0], todo_id=r[1], content=r[2], created_at=r[3]) for r in rows]


def add_note(todo_id: int, content: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (todo_id, content) VALUES (?, ?)", (todo_id, content))
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return note_id
