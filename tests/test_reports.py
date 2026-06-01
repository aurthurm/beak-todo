"""Reports and email integration tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src import db
from src.db.connection import get_db_connection
from src.integrations.email.draft import send_draft
from src.reports.collector import collect_weekly_context
from src.reports.formatters import format_context_as_text
from src.services import reports as reports_db
from src.services.report_service import generate_weekly
from src.services.todos import create_todo, update_todo


@pytest.fixture
def db_isolated(tmp_path, monkeypatch):
    todos_dir = tmp_path / ".todos"
    todos_dir.mkdir()
    db_path = todos_dir / "todos.db"
    monkeypatch.setattr(db.connection, "get_data_dir", lambda: todos_dir)
    monkeypatch.setattr(db.connection, "get_db_path", lambda: db_path)
    db.connection.init_db()
    cfg_path = todos_dir / "config.toml"
    cfg_path.write_text(
        '[email]\nfrom = "Test <test@example.com>"\n'
        'default_to = "boss@example.com"\n'
        'send_mode = "draft_first"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.get_config_path", lambda: cfg_path)
    yield todos_dir


def test_reports_tables_exist(db_isolated):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('reports', 'email_sends')"
    )
    names = {r[0] for r in cur.fetchall()}
    conn.close()
    assert "reports" in names
    assert "email_sends" in names


def test_completed_at_set_on_complete(db_isolated):
    tid = create_todo("Finish report", 1, "Work", None)
    update_todo(tid, completed=True)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT completed_at FROM todos WHERE id = ?", (tid,))
    row = cur.fetchone()
    conn.close()
    assert row[0] is not None


def test_collector_completed_in_period(db_isolated):
    tid = create_todo("Ship feature", 2, "Work", None)
    update_todo(tid, completed=True)
    ctx = collect_weekly_context("2000-01-01", "2099-12-31")
    text = format_context_as_text(ctx)
    assert "Ship feature" in text


def test_draft_save_and_load(db_isolated):
    rid = reports_db.create_report(
        "weekly",
        "2026-05-01",
        "2026-05-07",
        "Subject",
        "Body text",
        "<p>Body</p>",
    )
    draft = reports_db.get_current_draft()
    assert draft is not None
    assert draft.id == rid
    assert draft.status == "draft"


def test_send_blocked_without_api_key(db_isolated, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    reports_db.create_report(
        "weekly",
        "2026-05-01",
        "2026-05-07",
        "Subject",
        "Body",
    )
    with pytest.raises(Exception):
        send_draft("test@example.com", force=True)


def test_send_draft_mock_resend(db_isolated, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    rid = reports_db.create_report(
        "weekly",
        "2026-05-01",
        "2026-05-07",
        "Weekly",
        "Hello body",
        "<p>Hello</p>",
    )

    mock_send = MagicMock(return_value={"id": "msg_abc123"})
    with patch("resend.Emails.send", mock_send):
        message_id, send_id = send_draft("boss@example.com", force=True)

    assert message_id == "msg_abc123"
    report = reports_db.get_report(rid)
    assert report.status == "sent"
    sends = reports_db.list_email_sends(limit=1)
    assert sends[0].id == send_id
    assert sends[0].status == "sent"


def test_generate_weekly_no_ai(db_isolated):
    create_todo("Task A", 0, "General", None)
    content, _ = generate_weekly(
        "2000-01-01",
        "2099-12-31",
        use_ai=False,
        save_draft=False,
    )
    assert "Weekly Work Update" in content.subject
    assert content.body_text


def test_api_reports_generate(db_isolated):
    from src.api.app import app

    client = TestClient(app)
    res = client.post(
        "/api/reports/weekly/generate",
        json={"from": "2026-05-01", "to": "2026-05-07", "use_ai": False},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "draft"
    assert "subject" in data
