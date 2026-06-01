"""t config — manage ~/.todos/config.toml."""

from __future__ import annotations

import os
import subprocess
from typing import Optional

import typer

from src.config import (
    ensure_default_config,
    get_config_path,
    get_config_value,
    load_config,
    redact_config_for_display,
    set_config_value,
)

config_app = typer.Typer(help="Manage application configuration")


@config_app.command("show")
def config_show():
    """Show effective configuration."""
    cfg = redact_config_for_display()
    import json

    typer.echo(json.dumps(cfg, indent=2))


@config_app.command("path")
def config_path():
    """Print path to config.toml."""
    typer.echo(str(get_config_path()))


@config_app.command("get")
def config_get(key: str):
    """Get a config value (e.g. ai.provider)."""
    try:
        value = get_config_value(key)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    typer.echo(value)


@config_app.command("set")
def config_set(key: str, value: str):
    """Set a config value (e.g. ai.provider openai)."""
    try:
        set_config_value(key, value)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    typer.echo(f"Set {key} = {value}")


@config_app.command("edit")
def config_edit():
    """Open config.toml in $EDITOR."""
    path = ensure_default_config()
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(path)], check=False)
