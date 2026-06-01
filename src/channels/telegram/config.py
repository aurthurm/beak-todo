"""Telegram channel configuration."""

from __future__ import annotations

import os

from src.config import get_telegram_config
from src.todos import get_data_dir


def get_bot_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def get_offset_path():
    return get_data_dir() / "telegram-offset.txt"


def load_telegram_settings():
    return get_telegram_config()
