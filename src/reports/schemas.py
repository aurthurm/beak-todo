"""Report data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportPeriod:
    start: str  # YYYY-MM-DD
    end: str


@dataclass
class ReportLineItem:
    text: str
    url: Optional[str] = None
    source: Optional[str] = None


@dataclass
class ReportSection:
    title: str
    items: list[ReportLineItem] = field(default_factory=list)


@dataclass
class ReportContext:
    period: ReportPeriod
    sections: list[ReportSection] = field(default_factory=list)


@dataclass
class WeeklyReportContent:
    subject: str
    body_text: str
    body_html: str
    period: ReportPeriod
