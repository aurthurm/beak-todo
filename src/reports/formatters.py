"""Deterministic report formatting."""

from __future__ import annotations

import html
from datetime import datetime

from src.reports.schemas import ReportContext, WeeklyReportContent


def _format_period_label(period_start: str, period_end: str) -> str:
    try:
        s = datetime.fromisoformat(period_start).strftime("%d %b %Y")
        e = datetime.fromisoformat(period_end).strftime("%d %b %Y")
        return f"{s} – {e}"
    except ValueError:
        return f"{period_start} – {period_end}"


def format_context_as_text(ctx: ReportContext) -> str:
    lines: list[str] = []
    period_label = _format_period_label(ctx.period.start, ctx.period.end)
    lines.append(f"Weekly Work Update: {period_label}")
    lines.append("")
    lines.append("Hello,")
    lines.append("")
    for section in ctx.sections:
        if not section.items:
            continue
        lines.append(f"{section.title}:")
        for item in section.items:
            line = f"- {item.text}"
            if item.url:
                line += f" ({item.url})"
            lines.append(line)
        lines.append("")
    lines.append("Regards,")
    return "\n".join(lines).strip() + "\n"


def format_context_as_html(ctx: ReportContext) -> str:
    period_label = _format_period_label(ctx.period.start, ctx.period.end)
    parts = [
        "<html><body style='font-family:sans-serif;line-height:1.5'>",
        f"<p>Hello,</p>",
    ]
    for section in ctx.sections:
        if not section.items:
            continue
        parts.append(f"<h3>{html.escape(section.title)}</h3><ul>")
        for item in section.items:
            text = html.escape(item.text)
            if item.url:
                parts.append(
                    f"<li><a href=\"{html.escape(item.url)}\">{text}</a></li>"
                )
            else:
                parts.append(f"<li>{text}</li>")
        parts.append("</ul>")
    parts.append("<p>Regards,</p></body></html>")
    return "".join(parts)


def context_to_weekly_content(ctx: ReportContext) -> WeeklyReportContent:
    period_label = _format_period_label(ctx.period.start, ctx.period.end)
    subject = f"Weekly Work Update: {period_label}"
    body_text = format_context_as_text(ctx)
    body_html = format_context_as_html(ctx)
    return WeeklyReportContent(
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        period=ctx.period,
    )
