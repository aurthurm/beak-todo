"""Telegram channel tests (no live API)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src import db
from src.channels.dispatcher import dispatch
from src.channels.schemas import InternalCommand
from src.channels.telegram.handlers import handle_update, is_user_allowed
from src.channels.telegram.parser import parse_callback, parse_message
from src.config import save_config
from src.db.connection import get_db_connection
from src.services import pending_actions as pending_db
from src.services.todos import create_todo, query_todos


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
        "[telegram]\nenabled = true\nallowed_user_ids = [999]\n"
        "confirm_email_send = true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.get_config_path", lambda: cfg_path)
    yield todos_dir


def test_channel_tables_exist(db_isolated):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('channel_accounts', 'channel_messages', 'pending_actions')"
    )
    names = {r[0] for r in cur.fetchall()}
    conn.close()
    assert names == {"channel_accounts", "channel_messages", "pending_actions"}


def test_parser_add_and_done():
    cmd = parse_message("/add Finish report tomorrow", "999")
    assert cmd.action == "add"
    assert "Finish report" in cmd.args["text"]

    cmd2 = parse_message("/done 3", "999")
    assert cmd2.action == "done"
    assert cmd2.args["todo_id"] == "3"


def test_parser_report_weekly():
    cmd = parse_message("/report weekly", "999")
    assert cmd.action == "report_weekly"


def test_parser_callback_confirm():
    cmd = parse_callback("confirm:42", "999")
    assert cmd.action == "confirm"
    assert cmd.args["pending_id"] == "42"


def test_auth_allowlist(db_isolated):
    assert is_user_allowed(999, command="today") is True
    assert is_user_allowed(123, command="today") is False
    assert is_user_allowed(123, command="start") is True


def test_dispatch_add_creates_todo(db_isolated, monkeypatch):
    monkeypatch.setattr(
        "src.channels.dispatcher.ai_service.parse_single_task",
        lambda text: type(
            "P",
            (),
            {
                "message": text,
                "priority": 1,
                "category": "Work",
                "due_date": None,
            },
        )(),
    )
    reply = dispatch(
        InternalCommand("add", {"text": "Test from telegram"}, "telegram", "999")
    )
    assert "Added #" in reply.text
    open_tasks = [t for t in query_todos() if "telegram" in t.message.lower()]
    assert len(open_tasks) >= 1


def test_dispatch_done(db_isolated):
    tid = create_todo("To complete", 0, "General", None)
    reply = dispatch(
        InternalCommand("done", {"todo_id": str(tid)}, "telegram", "999")
    )
    assert "complete" in reply.text.lower()


def test_pending_brain_dump_confirm(db_isolated, monkeypatch):
    monkeypatch.setattr(
        "src.channels.dispatcher.ai_service.apply_parsed_tasks",
        lambda tasks: [101, 102],
    )
    pid = pending_db.create_pending(
        "telegram",
        "999",
        "brain_dump_apply",
        {
            "tasks": [
                {"message": "A", "priority": 0, "category": "General", "due_date": None},
            ]
        },
    )
    reply = dispatch(
        InternalCommand("confirm", {"pending_id": str(pid)}, "telegram", "999")
    )
    assert "Created" in reply.text
    assert pending_db.get_pending(pid) is None


def test_pending_cancel(db_isolated):
    pid = pending_db.create_pending(
        "telegram", "999", "email_send", {"to": "a@b.com", "report_id": 1}
    )
    reply = dispatch(
        InternalCommand("cancel", {"pending_id": str(pid)}, "telegram", "999")
    )
    assert "Cancelled" in reply.text


def test_handle_update_denied(db_isolated):
    update = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "chat": {"id": 111},
            "from": {"id": 555, "first_name": "Stranger"},
            "text": "/today",
        },
    }
    result = handle_update(update)
    assert result is not None
    chat_id, reply, _ = result
    assert chat_id == 111
    assert "Access denied" in reply.text


def test_email_send_pending(db_isolated, monkeypatch):
    from src.services import reports as reports_db

    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    cfg_path = db_isolated / "config.toml"
    cfg_path.write_text(
        "[telegram]\nenabled = true\nallowed_user_ids = [999]\n"
        "confirm_email_send = true\n"
        "[email]\nfrom = 'T <t@example.com>'\ndefault_to = 'boss@example.com'\n",
        encoding="utf-8",
    )
    reports_db.create_report("weekly", "2026-01-01", "2026-01-07", "Subj", "Body")
    reply = dispatch(
        InternalCommand("email_send", {}, "telegram", "999")
    )
    assert "Send report draft" in reply.text
    assert len(reply.inline_keyboard) == 1
