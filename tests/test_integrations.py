"""Integration schema, display, and sync tests."""

import pytest

from src import db
from src.integrations.github.display import format_display_source, parse_github_url
from src.integrations.github.sync import _remote_completed
from src.api.service_install import render_systemd_unit
from src.services import external as ext_svc
from src.services import tags as tags_svc
from src.services.todos import create_todo, get_todo_by_id, query_todos, ListFilters


@pytest.fixture
def db_isolated(tmp_path, monkeypatch):
    todos_dir = tmp_path / ".todos"
    todos_dir.mkdir()
    db_path = todos_dir / "todos.db"
    monkeypatch.setattr(db.connection, "get_data_dir", lambda: todos_dir)
    monkeypatch.setattr(db.connection, "get_db_path", lambda: db_path)
    db.connection.init_db()
    yield


def test_parse_github_issue_url():
    p = parse_github_url("https://github.com/beak-insights/beak-lims/issues/1025")
    assert p is not None
    assert p.organisation == "beak-insights"
    assert p.repository == "beak-lims"
    assert p.item_type == "issue"
    assert p.item_number == 1025


def test_parse_github_pr_url():
    p = parse_github_url("https://github.com/aurthurm/beak-todo/pull/14")
    assert p is not None
    assert p.item_type == "pr"
    assert p.item_number == 14


def test_format_display_source():
    s = format_display_source("beak-insights", "beak-lims", "issue", 1025)
    assert "[GitHub]" in s
    assert "beak-lims" in s
    assert "#1025" in s


def test_remote_completed():
    assert _remote_completed("closed")
    assert _remote_completed("merged")
    assert not _remote_completed("open")


def test_external_link_and_tags(db_isolated):
    sid = ext_svc.upsert_source("github", "org", "repo")
    iid = ext_svc.upsert_item(
        sid, "issue", 1, "Fix bug", "open", "https://github.com/org/repo/issues/1"
    )
    tid = create_todo("Fix bug")
    ext_svc.link_todo(tid, iid)
    tags_svc.add_tags_to_todo(tid, ["bug", "urgent"])

    rec = get_todo_by_id(tid)
    assert rec is not None
    assert rec.source_type == "github"
    assert rec.external is not None
    assert rec.external.organisation == "org"
    assert "bug" in rec.tags

    local = create_todo("Local only")
    locals_ = query_todos(ListFilters(source="local"))
    assert any(r.id == local for r in locals_)
    assert not any(r.id == tid for r in locals_)

    gh = query_todos(
        ListFilters(source="github", organisation="org", repository="repo")
    )
    assert any(r.id == tid for r in gh)

    tagged = query_todos(ListFilters(tags_all=["bug"]))
    assert any(r.id == tid for r in tagged)


def test_systemd_unit_template():
    unit = render_systemd_unit(
        "/usr/bin/beak-flow",
        "127.0.0.1",
        8787,
        __import__("pathlib").Path("/tmp/log"),
    )
    assert "beak-flow run" in unit
