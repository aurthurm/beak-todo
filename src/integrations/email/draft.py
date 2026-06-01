"""Draft-first email workflow."""

from __future__ import annotations

from typing import Optional

from src.config import get_email_config
from src.integrations.email.registry import get_email_provider
from src.services import reports as reports_db


class DraftSendError(Exception):
    pass


def get_current_draft() -> Optional[reports_db.ReportRecord]:
    return reports_db.get_current_draft()


def send_draft(
    recipient: Optional[str] = None,
    *,
    force: bool = False,
) -> tuple[str, int]:
    """Send current draft. Returns (provider_message_id, email_send_id)."""
    cfg = get_email_config()
    if cfg.send_mode == "draft_first" and not force:
        draft = reports_db.get_current_draft()
        if draft is None:
            raise DraftSendError("No draft report to send. Run `t email draft weekly` first.")

    draft = reports_db.get_current_draft()
    if draft is None:
        raise DraftSendError("No draft report to send")

    to_addr = (recipient or cfg.default_to or "").strip()
    if not to_addr:
        raise DraftSendError("Recipient required: set [email].default_to or pass --to")

    provider = get_email_provider(cfg.provider)
    html = draft.body_html or f"<pre>{draft.body_text}</pre>"
    try:
        message_id = provider.send(
            to=[to_addr],
            subject=draft.subject,
            html=html,
            text=draft.body_text,
        )
        send_id = reports_db.record_email_send(
            draft.id,
            provider.name,
            to_addr,
            message_id,
            "sent",
        )
        reports_db.mark_report_sent(draft.id)
        return message_id, send_id
    except Exception as exc:
        reports_db.record_email_send(
            draft.id,
            provider.name,
            to_addr,
            None,
            "failed",
            str(exc),
        )
        raise


def send_one_off(
    *,
    to: list[str],
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    force: bool = False,
) -> str:
    cfg = get_email_config()
    if cfg.send_mode == "draft_first" and not force:
        raise DraftSendError(
            "Direct send blocked in draft_first mode. Use --force or send-draft."
        )
    provider = get_email_provider(cfg.provider)
    html = body_html or f"<pre>{body_text}</pre>"
    return provider.send(to=to, subject=subject, html=html, text=body_text)


def cancel_draft() -> int:
    return reports_db.cancel_drafts()
