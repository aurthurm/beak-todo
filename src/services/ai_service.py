"""AI operations shared by CLI and API."""

from __future__ import annotations

from typing import Optional

from src.ai import prompts
from src.ai.client import complete_json
from src.ai.resolver import resolve_provider
from src.ai.schemas import (
    ActionPreviewResponse,
    BrainDumpResponse,
    BreakdownResponse,
    ChatResponse,
    ParsedTask,
    PlanResponse,
    RisksResponse,
    SearchRewrite,
    SummaryResponse,
)
from src.config import get_ai_config
from src.services.todos import (
    create_todo,
    fetch_open_todos_for_planning,
    fetch_stats_snapshot,
    list_category_names,
    query_todos,
    update_todo,
    validate_due_date,
)
from src.ai.schemas import TodoPatchProposal


def _provider(override: Optional[str] = None):
    ai_cfg = get_ai_config()
    if not ai_cfg.enabled:
        raise RuntimeError("AI is disabled in config")
    return resolve_provider(override)[0]


def parse_single_task(text: str, provider: Optional[str] = None) -> ParsedTask:
    prov = _provider(provider)
    categories = list_category_names()
    messages = [
        {"role": "system", "content": prompts.parse_task_system(categories)},
        {"role": "user", "content": prompts.parse_task_user(text)},
    ]
    return complete_json(prov, messages, ParsedTask)


def brain_dump(text: str, provider: Optional[str] = None) -> BrainDumpResponse:
    prov = _provider(provider)
    categories = list_category_names()
    messages = [
        {"role": "system", "content": prompts.brain_dump_system(categories)},
        {"role": "user", "content": prompts.brain_dump_user(text)},
    ]
    return complete_json(prov, messages, BrainDumpResponse)


def apply_parsed_tasks(tasks: list[ParsedTask]) -> list[int]:
    ids = []
    for t in tasks:
        due = None
        if t.due_date:
            due = validate_due_date(t.due_date)
        ids.append(create_todo(t.message, t.priority, t.category, due))
    return ids


def plan(horizon: str = "today", provider: Optional[str] = None) -> PlanResponse:
    prov = _provider(provider)
    days = {"today": 1, "tomorrow": 2, "week": 7}.get(horizon, 7)
    tasks = fetch_open_todos_for_planning(horizon_days=days)
    messages = [
        {"role": "system", "content": prompts.plan_system()},
        {"role": "user", "content": prompts.plan_user(tasks, horizon)},
    ]
    return complete_json(prov, messages, PlanResponse)


def summary(provider: Optional[str] = None) -> SummaryResponse:
    prov = _provider(provider)
    snap = fetch_stats_snapshot()
    messages = [
        {"role": "system", "content": prompts.summary_system()},
        {"role": "user", "content": prompts.summary_user(snap)},
    ]
    return complete_json(prov, messages, SummaryResponse)


def risks(provider: Optional[str] = None) -> RisksResponse:
    prov = _provider(provider)
    snap = fetch_stats_snapshot()
    signals = []
    if snap["overdue"] > 0:
        signals.append(f"{snap['overdue']} overdue tasks")
    if snap["critical_due_soon"] > 0:
        signals.append(f"{snap['critical_due_soon']} critical due within 2 days")
    if snap["high_no_due"] > 0:
        signals.append(f"{snap['high_no_due']} high-priority without due dates")
    messages = [
        {"role": "system", "content": prompts.risks_system()},
        {"role": "user", "content": prompts.risks_user(snap, signals)},
    ]
    return complete_json(prov, messages, RisksResponse)


def rewrite_search(query: str, provider: Optional[str] = None) -> SearchRewrite:
    prov = _provider(provider)
    messages = [
        {"role": "system", "content": prompts.search_system()},
        {"role": "user", "content": prompts.search_user(query)},
    ]
    return complete_json(prov, messages, SearchRewrite)


def breakdown(text: str, provider: Optional[str] = None) -> BreakdownResponse:
    prov = _provider(provider)
    categories = list_category_names()
    messages = [
        {"role": "system", "content": prompts.breakdown_system(categories)},
        {"role": "user", "content": prompts.breakdown_user(text)},
    ]
    return complete_json(prov, messages, BreakdownResponse)


def chat(message: str, provider: Optional[str] = None) -> ChatResponse:
    prov = _provider(provider)
    tasks = fetch_open_todos_for_planning(horizon_days=14)
    messages = [
        {"role": "system", "content": prompts.chat_system(tasks[:30])},
        {"role": "user", "content": prompts.chat_user(message)},
    ]
    return complete_json(prov, messages, ChatResponse)


def preview_actions(request: str, provider: Optional[str] = None) -> ActionPreviewResponse:
    prov = _provider(provider)
    open_tasks = [
        {"id": t.id, "message": t.message, "priority": t.priority, "due_date": t.due_date}
        for t in query_todos()
        if not t.completed
    ]
    messages = [
        {"role": "system", "content": prompts.action_preview_system(open_tasks)},
        {"role": "user", "content": prompts.action_preview_user(request)},
    ]
    return complete_json(prov, messages, ActionPreviewResponse)


def apply_action_patches(patches: list[TodoPatchProposal]) -> int:
    applied = 0
    for p in patches:
        ok = update_todo(
            p.todo_id,
            message=p.message,
            priority=p.priority,
            due=p.due_date,
            clear_due=p.clear_due,
            completed=p.completed,
        )
        if ok:
            applied += 1
    return applied
