"""Pydantic schemas for AI structured outputs."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ParsedTask(BaseModel):
    message: str = Field(description="Concise actionable task title")
    priority: int = Field(ge=0, le=3, description="0=Low, 1=Medium, 2=High, 3=Critical")
    category: str = Field(description="Category name")
    due_date: Optional[str] = Field(
        default=None,
        description="Due date as YYYY-MM-DD or null",
    )


class PlanItem(BaseModel):
    task_id: Optional[int] = Field(default=None, description="Existing todo id if applicable")
    title: str = Field(description="What to do")
    rationale: str = Field(default="", description="Brief why")


class PlanResponse(BaseModel):
    horizon: str = Field(description="today, tomorrow, or week")
    items: list[PlanItem] = Field(default_factory=list)
    summary: str = Field(default="", description="One-line focus for the period")


class SearchRewrite(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    priority_min: Optional[int] = Field(default=None, ge=0, le=3)
    due_within_days: Optional[int] = Field(default=None, ge=0)
    incomplete_only: bool = Field(default=True)


class SummaryResponse(BaseModel):
    narrative: str = Field(description="Short summary paragraph")
    suggested_focus: str = Field(default="")


class RiskItem(BaseModel):
    severity: str = Field(description="high, medium, or low")
    description: str = Field(description="Risk description")


class RisksResponse(BaseModel):
    risks: list[RiskItem] = Field(default_factory=list)


class BreakdownResponse(BaseModel):
    parent_title: str
    category: str
    priority: int = Field(ge=0, le=3)
    subtasks: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str = Field(description="Assistant reply")


class BrainDumpResponse(BaseModel):
    tasks: list[ParsedTask] = Field(default_factory=list)


class TodoPatchProposal(BaseModel):
    todo_id: int
    due_date: Optional[str] = None
    clear_due: bool = False
    priority: Optional[int] = Field(default=None, ge=0, le=3)
    completed: Optional[bool] = None
    message: Optional[str] = None


class ActionPreviewResponse(BaseModel):
    description: str
    patches: list[TodoPatchProposal] = Field(default_factory=list)


class WeeklyReportDraft(BaseModel):
    subject: str = Field(description="Email subject line")
    body_text: str = Field(description="Plain-text email body")
    body_html: Optional[str] = Field(
        default=None,
        description="Optional HTML body; plain text is required",
    )
