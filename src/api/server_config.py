"""Beak Flow server settings at ~/.todos/beak-flow.toml."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore

from src.todos import get_data_dir

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


def get_config_path() -> Path:
    return get_data_dir() / "beak-flow.toml"


def _default_config() -> dict[str, Any]:
    log_path = get_data_dir() / "beak-flow.log"
    return {
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "log": str(log_path),
    }


def load_config() -> dict[str, Any]:
    path = get_config_path()
    cfg = _default_config()
    if path.is_file():
        with path.open("rb") as f:
            data = tomllib.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    cfg["host"] = os.environ.get("BEAK_FLOW_HOST", str(cfg.get("host", DEFAULT_HOST)))
    port_env = os.environ.get("BEAK_FLOW_PORT")
    if port_env:
        cfg["port"] = int(port_env)
    else:
        cfg["port"] = int(cfg.get("port", DEFAULT_PORT))
    log_env = os.environ.get("BEAK_FLOW_LOG")
    if log_env:
        cfg["log"] = log_env
    return cfg


def save_config(host: str, port: int, log: Optional[str] = None) -> Path:
    if tomli_w is None:
        raise RuntimeError("tomli-w is required to save Beak Flow config")
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {"host": host, "port": port}
    if log:
        data["log"] = log
    else:
        data["log"] = str(get_data_dir() / "beak-flow.log")
    with path.open("wb") as f:
        tomli_w.dump(data, f)
    return path


def resolve_host(explicit: Optional[str] = None) -> str:
    if explicit is not None:
        return explicit
    return str(load_config()["host"])


def resolve_port(explicit: Optional[int] = None) -> int:
    if explicit is not None:
        return explicit
    return int(load_config()["port"])


def resolve_log_path() -> Path:
    return Path(str(load_config().get("log", get_data_dir() / "beak-flow.log")))
