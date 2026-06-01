"""Email configuration helpers."""

from __future__ import annotations

import os

from src.config import EmailConfig, get_email_config


def get_resend_api_key() -> str:
    return os.environ.get("RESEND_API_KEY", "").strip()


def load_email_settings() -> EmailConfig:
    return get_email_config()
