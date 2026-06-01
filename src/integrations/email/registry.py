"""Email provider registry."""

from __future__ import annotations

from src.config import get_email_config
from src.integrations.email.base import EmailProvider
from src.integrations.email.resend_provider import ResendProvider

_PROVIDERS: dict[str, type[ResendProvider]] = {
    "resend": ResendProvider,
}


def get_email_provider(name: str | None = None) -> EmailProvider:
    cfg = get_email_config()
    key = (name or cfg.provider or "resend").lower()
    cls = _PROVIDERS.get(key)
    if cls is None:
        raise ValueError(f"Unknown email provider: {key}")
    return cls()
