"""Weekly report CLI."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from src.reports.collector import default_weekly_period
from src.services.report_service import generate_weekly

console = Console()
report_app = typer.Typer(help="Work reports")


@report_app.command("weekly")
def report_weekly(
    date_from: Optional[str] = typer.Option(
        None, "--from", help="Period start YYYY-MM-DD"
    ),
    date_to: Optional[str] = typer.Option(
        None, "--to", help="Period end YYYY-MM-DD (inclusive)"
    ),
    no_ai: bool = typer.Option(False, "--no-ai", help="Deterministic bullets only"),
    save: bool = typer.Option(False, "--save", help="Save as email draft"),
    provider: Optional[str] = typer.Option(None, "--provider", help="AI provider override"),
):
    """Generate a weekly work report (default: last 7 days ending today)."""
    start = date_from
    end = date_to
    if not start or not end:
        period = default_weekly_period()
        start = start or period.start
        end = end or period.end

    content, report_id = generate_weekly(
        start,
        end,
        use_ai=not no_ai,
        provider=provider,
        save_draft=save,
    )
    console.print(Panel(content.subject, title="Subject", border_style="cyan"))
    console.print(Panel(content.body_text, title="Body", border_style="green"))
    if report_id:
        typer.echo(f"Saved draft report #{report_id}")
