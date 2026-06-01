"""CLI: t tag ..."""

from __future__ import annotations

import typer
from rich.table import Table
from rich.console import Console

from src.services import tags as tags_svc
from src.services.todos import get_todo_by_id

tag_app = typer.Typer(help="Tags on todos")
console = Console()


@tag_app.command("list")
def tag_list():
    """List all tags."""
    tags = tags_svc.list_tags()
    table = Table(title="Tags")
    table.add_column("Name")
    table.add_column("Todos")
    for t in tags:
        table.add_row(t.name, str(t.todo_count))
    console.print(table)


@tag_app.command("add")
def tag_add(
    todo_id: int = typer.Argument(...),
    names: list[str] = typer.Argument(..., help="Tag names"),
):
    """Add tags to a todo."""
    if get_todo_by_id(todo_id) is None:
        typer.echo(f"Todo #{todo_id} not found", err=True)
        raise typer.Exit(1)
    tags_svc.add_tags_to_todo(todo_id, names)
    typer.echo(f"Added tags to #{todo_id}: {', '.join(names)}")
