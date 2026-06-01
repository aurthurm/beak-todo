import pytest

from src import todos as todos_mod


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    todos_dir = tmp_path / ".todos"
    todos_dir.mkdir()
    db_path = todos_dir / "todos.db"
    monkeypatch.setattr(todos_mod, "get_data_dir", lambda: todos_dir)
    monkeypatch.setattr(todos_mod, "get_db_path", lambda: db_path)
    todos_mod.init_db()
    return todos_dir


def test_create_todo(isolated_db):
    tid = todos_mod.create_todo("Test task", priority=2, category="Work")
    assert tid >= 1
    rows = todos_mod.fetch_todos()
    assert any(r[1] == "Test task" for r in rows)


def test_validate_due_date_rejects_past():
    with pytest.raises(ValueError):
        todos_mod.validate_due_date("2000-01-01", is_completed=False)


def test_list_category_names(isolated_db):
    todos_mod.create_todo("A", category="LIMS")
    names = todos_mod.list_category_names()
    assert "LIMS" in names
