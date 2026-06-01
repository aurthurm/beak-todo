"""Collect report data from todos, GitHub links, and notes."""

from __future__ import annotations

import datetime
from typing import Optional

from src.config import WeeklyReportConfig, get_weekly_report_config
from src.db.connection import get_db_connection
from src.integrations.github.display import format_display_source
from src.reports.schemas import ReportContext, ReportLineItem, ReportPeriod, ReportSection
from src.services.todos import fetch_open_todos_for_planning


def default_weekly_period() -> ReportPeriod:
    today = datetime.date.today()
    start = today - datetime.timedelta(days=6)
    return ReportPeriod(start=start.isoformat(), end=today.isoformat())


def collect_weekly_context(
    period_start: str,
    period_end: str,
    cfg: Optional[WeeklyReportConfig] = None,
) -> ReportContext:
    cfg = cfg or get_weekly_report_config()
    period = ReportPeriod(start=period_start, end=period_end)
    sections: list[ReportSection] = []

    if cfg.include_completed_tasks:
        sections.append(
            ReportSection(
                title="Completed this period",
                items=_completed_in_period(period_start, period_end),
            )
        )

    if cfg.include_blockers:
        sections.append(
            ReportSection(title="Blockers / overdue", items=_blockers())
        )

    gh_items: list[ReportLineItem] = []
    if cfg.include_github_issues or cfg.include_github_prs:
        gh_items = _github_activity(
            period_start,
            period_end,
            include_issues=cfg.include_github_issues,
            include_prs=cfg.include_github_prs,
        )
    if gh_items:
        sections.append(ReportSection(title="GitHub activity", items=gh_items))

    notes_items = _notes_in_period(period_start, period_end)
    if notes_items:
        sections.append(ReportSection(title="Notes added", items=notes_items))

    if cfg.include_next_week_plan:
        sections.append(
            ReportSection(
                title="Upcoming priorities",
                items=_next_week_items(),
            )
        )

    return ReportContext(period=period, sections=sections)


def _completed_in_period(start: str, end: str) -> list[ReportLineItem]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.id, t.message, t.completed_at, t.updated_at,
               es.organisation, es.repository, ei.item_type, ei.item_number, ei.url
        FROM todos t
        LEFT JOIN todo_external_links tel ON t.id = tel.todo_id
        LEFT JOIN external_items ei ON tel.external_item_id = ei.id
        LEFT JOIN external_sources es ON ei.source_id = es.id
        WHERE t.completed = 1
          AND (
            (t.completed_at IS NOT NULL AND date(t.completed_at) >= date(?) AND date(t.completed_at) <= date(?))
            OR (t.completed_at IS NULL AND date(t.updated_at) >= date(?) AND date(t.updated_at) <= date(?))
          )
        ORDER BY COALESCE(t.completed_at, t.updated_at) DESC
        """,
        (start, end, start, end),
    )
    rows = cursor.fetchall()
    conn.close()
    items: list[ReportLineItem] = []
    for row in rows:
        msg, org, repo, itype, num, url = row[1], row[4], row[5], row[6], row[7], row[8]
        source = None
        if org and repo and itype and num:
            source = format_display_source(org, repo, itype, int(num))
            text = f"{msg} ({source})"
        else:
            text = msg
        items.append(ReportLineItem(text=text, url=url, source=source))
    return items


def _blockers() -> list[ReportLineItem]:
    today = datetime.date.today().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT t.message
        FROM todos t
        LEFT JOIN todo_tags tt ON t.id = tt.todo_id
        LEFT JOIN tags tg ON tt.tag_id = tg.id
        WHERE t.completed = 0
          AND (
            tg.name = 'blocked' COLLATE NOCASE
            OR (t.due_date IS NOT NULL AND t.due_date < ? AND t.priority >= 2)
          )
        ORDER BY t.priority DESC, t.due_date
        LIMIT 15
        """,
        (today,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [ReportLineItem(text=r[0]) for r in rows]


def _github_activity(
    start: str,
    end: str,
    *,
    include_issues: bool,
    include_prs: bool,
) -> list[ReportLineItem]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ei.title, ei.item_type, ei.item_number, ei.state, ei.url,
               es.organisation, es.repository, ei.updated_at_remote
        FROM external_items ei
        JOIN external_sources es ON ei.source_id = es.id
        WHERE es.provider = 'github'
          AND (
            date(COALESCE(ei.last_synced_at, ei.updated_at_remote, '1970-01-01')) >= date(?)
            AND date(COALESCE(ei.last_synced_at, ei.updated_at_remote, '1970-01-01')) <= date(?)
          )
        ORDER BY es.organisation, es.repository, ei.item_number DESC
        """,
        (start, end),
    )
    rows = cursor.fetchall()
    conn.close()
    items: list[ReportLineItem] = []
    for title, itype, num, state, url, org, repo, _ in rows:
        if itype == "issue" and not include_issues:
            continue
        if itype == "pr" and not include_prs:
            continue
        source = format_display_source(org, repo, itype, int(num))
        items.append(
            ReportLineItem(
                text=f"{title} [{state}] ({source})",
                url=url,
                source=source,
            )
        )
    return items


def _notes_in_period(start: str, end: str) -> list[ReportLineItem]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT n.content, t.message
        FROM notes n
        JOIN todos t ON n.todo_id = t.id
        WHERE date(n.created_at) >= date(?) AND date(n.created_at) <= date(?)
        ORDER BY n.created_at DESC
        LIMIT 20
        """,
        (start, end),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        ReportLineItem(text=f"{row[1]}: {row[0][:120]}")
        for row in rows
    ]


def _next_week_items() -> list[ReportLineItem]:
    items: list[ReportLineItem] = []
    for row in fetch_open_todos_for_planning(horizon_days=7)[:10]:
        due = f" (due {row['due_date']})" if row.get("due_date") else ""
        overdue = " [overdue]" if row.get("overdue") else ""
        items.append(
            ReportLineItem(
                text=f"{row['message']}{due}{overdue} — {row.get('priority_label', '')}"
            )
        )
    return items
