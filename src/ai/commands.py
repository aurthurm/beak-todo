"""AI Typer commands."""

from __future__ import annotations

import json
from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from src.ai import prompts
from src.ai.client import complete_json
from src.ai.resolver import (
    detect_api_keys,
    detect_harnesses,
    maybe_show_provider,
    peek_auto_resolution,
    resolve_provider,
)
from src.ai.schemas import (
    BreakdownResponse,
    ChatResponse,
    ParsedTask,
    PlanResponse,
    RisksResponse,
    SearchRewrite,
    SummaryResponse,
    WeeklyReportDraft,
)
from src.config import (
    ALLOWED_PROVIDERS,
    ensure_default_config,
    get_ai_config,
    get_config_path,
    set_config_value,
)
from src.todos import (
    PRIORITIES,
    create_todo,
    fetch_open_todos_for_planning,
    fetch_stats_snapshot,
    format_due_date,
    list_category_names,
    search_todos,
    validate_due_date,
)

console = Console()
provider_app = typer.Typer(help="Manage AI provider settings")


class PlanHorizon(str, Enum):
    today = "today"
    tomorrow = "tomorrow"
    week = "week"


HORIZON_DAYS = {"today": 1, "tomorrow": 2, "week": 7}


def _resolve_and_show(override: Optional[str], verbose: bool):
    provider, info = resolve_provider(override)
    maybe_show_provider(info)
    return provider


def setup():
    """Create ~/.todos/ and default config.toml."""
    from src.todos import init_db

    init_db()
    path = ensure_default_config()
    typer.echo(f"Initialized config at {path}")
    typer.echo("\nSet an API key for direct mode (recommended):")
    typer.echo("  export OPENAI_API_KEY=...")
    typer.echo("  export ANTHROPIC_API_KEY=...")
    typer.echo("  export GOOGLE_API_KEY=...")
    typer.echo("\nOr use harness mode (explicit):")
    typer.echo("  t ai provider set codex")
    typer.echo("\nRun `t ai doctor` to verify setup.")


def doctor():
    """Show AI configuration and availability."""
    path = get_config_path()
    ai_cfg = get_ai_config()
    keys = detect_api_keys()
    harnesses = detect_harnesses()

    typer.echo(f"Config: {path}")
    typer.echo(f"AI enabled: {ai_cfg.enabled}")
    typer.echo(f"Configured provider: {ai_cfg.provider}")
    typer.echo(f"Model: {ai_cfg.model}")

    typer.echo("\nDirect API keys:")
    for name, found in keys.items():
        typer.echo(f"  {name}: {'found' if found else 'not set'}")

    typer.echo("\nHarness CLIs:")
    for name, path_found in harnesses.items():
        typer.echo(f"  {name}: {path_found or 'not found'}")

    typer.echo(f"\nResolved for next command (auto): {peek_auto_resolution()}")


@provider_app.command("list")
def provider_list():
    """List allowed providers and current setting."""
    ai_cfg = get_ai_config()
    typer.echo("Allowed providers:")
    for p in sorted(ALLOWED_PROVIDERS):
        typer.echo(f"  - {p}")
    typer.echo(f"\nCurrent: {ai_cfg.provider}")
    typer.echo(f"Auto would use: {peek_auto_resolution()}")


@provider_app.command("set")
def provider_set(name: str):
    """Set AI provider (openai, anthropic, auto, codex, claude, none, ...)."""
    name = name.lower()
    if name not in ALLOWED_PROVIDERS:
        typer.echo(f"Unknown provider. Choose from: {', '.join(sorted(ALLOWED_PROVIDERS))}")
        raise typer.Exit(1)
    set_config_value("ai.provider", name)
    typer.echo(f"Set ai.provider to {name}")
    if name in ("codex", "claude"):
        typer.echo("Warning: harness mode may use subscription or API billing depending on your CLI setup.")


