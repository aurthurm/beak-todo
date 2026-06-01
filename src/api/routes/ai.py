from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    ActionApplyRequest,
    ActionApplyResponse,
    ActionPreviewRequest,
    BrainDumpApplyRequest,
    BrainDumpApplyResponse,
    BrainDumpRequest,
    ChatRequest,
    PlanRequest,
)
from src.ai.schemas import (
    ActionPreviewResponse,
    BrainDumpResponse,
    ChatResponse,
    PlanResponse,
    RisksResponse,
    SummaryResponse,
)
from src.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


def _ai_error(e: Exception):
    raise HTTPException(503, str(e)) from e


@router.post("/brain-dump", response_model=BrainDumpResponse)
def brain_dump(body: BrainDumpRequest):
    try:
        return ai_service.brain_dump(body.text, body.provider)
    except Exception as e:
        _ai_error(e)


@router.post("/brain-dump/apply", response_model=BrainDumpApplyResponse)
def brain_dump_apply(body: BrainDumpApplyRequest):
    ids = ai_service.apply_parsed_tasks(body.tasks)
    return BrainDumpApplyResponse(ids=ids)


@router.post("/plan", response_model=PlanResponse)
def ai_plan(body: PlanRequest):
    try:
        return ai_service.plan(body.horizon, body.provider)
    except Exception as e:
        _ai_error(e)


@router.post("/summary", response_model=SummaryResponse)
def ai_summary(provider: str | None = None):
    try:
        return ai_service.summary(provider)
    except Exception as e:
        _ai_error(e)


@router.post("/risks", response_model=RisksResponse)
def ai_risks(provider: str | None = None):
    try:
        return ai_service.risks(provider)
    except Exception as e:
        _ai_error(e)


@router.post("/chat", response_model=ChatResponse)
def ai_chat(body: ChatRequest):
    try:
        return ai_service.chat(body.message, body.provider)
    except Exception as e:
        _ai_error(e)


@router.post("/actions/preview", response_model=ActionPreviewResponse)
def actions_preview(body: ActionPreviewRequest):
    try:
        return ai_service.preview_actions(body.request, body.provider)
    except Exception as e:
        _ai_error(e)


@router.post("/actions/apply", response_model=ActionApplyResponse)
def actions_apply(body: ActionApplyRequest):
    applied = ai_service.apply_action_patches(body.patches)
    return ActionApplyResponse(applied=applied)
