"""Email CLI (Resend)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.integrations.email.draft import (
    DraftSendError,
    cancel_draft,
    get_current_draft,
    send_draft,
    send_one_off,
)
from src.integrations.email.registry import get_email_provider
from src.services import reports as reports_db
from src.services.report_service import generate_weekly

console = Console()
email_app = typer.Typer(help="Email via Resend (draft-first)")


@email_app.command("doctor")
def email_doctor():
    """Check Resend API key and email configuration."""
    provider = get_email_provider()
    result = provider.doctor()
    for msg in result.messages:
        typer.echo(msg)
    if not result.ok:
        raise typer.Exit(1)
    typer.echo("Email configuration looks OK.")


@email_app.command("draft")
def email_draft_weekly(
    weekly: bool = typer.Option(True, "--weekly/--no-weekly", help="Weekly report draft"),
    date_from: Optional[str] = typer.Option(None, "--from"),
    date_to: Optional[str] = typer.Option(None, "--to", help="Period end YYYY-MM-DD"),
    no_ai: bool = typer.Option(False, "--no-ai"),
):
    """Generate and save a weekly report draft."""
    if not weekly:
        typer.echo("Only weekly drafts are supported in v1")
        raise typer.Exit(1)
    content, report_id = generate_weekly(
        date_from,
        date_to,
        use_ai=not no_ai,
        save_draft=True,
    )
    console.print(Panel(content.subject, title=f"Draft #{report_id}", border_style="cyan"))
    console.print(Panel(content.body_text, title="Body"))
    typer.echo("Approve with: t email send-draft")


@email_app.command("show-draft")
def email_show_draft():
    """Show the current email draft."""
    draft = get_current_draft()
    if not draft:
        typer.echo("No draft report.")
        raise typer.Exit(1)
    console.print(Panel(draft.subject, title=f"Draft #{draft.id}", border_style="cyan"))
    console.print(Panel(draft.body_text, title="Body"))


@email_app.command("send-draft")
def email_send_draft(
    to: Optional[str] = typer.Option(None, "--to"),
    force: bool = typer.Option(False, "--force", help="Bypass draft_first guard"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Send the current draft via Resend."""
    draft = get_current_draft()
    if not draft:
        typer.echo("No draft to send.")
        raise typer.Exit(1)
    if not yes:
        console.print(Panel(draft.subject, title="Will send"))
        console.print(draft.body_text[:500] + ("…" if len(draft.body_text) > 500 else ""))
        if not typer.confirm("Send this email?"):
            raise typer.Exit(0)
    try:
        message_id, send_id = send_draft(to, force=force)
    except DraftSendError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Send failed: {exc}")
        raise typer.Exit(1)
    typer.echo(f"Sent (message_id={message_id}, email_send #{send_id})")


@email_app.command("send")
def email_send(
    to: str = typer.Option(..., "--to"),
    subject: str = typer.Option(..., "--subject"),
    body_file: Path = typer.Option(..., "--body-file", exists=True),
    force: bool = typer.Option(False, "--force"),
    yes: bool = typer.Option(False, "--yes", "-y"),
):
    """Send a one-off email from a text file."""
    body = body_file.read_text(encoding="utf-8")
    if not yes and not typer.confirm(f"Send to {to}?"):
        raise typer.Exit(0)
    try:
        message_id = send_one_off(
            to=[to],
            subject=subject,
            body_text=body,
            force=force or yes,
        )
    except DraftSendError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1)
    typer.echo(f"Sent (message_id={message_id})")


@email_app.command("history")
def email_history(limit: int = typer.Option(20, "--limit")):
    """List recent email sends."""
    sends = reports_db.list_email_sends(limit=limit)
    if not sends:
        typer.echo("No sends yet.")
        return
    table = Table(title="Email history")
    table.add_column("ID")
    table.add_column("Report")
    table.add_column("To")
    table.add_column("Status")
    table.add_column("Message ID")
    for s in sends:
        table.add_row(
            str(s.id),
            str(s.report_id or ""),
            s.recipient,
            s.status,
            s.provider_message_id or "",
        )
    console.print(table)


@email_app.command("cancel-draft")
def email_cancel_draft():
    """Cancel the current draft."""
    n = cancel_draft()
    typer.echo(f"Cancelled {n} draft(s).")
