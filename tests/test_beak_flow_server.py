"""Tests for Beak Flow static paths and service templates."""

from pathlib import Path

from src.api import service_install
from src.api.static_paths import package_static_dir, resolve_static_dir


def test_resolve_static_dir_prefers_bundled(tmp_path, monkeypatch):
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(
        "src.api.static_paths.package_static_dir",
        lambda: static,
    )
    monkeypatch.delenv("BEAK_FLOW_STATIC_DIR", raising=False)
    assert resolve_static_dir() == static


def test_resolve_static_dir_env_override(tmp_path, monkeypatch):
    custom = tmp_path / "custom"
    custom.mkdir()
    (custom / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setenv("BEAK_FLOW_STATIC_DIR", str(custom))
    assert resolve_static_dir() == custom


def test_resolve_static_dir_none_when_missing(monkeypatch):
    empty = Path("/nonexistent/beak-flow-static-test")
    monkeypatch.setattr(
        "src.api.static_paths.package_static_dir",
        lambda: empty,
    )
    monkeypatch.delenv("BEAK_FLOW_STATIC_DIR", raising=False)
    monkeypatch.setattr(
        "src.api.static_paths.repo_root",
        lambda: empty,
    )
    assert resolve_static_dir() is None


def test_systemd_unit_contains_exec_and_port():
    unit = service_install.render_systemd_unit(
        "/usr/bin/beak-flow",
        "127.0.0.1",
        8787,
        Path("/home/user/.todos/beak-flow.log"),
    )
    assert "ExecStart=/usr/bin/beak-flow run --host 127.0.0.1 --port 8787" in unit
    assert "beak-flow.log" in unit


def test_launchd_plist_contains_program_arguments():
    plist = service_install.render_launchd_plist(
        "/usr/local/bin/beak-flow",
        "0.0.0.0",
        9000,
        Path("/tmp/beak-flow.log"),
    )
    assert "<string>/usr/local/bin/beak-flow</string>" in plist
    assert "<string>9000</string>" in plist
