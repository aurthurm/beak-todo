"""API request/response models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.ai.schemas import (
    ActionPreviewResponse,
    BrainDumpResponse,
    ChatResponse,
    ParsedTask,
    PlanResponse,
    TodoPatchProposal,
)


class ExternalSourceOut(BaseModel):
    provider: str = "github"
    organisation: str
    repository: str
    item_type: str
    item_number: int
    state: str
    url: str


class TodoOut(BaseModel):
    id: int
    message: str
    priority: int
    priority_label: str
    priority_color: str
    category: str
    completed: bool
    due_date: Optional[str] = None
    sort_order: int = 0
    source_type: str = "local"
    external: Optional[ExternalSourceOut] = None
    tags: list[str] = []
    display_source: Optional[str] = None


class TodoCreate(BaseModel):
    message: str
    priority: int = 0
    category: str = "General"
    due_date: Optional[str] = None


class TodoPatch(BaseModel):
    message: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0, le=3)
    category: Optional[str] = None
    due_date: Optional[str] = None
    clear_due: bool = False
    completed: Optional[bool] = None
    sort_order: Optional[int] = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]


class NoteOut(BaseModel):
    id: int
    todo_id: int
    content: str
    created_at: str


class NoteCreate(BaseModel):
    content: str


class CategoryOut(BaseModel):
    id: int
    name: str
    todo_count: int


class BrainDumpRequest(BaseModel):
    text: str
    provider: Optional[str] = None


class BrainDumpApplyRequest(BaseModel):
    tasks: list[ParsedTask]


class BrainDumpApplyResponse(BaseModel):
    ids: list[int]


class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None


class PlanRequest(BaseModel):
    horizon: str = "today"
    provider: Optional[str] = None


class ActionPreviewRequest(BaseModel):
    request: str
    provider: Optional[str] = None


class ActionApplyRequest(BaseModel):
    patches: list[TodoPatchProposal]


class ActionApplyResponse(BaseModel):
    applied: int


class HealthResponse(BaseModel):
    status: str
    ai_enabled: bool
    config_path: str


class TagOut(BaseModel):
    id: int
    name: str
    todo_count: int


class TagsUpdate(BaseModel):
    tags: list[str]


class ExternalLinkRequest(BaseModel):
    url: str


class GitHubSyncResponse(BaseModel):
    created: int
    updated: int
    pushed: int
    errors: list[str]


class GitHubSourcesResponse(BaseModel):
    organisations: dict[str, list[dict]]


class GitHubStatusResponse(BaseModel):
    configured_repos: int
    sources_in_db: int
    last_errors: list[str] = []


class WeeklyReportGenerateRequest(BaseModel):
    date_from: Optional[str] = Field(default=None, alias="from")
    date_to: Optional[str] = Field(default=None, alias="to")
    use_ai: bool = True
    provider: Optional[str] = None

    model_config = {"populate_by_name": True}


class ReportDraftOut(BaseModel):
    id: int
    report_type: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    subject: str
    body_text: str
    body_html: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    sent_at: Optional[str] = None


class SendEmailRequest(BaseModel):
    to: Optional[str] = None
    force: bool = False


class EmailSendOut(BaseModel):
    id: int
    report_id: Optional[int] = None
    provider_message_id: Optional[str] = None
    status: str
    recipient: str
    error_message: Optional[str] = None
    sent_at: Optional[str] = None


class ReportHistoryOut(BaseModel):
    reports: list[ReportDraftOut]


class EmailHistoryOut(BaseModel):
    sends: list[EmailSendOut]


class EmailStatusOut(BaseModel):
    ok: bool
    messages: list[str]


class EmailConfigOut(BaseModel):
    provider: str
    from_address: str
    default_to: str
    send_mode: str
