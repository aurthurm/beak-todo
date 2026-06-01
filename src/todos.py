"""SQLite todo storage and queries."""

from __future__ import annotations

import datetime
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from dateutil.parser import parse as date_parse

PRIORITIES = {
    0: ("Low", "blue"),
    1: ("Medium", "yellow"),
    2: ("High", "orange"),
    3: ("Critical", "red"),
}

TodoRow = tuple[int, str, int, Optional[str], int, Optional[str]]


def get_data_dir() -> Path:
    return Path.home() / ".todos"


def get_db_path() -> Path:
    return get_data_dir() / "todos.db"


def init_db() -> None:
    """Initialize the database if it doesn't exist."""
    db_dir = get_data_dir()
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "todos.db"

    conn = sqlite3.connect(str(db_path))
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


def ensure_db() -> None:
    """Create database and tables if missing."""
    if not get_db_path().exists():
        init_db()
    else:
        init_db()


def get_db_connection() -> sqlite3.Connection:
    ensure_db()
    return sqlite3.connect(str(get_db_path()))


def get_category_id(category_name: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return category_id


def get_category_name(category_id: Optional[int]) -> str:
    if category_id is None:
        return "None"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return "Unknown"


def format_due_date(due_date: Optional[str]) -> str:
    if due_date is None:
        return ""
    try:
        date_obj = datetime.datetime.fromisoformat(due_date)
        return date_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(due_date)


def validate_due_date(due_date_str: str, is_completed: bool = False) -> str:
    try:
        due_date = date_parse(due_date_str).date()
        today = datetime.datetime.now().date()
        if not is_completed and due_date < today:
            raise ValueError("Due date must be today or in the future for incomplete tasks")
        return due_date.isoformat()
    except ValueError as e:
        if "Due date must be" in str(e):
            raise
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.") from e


def create_todo(
    message: str,
    priority: int = 0,
    category: str = "General",
    due_date: Optional[str] = None,
    completed: int = 0,
) -> int:
    category_id = get_category_id(category)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todos (message, priority, category_id, due_date, completed) VALUES (?, ?, ?, ?, ?)",
        (message, priority, category_id, due_date, completed),
    )
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return todo_id


def get_todo_completed(id: int) -> Optional[bool]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT completed FROM todos WHERE id = ?", (id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        return None
    return bool(result[0])


def update_todo(
    id: int,
    message: Optional[str] = None,
    priority: Optional[int] = None,
    category: Optional[str] = None,
    due: Optional[str] = None,
    clear_due: bool = False,
) -> bool:
    is_completed = get_todo_completed(id)
    if is_completed is None:
        return False

    updates: list[str] = []
    values: list[Any] = []

    if message is not None:
        updates.append("message = ?")
        values.append(message)
    if priority is not None:
        updates.append("priority = ?")
        values.append(priority)
    if category is not None:
        category_id = get_category_id(category)
        updates.append("category_id = ?")
        values.append(category_id)
    if clear_due:
        updates.append("due_date = NULL")
    elif due is not None:
        due_date = validate_due_date(due, is_completed)
        updates.append("due_date = ?")
        values.append(due_date)

    if not updates:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
    values.append(id)
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    return True


@dataclass
class ListFilters:
    priority: Optional[int] = None
    category: Optional[str] = None
    done: bool = False
    undone: bool = False
    sort_by_due: bool = False
    overdue: bool = False


def fetch_todos(filters: Optional[ListFilters] = None) -> list[TodoRow]:
    filters = filters or ListFilters()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT t.id, t.message, t.priority, c.name, t.completed, t.due_date
    FROM todos t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE 1=1
    """
    params: list[Any] = []

    if filters.priority is not None:
        query += " AND t.priority = ?"
        params.append(filters.priority)
    if filters.category is not None:
        query += " AND c.name = ?"
        params.append(filters.category)
    if filters.done:
        query += " AND t.completed = 1"
    if filters.undone:
        query += " AND t.completed = 0"
    if filters.overdue:
        today = datetime.datetime.now().date().isoformat()
        query += " AND t.due_date < ? AND t.completed = 0"
        params.append(today)

    if filters.sort_by_due:
        query += " ORDER BY t.due_date, t.priority DESC"
    else:
        query += " ORDER BY t.priority DESC, t.id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_todos(keywords: list[str]) -> list[TodoRow]:
    if not keywords:
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    conditions = []
    params: list[str] = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append("(t.message LIKE ? OR c.name LIKE ?)")
        params.extend([pattern, pattern])
    where = " OR ".join(conditions)
    query = f"""
    SELECT DISTINCT t.id, t.message, t.priority, c.name, t.completed, t.due_date
    FROM todos t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE {where}
    ORDER BY t.priority DESC, t.id
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_todos_single(keyword: str) -> list[TodoRow]:
    return search_todos([keyword])


