"""Route channel commands to services."""

from __future__ import annotations

from typing import Any, Optional

from src.ai.schemas import ParsedTask
from src.channels import formatters
from src.channels.schemas import ChannelReply, InlineButton, InternalCommand
from src.config import get_email_config, get_telegram_config
from src.db.connection import get_db_connection
from src.integrations.email.draft import DraftSendError, get_current_draft, send_draft
from src.integrations.registry import get_integration
from src.services import ai_service
from src.services import pending_actions as pending_db
from src.services.report_service import generate_weekly
from src.services.todos import (
    ListFilters,
    PRIORITIES,
    create_todo,
    fetch_by_due_date,
    query_todos,
    update_todo,
    validate_due_date,
)

HELP_TEXT = """Beak Todo bot — commands:

/start — link account & show your Telegram user id
/today — tasks due today and overdue
/add <text> — add a task (AI parses priority/due)
/done <id> — mark task complete
/dump <text> — brain dump → tasks (confirm)
/plan — AI focus plan for today
/report weekly — draft weekly email report
/email send — send current report draft (confirm)
/github — open GitHub issues/PRs
/help — this message"""


def dispatch(cmd: InternalCommand) -> ChannelReply:
    action = cmd.action
    if action == "help":
        return ChannelReply(text=HELP_TEXT)
    if action == "start":
        return _handle_start(cmd)
    if action == "today":
        return _handle_today()
    if action == "add":
        return _handle_add(cmd)
    if action == "done":
        return _handle_done(cmd)
    if action == "dump":
        return _handle_dump(cmd)
    if action == "plan":
        return _handle_plan()
    if action == "report_weekly":
        return _handle_report_weekly()
    if action == "email_send":
        return _handle_email_send(cmd)
    if action == "github_open":
        return _handle_github_open()
    if action == "github_sync":
        return _handle_github_sync(cmd)
    if action == "confirm":
        return _handle_confirm(cmd)
    if action == "cancel":
        return _handle_cancel(cmd)
    return ChannelReply(text=f"Unknown action: {action}\n\n{HELP_TEXT}")


def _handle_start(cmd: InternalCommand) -> ChannelReply:
    from src.services.channel_accounts import upsert_account

    name = cmd.args.get("display_name", "")
    upsert_account(cmd.channel, cmd.channel_user_id, name or None)
    cfg = get_telegram_config()
    allowed = int(cmd.channel_user_id) in cfg.allowed_user_ids
    lines = [
        f"Hello{', ' + name if name else ''}!",
        f"Your Telegram user id: {cmd.channel_user_id}",
        "",
    ]
    if allowed:
        lines.append("You are on the allowlist. Use /help for commands.")
    else:
        lines.append(
            "Add this id to [telegram].allowed_user_ids in ~/.todos/config.toml, "
            "then restart the bot."
        )
    return ChannelReply(text="\n".join(lines))


def _handle_today() -> ChannelReply:
    today = __import__("datetime").date.today().isoformat()
    due_today = fetch_by_due_date(today)
    due_today = [t for t in due_today if not t.completed]
    overdue = query_todos(ListFilters(overdue=True, undone=True))
    text = formatters.format_today_list(due_today, overdue)
    return ChannelReply(text=formatters.truncate(text))


def _handle_add(cmd: InternalCommand) -> ChannelReply:
    text = (cmd.args.get("text") or "").strip()
    if not text:
        return ChannelReply(text="Usage: /add <task description>")
    try:
        parsed = ai_service.parse_single_task(text)
        due = validate_due_date(parsed.due_date) if parsed.due_date else None
        todo_id = create_todo(parsed.message, parsed.priority, parsed.category, due)
        prio = PRIORITIES.get(parsed.priority, ("?", ""))[0]
        due_s = f" due {due}" if due else ""
        return ChannelReply(
            text=f"Added #{todo_id}: {parsed.message} ({prio}{due_s})"
        )
    except Exception as exc:
        todo_id = create_todo(text, 0, "General", None)
        return ChannelReply(
            text=f"Added #{todo_id}: {text} (AI parse skipped: {exc})"
        )


