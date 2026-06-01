"""Reports and email API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    EmailConfigOut,
    EmailHistoryOut,
    EmailSendOut,
    EmailStatusOut,
    ReportDraftOut,
    ReportHistoryOut,
    SendEmailRequest,
    WeeklyReportGenerateRequest,
)
from src.config import get_email_config
from src.integrations.email.draft import (
    DraftSendError,
    cancel_draft,
    get_current_draft,
    send_draft,
)
from src.integrations.email.registry import get_email_provider
from src.reports.collector import default_weekly_period
from src.services import reports as reports_db
from src.services.report_service import generate_weekly

router = APIRouter(tags=["reports"])


def _draft_out(record: reports_db.ReportRecord) -> ReportDraftOut:
    return ReportDraftOut(
        id=record.id,
        report_type=record.report_type,
        period_start=record.period_start,
        period_end=record.period_end,
        subject=record.subject,
        body_text=record.body_text,
        body_html=record.body_html,
        status=record.status,
        created_at=record.created_at,
        sent_at=record.sent_at,
    )


@router.post("/reports/weekly/generate", response_model=ReportDraftOut)
def generate_weekly_report(body: WeeklyReportGenerateRequest):
    start = body.date_from
    end = body.date_to
    if not start or not end:
        period = default_weekly_period()
        start = start or period.start
        end = end or period.end
    _content, report_id = generate_weekly(
        start,
        end,
        use_ai=body.use_ai,
        provider=body.provider,
        save_draft=True,
    )
    if report_id is None:
        raise HTTPException(500, "Failed to save draft")
    record = reports_db.get_report(report_id)
    if not record:
        raise HTTPException(500, "Draft not found after save")
    return _draft_out(record)


@router.get("/reports/draft", response_model=Optional[ReportDraftOut])
def get_draft():
    draft = get_current_draft()
    return _draft_out(draft) if draft else None


@router.post("/reports/draft/send", response_model=EmailSendOut)
def send_draft_email(body: SendEmailRequest):
    try:
        message_id, send_id = send_draft(body.to, force=body.force)
    except DraftSendError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, str(exc)) from exc
    sends = reports_db.list_email_sends(limit=1)
    send = sends[0] if sends and sends[0].id == send_id else None
    return EmailSendOut(
        id=send_id,
        report_id=send.report_id if send else None,
        provider_message_id=message_id,
        status="sent",
        recipient=body.to or get_email_config().default_to,
    )


@router.delete("/reports/draft", status_code=204)
def delete_draft():
    cancel_draft()


@router.get("/reports/history", response_model=ReportHistoryOut)
def report_history(limit: int = 20):
    reports = reports_db.list_reports(limit=limit)
    return ReportHistoryOut(
        reports=[
            ReportDraftOut(
                id=r.id,
                report_type=r.report_type,
                period_start=r.period_start,
                period_end=r.period_end,
                subject=r.subject,
                body_text=r.body_text,
                body_html=r.body_html,
                status=r.status,
                created_at=r.created_at,
                sent_at=r.sent_at,
            )
            for r in reports
        ]
    )


@router.get("/email/status", response_model=EmailStatusOut)
def email_status():
    provider = get_email_provider()
    result = provider.doctor()
    return EmailStatusOut(ok=result.ok, messages=result.messages)


@router.get("/email/config", response_model=EmailConfigOut)
def email_config():
    cfg = get_email_config()
    return EmailConfigOut(
        provider=cfg.provider,
        from_address=cfg.from_address,
        default_to=cfg.default_to,
        send_mode=cfg.send_mode,
    )


@router.get("/email/history", response_model=EmailHistoryOut)
def email_history(limit: int = 20):
    sends = reports_db.list_email_sends(limit=limit)
    return EmailHistoryOut(
        sends=[
            EmailSendOut(
                id=s.id,
                report_id=s.report_id,
                provider_message_id=s.provider_message_id,
                status=s.status,
                recipient=s.recipient,
                error_message=s.error_message,
                sent_at=s.sent_at,
            )
            for s in sends
        ]
    )
