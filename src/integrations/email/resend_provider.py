"""Resend email provider."""

from __future__ import annotations

from typing import Optional

from src.integrations.email.base import DoctorResult
from src.integrations.email.config import get_resend_api_key, load_email_settings


class ResendProvider:
    name = "resend"

    def doctor(self) -> DoctorResult:
        messages: list[str] = []
        ok = True
        key = get_resend_api_key()
        if not key:
            ok = False
            messages.append("RESEND_API_KEY is not set")
        else:
            messages.append("RESEND_API_KEY is set")

        cfg = load_email_settings()
        if not cfg.from_address:
            ok = False
            messages.append("[email].from is not configured")
        else:
            messages.append(f"From: {cfg.from_address}")

        if not cfg.default_to:
            messages.append("default_to is empty (override with --to when sending)")
        else:
            messages.append(f"default_to: {cfg.default_to}")

        return DoctorResult(ok=ok, messages=messages)

    def send(
        self,
        *,
        to: list[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_address: Optional[str] = None,
    ) -> str:
        import resend

        key = get_resend_api_key()
        if not key:
            raise RuntimeError("RESEND_API_KEY is not set")

        cfg = load_email_settings()
        sender = from_address or cfg.from_address
        if not sender:
            raise RuntimeError("[email].from is not configured")

        resend.api_key = key
        params: dict = {
            "from": sender,
            "to": to,
            "subject": subject,
            "html": html,
        }
        if text:
            params["text"] = text

        response = resend.Emails.send(params)
        if isinstance(response, dict):
            return str(response.get("id", ""))
        return str(getattr(response, "id", response))
