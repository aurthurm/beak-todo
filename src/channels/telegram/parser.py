"""Parse Telegram text into InternalCommand."""

from __future__ import annotations

import re

from src.channels.schemas import InternalCommand

_COMMAND_RE = re.compile(r"^/(\w+)(?:@\w+)?(?:\s+(.*))?$", re.DOTALL)


def parse_message(
    text: str,
    channel_user_id: str,
    *,
    channel: str = "telegram",
) -> InternalCommand:
    text = (text or "").strip()
    if not text.startswith("/"):
        return InternalCommand(
            action="help",
            channel=channel,
            channel_user_id=channel_user_id,
            raw_text=text,
        )
    match = _COMMAND_RE.match(text)
    if not match:
        return InternalCommand(
            action="help",
            channel=channel,
            channel_user_id=channel_user_id,
            raw_text=text,
        )
    cmd, rest = match.group(1).lower(), (match.group(2) or "").strip()
    args: dict = {"text": rest} if rest else {}

    if cmd == "start":
        return InternalCommand("start", args, channel, channel_user_id, text)
    if cmd in ("help", "h"):
        return InternalCommand("help", {}, channel, channel_user_id, text)
    if cmd == "today":
        return InternalCommand("today", {}, channel, channel_user_id, text)
    if cmd == "add":
        return InternalCommand("add", {"text": rest}, channel, channel_user_id, text)
    if cmd == "done":
        parts = rest.split()
        todo_id = parts[0] if parts else None
        return InternalCommand(
            "done", {"todo_id": todo_id}, channel, channel_user_id, text
        )
    if cmd == "dump":
        return InternalCommand("dump", {"text": rest}, channel, channel_user_id, text)
    if cmd == "plan":
        return InternalCommand("plan", {}, channel, channel_user_id, text)
    if cmd == "report":
        sub = rest.lower()
        if sub in ("weekly", "week", ""):
            return InternalCommand(
                "report_weekly", {}, channel, channel_user_id, text
            )
        return InternalCommand(
            "help",
            {},
            channel,
            channel_user_id,
            text,
        )
    if cmd == "email":
        if rest.lower().startswith("send"):
            return InternalCommand("email_send", {}, channel, channel_user_id, text)
        return InternalCommand("help", {}, channel, channel_user_id, text)
    if cmd == "github":
        if rest.lower() == "sync":
            return InternalCommand("github_sync", {}, channel, channel_user_id, text)
        return InternalCommand("github_open", {}, channel, channel_user_id, text)
    return InternalCommand("help", {}, channel, channel_user_id, text)


def parse_callback(
    data: str, channel_user_id: str, *, channel: str = "telegram"
) -> InternalCommand:
    if data.startswith("confirm:"):
        return InternalCommand(
            "confirm",
            {"pending_id": data.split(":", 1)[1]},
            channel,
            channel_user_id,
            data,
        )
    if data.startswith("cancel:"):
        return InternalCommand(
            "cancel",
            {"pending_id": data.split(":", 1)[1]},
            channel,
            channel_user_id,
            data,
        )
    return InternalCommand("help", {}, channel, channel_user_id, data)
