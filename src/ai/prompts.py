"""Prompt templates for AI commands."""

from __future__ import annotations

import datetime
import json
from typing import Any


def today_iso() -> str:
    return datetime.datetime.now().date().isoformat()


def parse_task_system(categories: list[str]) -> str:
    cats = ", ".join(categories) if categories else "General, Work, Personal"
    return f"""You extract structured todo fields from natural language.
Today is {today_iso()} (use for relative dates like Friday, tomorrow, next week).

Rules:
- message: short actionable title, no filler words
- priority: 0=Low, 1=Medium, 2=High, 3=Critical (urgent/asap/production/demo -> 3)
- category: prefer one of: {cats}. Create a sensible new name only if none fit.
- due_date: YYYY-MM-DD or null. Resolve relative dates from today.

Respond with valid JSON only matching the schema."""


def parse_task_user(text: str) -> str:
    return f"Parse this todo:\n{text}"


def plan_system() -> str:
    return """You are a productivity planner. Given open tasks, suggest a focused ordered plan.
Reference task ids when suggesting existing tasks. Add rationale briefly.
Respond with valid JSON only."""


def plan_user(tasks: list[dict[str, Any]], horizon: str) -> str:
    return f"Horizon: {horizon}\n\nOpen tasks:\n{json.dumps(tasks, indent=2)}"


def summary_system() -> str:
    return "Summarize todo workload for the user. Be concise and actionable. JSON only."


def summary_user(snapshot: dict[str, Any]) -> str:
    return f"Stats snapshot:\n{json.dumps(snapshot, indent=2, default=str)}"


def risks_system() -> str:
    return """Identify deadline and workload risks from the snapshot.
severity: high, medium, or low. JSON only."""


def risks_user(snapshot: dict[str, Any], signals: list[str]) -> str:
    return f"Signals:\n{chr(10).join(signals)}\n\nSnapshot:\n{json.dumps(snapshot, indent=2, default=str)}"


def search_system() -> str:
    return """Rewrite natural language search into keywords and optional filters.
keywords: list of terms for SQL LIKE search. JSON only."""


def search_user(query: str) -> str:
    return f"Search query: {query}"


def breakdown_system(categories: list[str]) -> str:
    cats = ", ".join(categories) if categories else "General, Work"
    return f"""Break a large task into 4-8 concrete subtasks.
category: prefer {cats}. priority 0-3. JSON only."""


def breakdown_user(text: str) -> str:
    return f"Break down:\n{text}"


def chat_system(tasks: list[dict[str, Any]]) -> str:
    return f"""You are a read-only todo assistant. Today is {today_iso()}.
Suggest actions but do not claim you modified data. Context tasks:
{json.dumps(tasks, indent=2)}"""


def chat_user(message: str) -> str:
    return message


def brain_dump_system(categories: list[str]) -> str:
    cats = ", ".join(categories) if categories else "General, Work, Personal"
    return f"""Split messy brain-dump text into multiple structured todos.
Today is {today_iso()}.

Each task needs: message, priority (0-3), category (prefer: {cats}), due_date (YYYY-MM-DD or null).
One thought per line or bullet in the input may become one task.
Respond with JSON: {{ "tasks": [ ... ] }} only."""


def brain_dump_user(text: str) -> str:
    return f"Brain dump:\n{text}"


def action_preview_system(tasks_context: list[dict[str, Any]]) -> str:
    return f"""Propose todo changes as patches. Today is {today_iso()}.
Open tasks context:
{json.dumps(tasks_context[:40], indent=2)}

Return JSON with description and patches (todo_id, due_date, clear_due, priority, completed).
Only suggest changes that match the user request. Do not invent todo ids."""


def action_preview_user(request: str) -> str:
    return f"User request: {request}"


def harness_json_instruction(schema_name: str) -> str:
    return f"Respond with ONLY valid JSON for schema {schema_name}. No markdown, no explanation."


def weekly_report_system() -> str:
    return f"""You write professional weekly work update emails for a manager.
Today is {today_iso()}.

Rules:
- Use ONLY facts from the provided context JSON. Do not invent tasks, GitHub items, or outcomes.
- Preserve GitHub references exactly (organisation/repo#issue or #PR numbers and URLs when given).
- Professional, concise tone. Use bullet lists for sections that have items.
- If a section has no items in context, omit it or say briefly that there were none.
- Include a short greeting and sign-off in body_text.
- body_html should mirror body_text with simple HTML (paragraphs and ul/li), no external CSS.

Respond with JSON: subject, body_text, body_html (optional)."""


def weekly_report_user(context: dict[str, Any]) -> str:
    return f"Report period and collected work context:\n{json.dumps(context, indent=2)}"
