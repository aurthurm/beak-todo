"""Channel command and reply models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class InternalCommand:
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    channel: str = "telegram"
    channel_user_id: str = ""
    raw_text: str = ""


@dataclass
class InlineButton:
    text: str
    callback_data: str


@dataclass
class ChannelReply:
    text: str
    parse_mode: Optional[str] = None
    inline_keyboard: list[list[InlineButton]] = field(default_factory=list)
