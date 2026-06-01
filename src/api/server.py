"""Beak Flow CLI: run server, build UI, install OS service."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from src.api.server_config import (
    resolve_host,
    resolve_log_path,
    resolve_port,
    save_config,
)
from src.api.service_install import (
    install_service,
    service_status,
    uninstall_service,
    warn_if_ui_missing,
)
from src.api.static_paths import package_static_dir, resolve_static_dir, ui_source_dir

cli = typer.Typer(
    help="Beak Flow planning gateway — API + UI on one port.",
    no_args_is_help=False,
)


def _run_server(host: str, port: int) -> None:
    import uvicorn

    warn_if_ui_missing()
    logging.basicConfig(level=logging.INFO)
    url = f"http://{host}:{port}"
    typer.echo(f"Starting Beak Flow at {url}")
    if resolve_static_dir() is not None:
        typer.echo(f"  UI: {url}/")
    else:
        typer.echo("  UI: not available (run `beak-flow build-ui`)")
    typer.echo(f"  API docs: {url}/docs")
    uvicorn.run("src.api.app:app", host=host, port=port, reload=False)


@cli.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    host: Optional[str] = typer.Option(
        None, "--host", help="Bind host (default from ~/.todos/beak-flow.toml)"
    ),
    port: Optional[int] = typer.Option(
        None, "--port", help="Bind port (default from ~/.todos/beak-flow.toml)"
    ),
) -> None:
    """Default: run the server in the foreground."""
    if ctx.invoked_subcommand is None:
        _run_server(resolve_host(host), resolve_port(port))


@cli.command()
def run(
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    """Run the Beak Flow server (API + static UI)."""
    _run_server(resolve_host(host), resolve_port(port))


@cli.command("build-ui")
def build_ui(
    install_deps: bool = typer.Option(
        True,
        "--install-deps/--no-install-deps",
        help="Run npm install before build",
    ),
) -> None:
    """Build the Vue UI into src/api/static for single-port serving."""
    ui_dir = ui_source_dir()
    if not (ui_dir / "package.json").is_file():
        typer.echo(f"UI project not found at {ui_dir}", err=True)
        raise typer.Exit(1)
    if shutil.which("npm") is None:
        typer.echo("npm not found. Install Node.js 18+ and try again.", err=True)
        raise typer.Exit(1)

    package_static_dir().mkdir(parents=True, exist_ok=True)

    if install_deps:
        typer.echo("Installing npm dependencies…")
        subprocess.run(["npm", "install"], cwd=ui_dir, check=True)

    typer.echo("Building UI…")
    subprocess.run(["npm", "run", "build"], cwd=ui_dir, check=True)

    index = package_static_dir() / "index.html"
    if not index.is_file():
        typer.echo(f"Build failed: {index} not found", err=True)
        raise typer.Exit(1)
    typer.echo(f"UI built at {index}")


@cli.command("install-service")
def cmd_install_service(
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    """Install Beak Flow to start in the background (systemd / launchd / Task Scheduler)."""
    try:
        install_service(host=host, port=port)
    except RuntimeError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        typer.echo(f"Service install failed: {e.stderr or e}", err=True)
        raise typer.Exit(1) from e


@cli.command("uninstall-service")
def cmd_uninstall_service() -> None:
    """Remove the Beak Flow OS service."""
    try:
        uninstall_service()
    except subprocess.CalledProcessError as e:
        typer.echo(f"Uninstall failed: {e.stderr or e}", err=True)
        raise typer.Exit(1) from e


@cli.command("service-status")
def cmd_service_status() -> None:
    """Show whether the Beak Flow OS service is installed and running."""
    typer.echo(service_status())
    cfg_host = resolve_host()
    cfg_port = resolve_port()
    typer.echo(f"config: http://{cfg_host}:{cfg_port}/")
    typer.echo(f"log: {resolve_log_path()}")


def main_entry() -> None:
    cli()


if __name__ == "__main__":
    main_entry()
