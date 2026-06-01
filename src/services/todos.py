"""Todo service layer — shared by CLI and API."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Optional

from dateutil.parser import parse as date_parse

from src.db.connection import get_db_connection

PRIORITIES = {
    0: ("Low", "blue"),
    1: ("Medium", "yellow"),
    2: ("High", "orange"),
    3: ("Critical", "red"),
}

TodoRow = tuple[int, str, int, Optional[str], int, Optional[str], int]


@dataclass
class TodoRecord:
    id: int
    message: str
    priority: int
    category: str
    completed: bool
    due_date: Optional[str]
    sort_order: int = 0

    @property
    def priority_label(self) -> str:
        return PRIORITIES.get(self.priority, ("?", ""))[0]

    @property
    def priority_color(self) -> str:
        return PRIORITIES.get(self.priority, ("", "gray"))[1]


def _row_to_record(row: tuple) -> TodoRecord:
    todo_id, message, priority, category_name, completed, due_date, sort_order = row
    return TodoRecord(
        id=todo_id,
        message=message,
        priority=priority,
        category=category_name or "General",
        completed=bool(completed),
        due_date=due_date,
        sort_order=sort_order or 0,
    )


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
        return "General"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Unknown"


def format_due_date(due_date: Optional[str]) -> str:
    if due_date is None:
        return ""
    try:
        return datetime.datetime.fromisoformat(due_date).strftime("%Y-%m-%d")
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
    sort_order: int = 0,
) -> int:
    category_id = get_category_id(category)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO todos (message, priority, category_id, due_date, completed, sort_order)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (message, priority, category_id, due_date, completed, sort_order),
    )
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return todo_id


def get_todo_by_id(todo_id: int) -> Optional[TodoRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.id, t.message, t.priority, c.name, t.completed, t.due_date, t.sort_order
        FROM todos t LEFT JOIN categories c ON t.category_id = c.id WHERE t.id = ?
        """,
        (todo_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_record(row) if row else None


def get_todo_completed(todo_id: int) -> Optional[bool]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT completed FROM todos WHERE id = ?", (todo_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        return None
    return bool(result[0])


def delete_todo(todo_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE todo_id = ?", (todo_id,))
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def update_todo(
    todo_id: int,
    message: Optional[str] = None,
    priority: Optional[int] = None,
    category: Optional[str] = None,
    due: Optional[str] = None,
    clear_due: bool = False,
    completed: Optional[bool] = None,
    sort_order: Optional[int] = None,
) -> bool:
    is_completed = get_todo_completed(todo_id)
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
        updates.append("category_id = ?")
        values.append(get_category_id(category))
    if clear_due:
        updates.append("due_date = NULL")
    elif due is not None:
        due_date = validate_due_date(due, is_completed if completed is None else completed)
        updates.append("due_date = ?")
        values.append(due_date)
    if completed is not None:
        updates.append("completed = ?")
        values.append(1 if completed else 0)
    if sort_order is not None:
        updates.append("sort_order = ?")
        values.append(sort_order)

    if not updates:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
    values.append(todo_id)
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    return True


def reorder_todos(order: list[tuple[int, int]]) -> None:
    """Batch update sort_order: list of (todo_id, sort_order)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for todo_id, sort_order in order:
        cursor.execute("UPDATE todos SET sort_order = ? WHERE id = ?", (sort_order, todo_id))
    conn.commit()
    conn.close()


@dataclass
class ListFilters:
    priority: Optional[int] = None
    category: Optional[str] = None
    done: bool = False
    undone: bool = False
    sort_by_due: bool = False
    overdue: bool = False
    due_date: Optional[str] = None
    due_from: Optional[str] = None
    due_to: Optional[str] = None
    inbox: bool = False
    search: Optional[str] = None


def _base_select() -> str:
    return """
    SELECT t.id, t.message, t.priority, c.name, t.completed, t.due_date, t.sort_order
    FROM todos t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE 1=1
    """


def query_todos(filters: Optional[ListFilters] = None) -> list[TodoRecord]:
    filters = filters or ListFilters()
    conn = get_db_connection()
    cursor = conn.cursor()
    query = _base_select()
    params: list[Any] = []

    if filters.inbox:
        query += " AND t.due_date IS NULL AND t.completed = 0"
    if filters.due_date is not None:
        query += " AND t.due_date = ?"
        params.append(filters.due_date)
    if filters.due_from is not None:
        query += " AND t.due_date >= ?"
        params.append(filters.due_from)
    if filters.due_to is not None:
        query += " AND t.due_date <= ?"
        params.append(filters.due_to)
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
    if filters.search:
        pattern = f"%{filters.search}%"
        query += " AND (t.message LIKE ? OR c.name LIKE ?)"
        params.extend([pattern, pattern])

    if filters.sort_by_due:
        query += " ORDER BY t.due_date, t.sort_order, t.priority DESC"
    else:
        query += " ORDER BY t.sort_order, t.priority DESC, t.id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_record(r) for r in rows]


def fetch_todos(filters: Optional[ListFilters] = None) -> list[tuple]:
    """Legacy 6-tuple rows for CLI display."""
    records = query_todos(filters)
    return [
        (r.id, r.message, r.priority, r.category, int(r.completed), r.due_date)
        for r in records
    ]


def fetch_inbox() -> list[TodoRecord]:
    return query_todos(ListFilters(inbox=True))


def fetch_by_date_range(due_from: str, due_to: str, include_completed: bool = False) -> list[TodoRecord]:
    f = ListFilters(due_from=due_from, due_to=due_to)
    if not include_completed:
        f.undone = True
    return query_todos(f)


def fetch_by_due_date(due_date: str) -> list[TodoRecord]:
    return query_todos(ListFilters(due_date=due_date))


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
    SELECT DISTINCT t.id, t.message, t.priority, c.name, t.completed, t.due_date, t.sort_order
    FROM todos t LEFT JOIN categories c ON t.category_id = c.id
    WHERE {where}
    ORDER BY t.sort_order, t.priority DESC, t.id
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [
        (r[0], r[1], r[2], r[3] or "General", r[4], r[5])
        for r in rows
    ]


def search_todos_single(keyword: str) -> list[tuple]:
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
    today = datetime.datetime.now().date()
    horizon_end = (today + datetime.timedelta(days=horizon_days)).isoformat()
    today_iso = today.isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.id, t.message, t.priority, c.name, t.due_date
        FROM todos t LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.completed = 0
        ORDER BY
            CASE WHEN t.due_date IS NOT NULL AND t.due_date < ? THEN 0 ELSE 1 END,
            t.priority DESC, (t.due_date IS NULL), t.due_date ASC, t.id
        """,
        (today_iso,),
    )
    rows = cursor.fetchall()
    conn.close()

    result: list[dict[str, Any]] = []
    for todo_id, message, priority, category_name, due_date in rows:
        category_name = category_name or "General"
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
        "SELECT COUNT(*) FROM todos WHERE due_date < ? AND completed = 0", (today,)
    )
    overdue = cursor.fetchone()[0]
    cursor.execute(
        "SELECT priority, COUNT(*) FROM todos WHERE completed = 0 GROUP BY priority ORDER BY priority"
    )
    priority_open = dict(cursor.fetchall())
    cursor.execute("SELECT COUNT(*) FROM todos WHERE completed = 0 AND priority = 3")
    critical_open = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT c.name, COUNT(t.id) FROM categories c
        LEFT JOIN todos t ON c.id = t.category_id AND t.completed = 0
        GROUP BY c.id ORDER BY COUNT(t.id) DESC
        """
    )
    category_open = cursor.fetchall()
    cursor.execute(
        """
        SELECT t.id, t.message, t.priority, c.name, t.due_date
        FROM todos t LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.completed = 0 AND t.priority >= 2
        ORDER BY t.priority DESC, (t.due_date IS NULL), t.due_date ASC LIMIT 10
        """
    )
    top_urgent = [
        {"id": r[0], "message": r[1], "priority": r[2], "category": r[3] or "General", "due_date": r[4]}
        for r in cursor.fetchall()
    ]
    cursor.execute(
        """
        SELECT COUNT(*) FROM todos
        WHERE completed = 0 AND due_date IS NOT NULL AND due_date <= ? AND priority = 3
        """,
        ((datetime.datetime.now().date() + datetime.timedelta(days=2)).isoformat(),),
    )
    critical_due_soon = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM todos WHERE completed = 0 AND due_date IS NULL AND priority >= 2"
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
