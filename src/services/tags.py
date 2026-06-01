"""Tag service — many-to-many tags on todos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.db.connection import get_db_connection


@dataclass
class TagRecord:
    id: int
    name: str
    todo_count: int = 0


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def get_or_create_tag(name: str) -> int:
    normalized = _normalize_name(name)
    if not normalized:
        raise ValueError("Tag name cannot be empty")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tags WHERE name = ? COLLATE NOCASE", (normalized,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
    cursor.execute("INSERT INTO tags (name) VALUES (?)", (normalized,))
    tag_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tag_id


def list_tags() -> list[TagRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT tg.id, tg.name, COUNT(tt.todo_id) AS cnt
        FROM tags tg
        LEFT JOIN todo_tags tt ON tg.id = tt.tag_id
        GROUP BY tg.id
        ORDER BY tg.name
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [TagRecord(id=r[0], name=r[1], todo_count=r[2]) for r in rows]


def get_tags_for_todos(todo_ids: list[int]) -> dict[int, list[str]]:
    if not todo_ids:
        return {}
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(todo_ids))
    cursor.execute(
        f"""
        SELECT tt.todo_id, tg.name
        FROM todo_tags tt
        JOIN tags tg ON tt.tag_id = tg.id
        WHERE tt.todo_id IN ({placeholders})
        ORDER BY tg.name
        """,
        todo_ids,
    )
    result: dict[int, list[str]] = {tid: [] for tid in todo_ids}
    for todo_id, name in cursor.fetchall():
        result[todo_id].append(name)
    conn.close()
    return result


def get_tags_for_todo(todo_id: int) -> list[str]:
    return get_tags_for_todos([todo_id]).get(todo_id, [])


def _tag_id_in_conn(cursor, normalized: str) -> int:
    cursor.execute("SELECT id FROM tags WHERE name = ? COLLATE NOCASE", (normalized,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO tags (name) VALUES (?)", (normalized,))
    return cursor.lastrowid


def set_todo_tags(todo_id: int, tag_names: list[str]) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todo_tags WHERE todo_id = ?", (todo_id,))
    for name in tag_names:
        normalized = _normalize_name(name)
        if not normalized:
            continue
        tag_id = _tag_id_in_conn(cursor, normalized)
        cursor.execute(
            "INSERT OR IGNORE INTO todo_tags (todo_id, tag_id) VALUES (?, ?)",
            (todo_id, tag_id),
        )
    conn.commit()
    conn.close()


def add_tags_to_todo(todo_id: int, tag_names: list[str]) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    for name in tag_names:
        normalized = _normalize_name(name)
        if not normalized:
            continue
        tag_id = _tag_id_in_conn(cursor, normalized)
        cursor.execute(
            "INSERT OR IGNORE INTO todo_tags (todo_id, tag_id) VALUES (?, ?)",
            (todo_id, tag_id),
        )
    conn.commit()
    conn.close()


def merge_tags_for_todo(todo_id: int, tag_names: list[str]) -> None:
    existing = set(get_tags_for_todo(todo_id))
    for name in tag_names:
        normalized = _normalize_name(name)
        if normalized:
            existing.add(normalized)
    set_todo_tags(todo_id, sorted(existing))
