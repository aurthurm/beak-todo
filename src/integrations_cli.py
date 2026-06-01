"""CLI: t integrations ..."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.integrations.github.config import (
    add_repo_to_config,
    get_config_path,
    load_github_config,
    parse_repos,
    write_default_config,
)
from src.integrations.github.display import normalize_repo_slug
from src.integrations.registry import get_integration
from src.services import external as ext_svc

integrations_app = typer.Typer(help="External integrations (GitHub, …)")
github_app = typer.Typer(help="GitHub issues and pull requests")
integrations_app.add_typer(github_app, name="github")
console = Console()


@github_app.command("setup")
def github_setup():
    """Create ~/.todos/integrations/github.toml template."""
    path = write_default_config()
    typer.echo(f"Created {path}")
    typer.echo("Set GITHUB_TOKEN or edit token_file, then add repos and run: t integrations github doctor")


@github_app.command("doctor")
def github_doctor():
    """Verify GitHub token and configuration."""
    gh = get_integration("github")
    for line in gh.doctor():
        if line.startswith("OK:"):
            console.print(f"[green]{line}[/green]")
        else:
            console.print(line)


@github_app.command("sync")
def github_sync(
    org: Optional[str] = typer.Option(None, "--org", help="Organisation filter"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository filter"),
):
    """Sync issues and PRs from configured GitHub repos."""
    gh = get_integration("github")
    result = gh.sync(organisation=org, repository=repo)
    typer.echo(
        f"Sync complete: created={result.created} updated={result.updated} "
        f"pushed={result.pushed}"
    )
    for err in result.errors:
        typer.echo(f"  error: {err}", err=True)
    if result.errors:
        raise typer.Exit(1)


@github_app.callback(invoke_without_command=True)
def github_group(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


repos_app = typer.Typer(help="Manage configured repositories")
github_app.add_typer(repos_app, name="repos")


@repos_app.command("list")
def repos_list():
    cfg = load_github_config()
    repos = parse_repos(cfg)
    table = Table(title="GitHub repos")
    table.add_column("Organisation")
    table.add_column("Repository")
    table.add_column("Enabled")
    table.add_column("Issues")
    table.add_column("PRs")
    for r in repos:
        table.add_row(
            r.organisation,
            r.repository,
            str(r.enabled),
            str(r.sync_issues),
            str(r.sync_prs),
        )
    if not repos:
        typer.echo(f"No repos in {get_config_path()}")
    else:
        console.print(table)


@repos_app.command("add")
def repos_add(slug: str = typer.Argument(..., help="org/repo")):
    org, repo = normalize_repo_slug(slug)
    path = add_repo_to_config(org, repo)
    ext_svc.upsert_source("github", org, repo)
    typer.echo(f"Added {org}/{repo} to {path}")


@github_app.command("link")
def github_link(
    todo_id: int = typer.Argument(..., help="Local todo id"),
    url: str = typer.Argument(..., help="GitHub issue or PR URL"),
):
    gh = get_integration("github")
    gh.link_todo(todo_id, url)
    typer.echo(f"Linked todo #{todo_id} to {url}")


@github_app.command("unlink")
def github_unlink(todo_id: int = typer.Argument(..., help="Local todo id")):
    gh = get_integration("github")
    if gh.unlink_todo(todo_id):
        typer.echo(f"Unlinked todo #{todo_id}")
    else:
        typer.echo(f"Todo #{todo_id} has no external link")
        raise typer.Exit(1)