def add(
    text: str = typer.Argument(..., help="Natural language todo description"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without saving"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Override AI provider"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed errors"),
):
    """Add a todo from natural language."""
    ai_cfg = get_ai_config()
    if not ai_cfg.enabled:
        typer.echo("AI is disabled. Run `t config set ai.enabled true`")
        raise typer.Exit(1)

    prov = _resolve_and_show(provider, verbose)
    categories = list_category_names()

    messages = [
        {"role": "system", "content": prompts.parse_task_system(categories)},
        {"role": "user", "content": prompts.parse_task_user(text)},
    ]
    parsed = complete_json(prov, messages, ParsedTask, verbose=verbose)

    due_date = None
    if parsed.due_date:
        try:
            due_date = validate_due_date(parsed.due_date)
        except ValueError as e:
            typer.echo(str(e))
            raise typer.Exit(1)

    table = Table(title="Parsed task" if dry_run else "Added task")
    table.add_column("Field")
    table.add_column("Value")
    pname, pcolor = PRIORITIES[parsed.priority]
    table.add_row("Message", parsed.message)
    table.add_row("Priority", Text(pname, style=pcolor))
    table.add_row("Category", parsed.category)
    table.add_row("Due", format_due_date(due_date) or "(none)")
    console.print(table)

    if dry_run:
        typer.echo("(dry run — not saved)")
        return

    todo_id = create_todo(
        message=parsed.message,
        priority=parsed.priority,
        category=parsed.category,
        due_date=due_date,
    )
    typer.echo(f"Added todo #{todo_id}")


def plan(
    horizon: PlanHorizon = typer.Argument(PlanHorizon.today, help="Planning horizon"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """Suggest a focused plan from open tasks."""
    ai_cfg = get_ai_config()
    if not ai_cfg.enabled:
        typer.echo("AI is disabled.")
        raise typer.Exit(1)

    prov = _resolve_and_show(provider, verbose)
    days = HORIZON_DAYS[horizon.value]
    tasks = fetch_open_todos_for_planning(horizon_days=days)
    if not tasks:
        typer.echo("No open tasks to plan.")
        return

    messages = [
        {"role": "system", "content": prompts.plan_system()},
        {"role": "user", "content": prompts.plan_user(tasks, horizon.value)},
    ]
    result = complete_json(prov, messages, PlanResponse, verbose=verbose)

    typer.echo(f"\nSuggested plan ({horizon.value}):")
    if result.summary:
        typer.echo(result.summary)
        typer.echo("")
    for i, item in enumerate(result.items, 1):
        ref = f" [#{item.task_id}]" if item.task_id else ""
        typer.echo(f"  {i}. {item.title}{ref}")
        if item.rationale:
            typer.echo(f"     → {item.rationale}")


def summary(
    provider: Optional[str] = typer.Option(None, "--provider"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """AI narrative summary of your todos."""
    prov = _resolve_and_show(provider, verbose)
    snapshot = fetch_stats_snapshot()
    messages = [
        {"role": "system", "content": prompts.summary_system()},
        {"role": "user", "content": prompts.summary_user(snapshot)},
    ]
    result = complete_json(prov, messages, SummaryResponse, verbose=verbose)
    typer.echo(result.narrative)
    if result.suggested_focus:
        typer.echo(f"\nSuggested focus: {result.suggested_focus}")


def risks(
    provider: Optional[str] = typer.Option(None, "--provider"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """Detect deadline and workload risks."""
    prov = _resolve_and_show(provider, verbose)
    snapshot = fetch_stats_snapshot()
    signals = []
    if snapshot["overdue"] > 0:
        signals.append(f"{snapshot['overdue']} overdue incomplete tasks")
    if snapshot["critical_due_soon"] > 0:
        signals.append(f"{snapshot['critical_due_soon']} critical tasks due within 2 days")
    if snapshot["high_no_due"] > 0:
        signals.append(f"{snapshot['high_no_due']} high-priority tasks without due dates")
    if snapshot["critical_open"] > 0:
        signals.append(f"{snapshot['critical_open']} critical open tasks total")

    messages = [
        {"role": "system", "content": prompts.risks_system()},
        {"role": "user", "content": prompts.risks_user(snapshot, signals)},
    ]
    result = complete_json(prov, messages, RisksResponse, verbose=verbose)
    if not result.risks:
        typer.echo("No significant risks detected.")
        return
    for risk in result.risks:
        typer.echo(f"[{risk.severity.upper()}] {risk.description}")


def ai_search(
    query: str = typer.Argument(..., help="Natural language search query"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """Natural language search (LLM rewrites to keywords)."""
    prov = _resolve_and_show(provider, verbose)
    messages = [
        {"role": "system", "content": prompts.search_system()},
        {"role": "user", "content": prompts.search_user(query)},
    ]
    rewrite = complete_json(prov, messages, SearchRewrite, verbose=verbose)
    keywords = rewrite.keywords or [query]
    rows = search_todos(keywords)
    if not rows:
        typer.echo(f"No todos found for: {', '.join(keywords)}")
        return
    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Message")
    table.add_column("Priority")
    table.add_column("Category")
    table.add_column("Due")
    for todo_id, message, priority, category_name, completed, due_date in rows:
        if rewrite.incomplete_only and completed:
            continue
        if rewrite.priority_min is not None and priority < rewrite.priority_min:
            continue
        category_name = category_name or "General"
        pname, pcolor = PRIORITIES[priority]
        table.add_row(
            str(todo_id),
            message,
            Text(pname, style=pcolor),
            category_name,
            format_due_date(due_date),
        )
    console.print(table)


def breakdown(
    text: str = typer.Argument(..., help="Large task to break down"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """Break a large task into subtasks (flat todos)."""
    prov = _resolve_and_show(provider, verbose)
    categories = list_category_names()
    messages = [
        {"role": "system", "content": prompts.breakdown_system(categories)},
        {"role": "user", "content": prompts.breakdown_user(text)},
    ]
    result = complete_json(prov, messages, BreakdownResponse, verbose=verbose)

    typer.echo(f"Parent: {result.parent_title}")
    typer.echo(f"Category: {result.category} | Priority: {PRIORITIES[result.priority][0]}")
    typer.echo("\nSubtasks:")
    for i, sub in enumerate(result.subtasks, 1):
        label = f"[{result.parent_title[:30]}] {sub}" if len(result.parent_title) > 0 else sub
        typer.echo(f"  {i}. {sub}")
        if not dry_run:
            create_todo(
                message=label,
                priority=result.priority,
                category=result.category,
            )
    if dry_run:
        typer.echo("\n(dry run — not saved)")
    else:
        typer.echo(f"\nCreated {len(result.subtasks)} todos.")


def chat(
    provider: Optional[str] = typer.Option(None, "--provider"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """Read-only conversational assistant about your todos."""
    prov = _resolve_and_show(provider, verbose)
    typer.echo("Todo chat (read-only). Type 'exit' to quit.\n")
    while True:
        try:
            line = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nBye.")
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit", "q"):
            break
        tasks = fetch_open_todos_for_planning(horizon_days=14)
        messages = [
            {"role": "system", "content": prompts.chat_system(tasks[:30])},
            {"role": "user", "content": prompts.chat_user(line)},
        ]
        try:
            result = complete_json(prov, messages, ChatResponse, verbose=verbose)
            typer.echo(f"\nAssistant> {result.answer}\n")
        except Exception as e:
            typer.echo(f"Error: {e}\n")


def email(
    request: str = typer.Argument(..., help="How to adjust the weekly report draft"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    """Preview AI edits to a weekly report (does not send)."""
    from src.integrations.email.draft import get_current_draft
    from src.reports.collector import collect_weekly_context, default_weekly_period
    from src.reports.generator import context_to_dict
    from src.services.report_service import generate_weekly

    prov = _resolve_and_show(provider, verbose)
    draft = get_current_draft()
    if draft and draft.period_start and draft.period_end:
        ctx = collect_weekly_context(draft.period_start, draft.period_end)
        context = {
            "current_draft": {
                "subject": draft.subject,
                "body_text": draft.body_text,
            },
            "work_context": context_to_dict(ctx),
            "user_request": request,
        }
    else:
        period = default_weekly_period()
        content, _ = generate_weekly(period.start, period.end, use_ai=False, save_draft=False)
        context = {
            "current_draft": {"subject": content.subject, "body_text": content.body_text},
            "user_request": request,
        }

    messages = [
        {"role": "system", "content": prompts.weekly_report_system()},
        {
            "role": "user",
            "content": (
                "Revise the weekly report per the user request. "
                "Use only facts from work_context.\n"
                + json.dumps(context, indent=2)
            ),
        },
    ]
    result = complete_json(prov, messages, WeeklyReportDraft, verbose=verbose)
    console.print(Panel(result.subject, title="Preview subject", border_style="cyan"))
    console.print(Panel(result.body_text, title="Preview body"))
    typer.echo("\nTo save and send: t email draft weekly  (or edit draft) then t email send-draft")
