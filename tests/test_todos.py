import pytest

from src import db
from src.services import todos as todos_mod


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    todos_dir = tmp_path / ".todos"
    todos_dir.mkdir()
    db_path = todos_dir / "todos.db"
    monkeypatch.setattr(db.connection, "get_data_dir", lambda: todos_dir)
    monkeypatch.setattr(db.connection, "get_db_path", lambda: db_path)
    db.connection.init_db()
    return todos_dir


def test_create_todo(isolated_db):
    tid = todos_mod.create_todo("Test task", priority=2, category="Work")
    assert tid >= 1
    rows = todos_mod.fetch_todos()
    assert any(r[1] == "Test task" for r in rows)


def test_inbox_query(isolated_db):
    todos_mod.create_todo("Inbox only", category="General")
    inbox = todos_mod.fetch_inbox()
    assert any(t.message == "Inbox only" for t in inbox)


def test_sort_order_migration(isolated_db):
    tid = todos_mod.create_todo("Ordered", sort_order=5)
    rec = todos_mod.get_todo_by_id(tid)
    assert rec is not None
    assert rec.sort_order == 5


def test_validate_due_date_rejects_past():
    with pytest.raises(ValueError):
        todos_mod.validate_due_date("2000-01-01", is_completed=False)
