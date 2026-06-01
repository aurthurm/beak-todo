import os
from pathlib import Path

import pytest

from src import config as config_mod


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    todos_dir = tmp_path / ".todos"
    todos_dir.mkdir()
    monkeypatch.setattr(config_mod, "get_data_dir", lambda: todos_dir)
    monkeypatch.setattr(
        config_mod,
        "get_config_path",
        lambda: todos_dir / "config.toml",
    )
    return todos_dir


def test_default_config_when_missing(isolated_config):
    cfg = config_mod.load_config()
    assert cfg["ai"]["provider"] == "auto"
    assert cfg["ai"]["enabled"] is True


def test_set_and_load(isolated_config):
    config_mod.set_config_value("ai.provider", "openai")
    assert config_mod.get_config_value("ai.provider") == "openai"


def test_ensure_default_config_creates_file(isolated_config):
    path = config_mod.ensure_default_config()
    assert path.exists()
