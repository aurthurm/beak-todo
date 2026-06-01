"""Format service data for channel replies."""

from __future__ import annotations

import datetime

from src.services.todos import PRIORITIES, TodoRecord


def format_today_header() -> str:
    today = datetime.date.today()
    label = today.strftime("%A, %d %b %Y")
    return f"Today — {label}"


def format_todo_line(index: int, todo: TodoRecord, *, suffix: str = "") -> str:
    prio = PRIORITIES.get(todo.priority, ("?", ""))[0]
    due = f" [due {todo.due_date}]" if todo.due_date else ""
    src = f" ({todo.display_source})" if todo.display_source else ""
    extra = f" {suffix}" if suffix else ""
    return f"{index}. {todo.message} — {prio}{due}{src}{extra}"


def format_today_list(due_today: list[TodoRecord], overdue: list[TodoRecord]) -> str:
    lines = [format_today_header(), ""]
    if due_today:
        lines.append("Due today")
        for i, t in enumerate(due_today[:15], 1):
            lines.append(format_todo_line(i, t))
        lines.append("")
    if overdue:
        lines.append("Overdue")
        start = 1
        for i, t in enumerate(overdue[:15], start):
            lines.append(format_todo_line(i, t, suffix="[overdue]"))
        lines.append("")
    if not due_today and not overdue:
        lines.append("No tasks due today or overdue. Nice work!")
    else:
        lines.append("Reply: /done <id>")
    return "\n".join(lines).strip()


def format_brain_dump_preview(tasks: list[dict]) -> str:
    lines = [f"I found {len(tasks)} task(s):", ""]
    for i, t in enumerate(tasks, 1):
        due = f" — due {t['due_date']}" if t.get("due_date") else ""
        lines.append(
            f"{i}. {t['message']} — {t.get('priority_label', '')} — "
            f"{t.get('category', 'General')}{due}"
        )
    lines.append("")
    lines.append("Create these tasks?")
    return "\n".join(lines)


def format_plan_summary(summary: str, items: list[dict]) -> str:
    lines = [summary or "Plan", ""]
    for i, item in enumerate(items[:10], 1):
        rationale = f" — {item['rationale']}" if item.get("rationale") else ""
        lines.append(f"{i}. {item['title']}{rationale}")
    return "\n".join(lines).strip()


def truncate(text: str, max_len: int = 4000) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