def _handle_done(cmd: InternalCommand) -> ChannelReply:
    raw_id = cmd.args.get("todo_id")
    if raw_id is None:
        return ChannelReply(text="Usage: /done <task id>")
    try:
        todo_id = int(raw_id)
    except (TypeError, ValueError):
        return ChannelReply(text="Task id must be a number.")
    if not update_todo(todo_id, completed=True):
        return ChannelReply(text=f"Task #{todo_id} not found.")
    return ChannelReply(text=f"Marked #{todo_id} complete.")


def _handle_dump(cmd: InternalCommand) -> ChannelReply:
    text = (cmd.args.get("text") or "").strip()
    if not text:
        return ChannelReply(text="Usage: /dump <messy notes>")
    try:
        result = ai_service.brain_dump(text)
    except Exception as exc:
        return ChannelReply(text=f"Brain dump failed: {exc}")
    tasks = [
        {
            "message": t.message,
            "priority": t.priority,
            "priority_label": PRIORITIES.get(t.priority, ("?", ""))[0],
            "category": t.category,
            "due_date": t.due_date,
        }
        for t in result.tasks
    ]
    if not tasks:
        return ChannelReply(text="No tasks found in that text.")
    payload = {
        "tasks": [
            {
                "message": t.message,
                "priority": t.priority,
                "category": t.category,
                "due_date": t.due_date,
            }
            for t in result.tasks
        ]
    }
    pending_id = pending_db.create_pending(
        cmd.channel, cmd.channel_user_id, "brain_dump_apply", payload
    )
    preview = formatters.format_brain_dump_preview(tasks)
    return ChannelReply(
        text=preview,
        inline_keyboard=[
            [
                InlineButton("Create", f"confirm:{pending_id}"),
                InlineButton("Cancel", f"cancel:{pending_id}"),
            ]
        ],
    )


def _handle_plan() -> ChannelReply:
    try:
        result = ai_service.plan("today")
    except Exception as exc:
        return ChannelReply(text=f"Plan failed: {exc}")
    items = [
        {"title": i.title, "rationale": i.rationale} for i in result.items
    ]
    text = formatters.format_plan_summary(result.summary, items)
    return ChannelReply(text=formatters.truncate(text))


def _handle_report_weekly() -> ChannelReply:
    try:
        content, report_id = generate_weekly(save_draft=True, use_ai=True)
    except Exception as exc:
        return ChannelReply(text=f"Report failed: {exc}")
    body_preview = content.body_text[:2500]
    if len(content.body_text) > 2500:
        body_preview += "\n…"
    text = (
        f"Draft report #{report_id}\n\n"
        f"Subject: {content.subject}\n\n"
        f"{body_preview}\n\n"
        "Send with /email send (confirmation required)."
    )
    return ChannelReply(text=formatters.truncate(text))


def _handle_email_send(cmd: InternalCommand) -> ChannelReply:
    draft = get_current_draft()
    if not draft:
        return ChannelReply(text="No draft report. Run /report weekly first.")
    cfg = get_email_config()
    to_addr = (cmd.args.get("to") or cfg.default_to or "").strip()
    if not to_addr:
        return ChannelReply(
            text="Set [email].default_to in config or use /email send after setting recipient."
        )
    tg_cfg = get_telegram_config()
    if tg_cfg.confirm_email_send:
        pending_id = pending_db.create_pending(
            cmd.channel,
            cmd.channel_user_id,
            "email_send",
            {"to": to_addr, "report_id": draft.id},
        )
        return ChannelReply(
            text=f"Send report draft to {to_addr}?",
            inline_keyboard=[
                [
                    InlineButton("Send", f"confirm:{pending_id}"),
                    InlineButton("Cancel", f"cancel:{pending_id}"),
                ]
            ],
        )
    try:
        message_id, _ = send_draft(to_addr, force=True)
        return ChannelReply(text=f"Sent (message_id={message_id})")
    except (DraftSendError, Exception) as exc:
        return ChannelReply(text=f"Send failed: {exc}")


