import pytest
from fastapi.testclient import TestClient

from src import db
from src.api.app import app
from src.services import todos as todos_mod


@pytest.fixture
def client(tmp_path, monkeypatch):
    todos_dir = tmp_path / ".todos"
    todos_dir.mkdir()
    db_path = todos_dir / "todos.db"
    monkeypatch.setattr(db.connection, "get_data_dir", lambda: todos_dir)
    monkeypatch.setattr(db.connection, "get_db_path", lambda: db_path)
    db.connection.init_db()
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_list(client):
    r = client.post(
        "/api/todos",
        json={"message": "API task", "priority": 2, "category": "Work", "due_date": "2030-01-15"},
    )
    assert r.status_code == 201
    tid = r.json()["id"]
    r2 = client.get("/api/todos", params={"due_date": "2030-01-15"})
    assert any(t["id"] == tid for t in r2.json())


def test_inbox(client):
    client.post("/api/todos", json={"message": "Inbox item", "priority": 0})
    r = client.get("/api/todos", params={"inbox": True})
    assert r.status_code == 200
    assert any(t["message"] == "Inbox item" for t in r.json())


def test_patch_clear_due(client):
    r = client.post(
        "/api/todos",
        json={"message": "Dated", "due_date": "2030-02-01"},
    )
    tid = r.json()["id"]
    client.patch(f"/api/todos/{tid}", json={"clear_due": True})
    r2 = client.get("/api/todos", params={"inbox": True})
    assert any(t["id"] == tid for t in r2.json())
