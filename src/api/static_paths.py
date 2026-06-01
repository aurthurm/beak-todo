"""Resolve bundled UI static files for Beak Flow."""

from __future__ import annotations

import os
from pathlib import Path


def package_static_dir() -> Path:
    return Path(__file__).resolve().parent / "static"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ui_source_dir() -> Path:
    env = os.environ.get("BEAK_FLOW_REPO_ROOT")
    if env:
        return Path(env) / "ui"
    return repo_root() / "ui"


def resolve_static_dir() -> Path | None:
    """Return directory containing built UI (index.html), or None."""
    override = os.environ.get("BEAK_FLOW_STATIC_DIR")
    if override:
        path = Path(override)
        if (path / "index.html").is_file():
            return path

    bundled = package_static_dir()
    if (bundled / "index.html").is_file():
        return bundled

    legacy = repo_root() / "ui" / "dist"
    if (legacy / "index.html").is_file():
        return legacy

    return None