def _list_open_github_items(limit: int = 20) -> list[tuple]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ei.title, ei.item_type, ei.item_number, ei.state, ei.url,
               es.organisation, es.repository
        FROM external_items ei
        JOIN external_sources es ON ei.source_id = es.id
        WHERE es.provider = 'github' AND ei.state = 'open'
        ORDER BY es.organisation, es.repository, ei.item_number DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def _handle_github_open() -> ChannelReply:
    rows = _list_open_github_items()
    if not rows:
        return ChannelReply(
            text="No open GitHub items in DB. Run: t integrations github sync"
        )
    lines = ["Open GitHub items:", ""]
    for title, itype, num, state, url, org, repo in rows:
        lines.append(f"• {org}/{repo} {itype} #{num}: {title[:60]}")
        lines.append(f"  {url}")
    return ChannelReply(text=formatters.truncate("\n".join(lines)))


def _handle_github_sync(cmd: InternalCommand) -> ChannelReply:
    tg_cfg = get_telegram_config()
    if tg_cfg.confirm_github_sync:
        pending_id = pending_db.create_pending(
            cmd.channel, cmd.channel_user_id, "github_sync", {}
        )
        return ChannelReply(
            text="Run GitHub sync now?",
            inline_keyboard=[
                [
                    InlineButton("Sync", f"confirm:{pending_id}"),
                    InlineButton("Cancel", f"cancel:{pending_id}"),
                ]
            ],
        )
    return _run_github_sync()


def _run_github_sync() -> ChannelReply:
    try:
        gh = get_integration("github")
        result = gh.sync()
        return ChannelReply(
            text=(
                f"Sync done: created={result.created}, "
                f"updated={result.updated}, pushed={result.pushed}"
            )
        )
    except Exception as exc:
        return ChannelReply(text=f"Sync failed: {exc}")


def _handle_confirm(cmd: InternalCommand) -> ChannelReply:
    action_id = cmd.args.get("pending_id")
    if action_id is None:
        return ChannelReply(text="Invalid confirmation.")
    try:
        pid = int(action_id)
    except (TypeError, ValueError):
        return ChannelReply(text="Invalid confirmation id.")
    pending = pending_db.get_pending(pid)
    if not pending:
        return ChannelReply(text="Confirmation expired or not found.")
    if pending.channel_user_id != cmd.channel_user_id:
        return ChannelReply(text="Not your confirmation.")
    pending_db.delete_pending(pid)
    if pending.action_type == "brain_dump_apply":
        tasks = [ParsedTask(**t) for t in pending.payload.get("tasks", [])]
        ids = ai_service.apply_parsed_tasks(tasks)
        return ChannelReply(text=f"Created {len(ids)} task(s): {', '.join(f'#{i}' for i in ids)}")
    if pending.action_type == "email_send":
        to_addr = pending.payload.get("to", "")
        try:
            message_id, _ = send_draft(to_addr, force=True)
            return ChannelReply(text=f"Email sent (message_id={message_id})")
        except Exception as exc:
            return ChannelReply(text=f"Send failed: {exc}")
    if pending.action_type == "github_sync":
        return _run_github_sync()
    return ChannelReply(text=f"Unknown pending action: {pending.action_type}")


def _handle_cancel(cmd: InternalCommand) -> ChannelReply:
    action_id = cmd.args.get("pending_id")
    if action_id is not None:
        try:
            pending_db.delete_pending(int(action_id))
        except (TypeError, ValueError):
            pass
    return ChannelReply(text="Cancelled.")
