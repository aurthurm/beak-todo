"""AI and deterministic weekly report generation."""

from __future__ import annotations

from typing import Any, Optional

from src.ai import prompts
from src.ai.client import complete_json
from src.ai.resolver import resolve_provider
from src.ai.schemas import WeeklyReportDraft
from src.config import get_ai_config
from src.reports.collector import collect_weekly_context
from src.reports.formatters import context_to_weekly_content
from src.reports.schemas import ReportContext, WeeklyReportContent


def context_to_dict(ctx: ReportContext) -> dict[str, Any]:
    return {
        "period": {"start": ctx.period.start, "end": ctx.period.end},
        "sections": [
            {
                "title": s.title,
                "items": [
                    {
                        "text": i.text,
                        "url": i.url,
                        "source": i.source,
                    }
                    for i in s.items
                ],
            }
            for s in ctx.sections
        ],
    }


def generate_weekly_content(
    period_start: str,
    period_end: str,
    *,
    use_ai: bool = True,
    provider: Optional[str] = None,
) -> WeeklyReportContent:
    ctx = collect_weekly_context(period_start, period_end)
    if not use_ai:
        return context_to_weekly_content(ctx)

    ai_cfg = get_ai_config()
    if not ai_cfg.enabled:
        return context_to_weekly_content(ctx)

    prov, _info = resolve_provider(provider)
    messages = [
        {"role": "system", "content": prompts.weekly_report_system()},
        {"role": "user", "content": prompts.weekly_report_user(context_to_dict(ctx))},
    ]
    draft = complete_json(prov, messages, WeeklyReportDraft)
    body_html = draft.body_html or context_to_weekly_content(ctx).body_html
    return WeeklyReportContent(
        subject=draft.subject,
        body_text=draft.body_text,
        body_html=body_html,
        period=ctx.period,
    )
