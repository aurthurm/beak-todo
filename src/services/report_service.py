"""Orchestrate weekly report generation and draft persistence."""

from __future__ import annotations

from typing import Optional

from src.reports.collector import default_weekly_period
from src.reports.generator import generate_weekly_content
from src.reports.schemas import WeeklyReportContent
from src.services import reports as reports_db


def generate_weekly(
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    *,
    use_ai: bool = True,
    provider: Optional[str] = None,
    save_draft: bool = False,
) -> tuple[WeeklyReportContent, Optional[int]]:
    if not period_start or not period_end:
        period = default_weekly_period()
        period_start = period.start
        period_end = period.end

    content = generate_weekly_content(
        period_start,
        period_end,
        use_ai=use_ai,
        provider=provider,
    )
    report_id: Optional[int] = None
    if save_draft:
        report_id = reports_db.create_report(
            "weekly",
            period_start,
            period_end,
            content.subject,
            content.body_text,
            content.body_html,
        )
    return content, report_id
