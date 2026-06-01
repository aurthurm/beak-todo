"""Telegram Bot API HTTP client."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.channels.schemas import InlineButton
from src.channels.telegram.config import get_bot_token

API_BASE = "https://api.telegram.org/bot{token}"


class TelegramClient:
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or get_bot_token()
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    def _url(self, method: str) -> str:
        return API_BASE.format(token=self.token) + f"/{method}"

    def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(self._url(method), json=payload)
            resp.raise_for_status()
            data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "Telegram API error"))
        return data

    def get_me(self) -> dict[str, Any]:
        return self._post("getMe", {})["result"]

    def get_updates(
        self, offset: int, timeout: int
    ) -> list[dict[str, Any]]:
        data = self._post(
            "getUpdates",
            {"offset": offset, "timeout": timeout, "allowed_updates": ["message", "callback_query"]},
        )
        return data.get("result", [])

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        parse_mode: Optional[str] = None,
        inline_keyboard: Optional[list[list[InlineButton]]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if inline_keyboard:
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [{"text": b.text, "callback_data": b.callback_data} for b in row]
                    for row in inline_keyboard
                ]
            }
        return self._post("sendMessage", payload)["result"]

    def answer_callback_query(
        self, callback_query_id: str, text: Optional[str] = None
    ) -> None:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        self._post("answerCallbackQuery", payload)