def list_category_names() -> list[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names


def _today_iso() -> str:
    return datetime.datetime.now().date().isoformat()


def fetch_open_todos_for_planning(horizon_days: int = 7) -> list[dict[str, Any]]:
    """Incomplete todos: overdue first, then by priority and due date within horizon."""
    today = datetime.datetime.now().date()
    horizon_end = (today + datetime.timedelta(days=horizon_days)).isoformat()
    today_iso = today.isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.id, t.message, t.priority, c.name, t.due_date
        FROM todos t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.completed = 0
        ORDER BY
            CASE WHEN t.due_date IS NOT NULL AND t.due_date < ? THEN 0 ELSE 1 END,
            t.priority DESC,
            (t.due_date IS NULL),
            t.due_date ASC,
            t.id
        """,
        (today_iso,),
    )
    rows = cursor.fetchall()
    conn.close()

    result: list[dict[str, Any]] = []
    for todo_id, message, priority, category_name, due_date in rows:
        if category_name is None:
            category_name = "General"
        overdue = False
        if due_date:
            try:
                overdue = datetime.datetime.fromisoformat(due_date).date() < today
            except ValueError:
                pass
            if not overdue and due_date > horizon_end:
                continue
        result.append(
            {
                "id": todo_id,
                "message": message,
                "priority": priority,
                "priority_label": PRIORITIES.get(priority, ("?", ""))[0],
                "category": category_name,
                "due_date": due_date,
                "overdue": overdue,
            }
        )
    return result


def fetch_stats_snapshot() -> dict[str, Any]:
    today = _today_iso()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM todos")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM todos WHERE completed = 1")
    completed = cursor.fetchone()[0]

    incomplete = total - completed

    cursor.execute(
        "SELECT COUNT(*) FROM todos WHERE due_date < ? AND completed = 0",
        (today,),
    )
    overdue = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT priority, COUNT(*) FROM todos WHERE completed = 0 GROUP BY priority ORDER BY priority
        """
    )
    priority_open = dict(cursor.fetchall())

    cursor.execute(
        """
        SELECT priority, COUNT(*) FROM todos
        WHERE completed = 0 AND priority = 3
        """
    )
    critical_open = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT c.name, COUNT(t.id)
        FROM categories c
        LEFT JOIN todos t ON c.id = t.category_id AND t.completed = 0
        GROUP BY c.id
        ORDER BY COUNT(t.id) DESC
        """
    )
    category_open = cursor.fetchall()

    cursor.execute(
        """
        SELECT t.id, t.message, t.priority, c.name, t.due_date
        FROM todos t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.completed = 0 AND t.priority >= 2
        ORDER BY t.priority DESC, (t.due_date IS NULL), t.due_date ASC
        LIMIT 10
        """
    )
    top_urgent = [
        {
            "id": r[0],
            "message": r[1],
            "priority": r[2],
            "category": r[3] or "General",
            "due_date": r[4],
        }
        for r in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT COUNT(*) FROM todos
        WHERE completed = 0 AND due_date IS NOT NULL AND due_date <= ?
        AND priority = 3
        """,
        ((datetime.datetime.now().date() + datetime.timedelta(days=2)).isoformat(),),
    )
    critical_due_soon = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM todos
        WHERE completed = 0 AND due_date IS NULL AND priority >= 2
        """
    )
    high_no_due = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "completed": completed,
        "incomplete": incomplete,
        "overdue": overdue,
        "priority_open": priority_open,
        "critical_open": critical_open,
        "category_open": category_open,
        "top_urgent": top_urgent,
        "critical_due_soon": critical_due_soon,
        "high_no_due": high_no_due,
        "today": today,
    }
