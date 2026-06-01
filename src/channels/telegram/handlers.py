"""Process Telegram updates through dispatcher."""

from __future__ import annotations

from typing import Any, Optional

from src.channels.dispatcher import dispatch
from src.channels.schemas import ChannelReply
from src.channels.telegram.parser import parse_callback, parse_message
from src.config import get_telegram_config
from src.services.channel_log import log_message


def is_user_allowed(user_id: int, *, command: str) -> bool:
    if command == "start":
        return True
    cfg = get_telegram_config()
    return user_id in cfg.allowed_user_ids


def _user_from_update(update: dict[str, Any]) -> tuple[Optional[int], Optional[str]]:
    if "message" in update:
        user = update["message"].get("from") or {}
        return user.get("id"), user.get("first_name")
    if "callback_query" in update:
        user = update["callback_query"].get("from") or {}
        return user.get("id"), user.get("first_name")
    return None, None


def _chat_id(update: dict[str, Any]) -> Optional[int]:
    if "message" in update:
        return update["message"].get("chat", {}).get("id")
    if "callback_query" in update:
        msg = update["callback_query"].get("message") or {}
        return msg.get("chat", {}).get("id")
    return None


def handle_update(update: dict[str, Any]) -> Optional[tuple[int, ChannelReply, Optional[str]]]:
    """
    Returns (chat_id, reply, callback_query_id) or None if ignored.
    """
    user_id, first_name = _user_from_update(update)
    if user_id is None:
        return None
    chat_id = _chat_id(update)
    if chat_id is None:
        return None

    channel_user_id = str(user_id)
    callback_id: Optional[str] = None

    if "callback_query" in update:
        cq = update["callback_query"]
        callback_id = cq.get("id")
        data = cq.get("data") or ""
        cmd = parse_callback(data, channel_user_id)
        log_message("telegram", channel_user_id, "in", data, cmd.action)
    elif "message" in update:
        msg = update["message"]
        text = msg.get("text") or ""
        if not text:
            return None
        cmd = parse_message(text, channel_user_id)
        if cmd.action == "start":
            cmd.args["display_name"] = first_name
        log_message("telegram", channel_user_id, "in", text, cmd.action)
    else:
        return None

    if not is_user_allowed(user_id, command=cmd.action):
        reply = ChannelReply(
            text=(
                f"Access denied. Your user id is {user_id}.\n"
                "Add it to [telegram].allowed_user_ids in ~/.todos/config.toml "
                "and run /start again."
            )
        )
        return chat_id, reply, callback_id

    reply = dispatch(cmd)
    log_message(
        "telegram",
        channel_user_id,
        "out",
        reply.text[:500],
        cmd.action,
        "ok",
    )
    return chat_id, reply, callback_id
