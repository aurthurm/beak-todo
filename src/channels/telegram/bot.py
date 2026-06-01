"""Long-polling Telegram bot runner."""

from __future__ import annotations

import logging
import time

from src.channels.telegram.client import TelegramClient
from src.channels.telegram.config import get_offset_path, load_telegram_settings
from src.channels.telegram.handlers import handle_update
from src.db.connection import ensure_db

log = logging.getLogger(__name__)


def read_offset() -> int:
    path = get_offset_path()
    if not path.exists():
        return 0
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return 0


def write_offset(offset: int) -> None:
    path = get_offset_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(offset), encoding="utf-8")


def run_polling(*, once: bool = False) -> None:
    ensure_db()
    cfg = load_telegram_settings()
    client = TelegramClient()
    me = client.get_me()
    log.info("Telegram bot @%s (%s)", me.get("username"), me.get("id"))

    offset = read_offset()
    while True:
        try:
            updates = client.get_updates(offset, cfg.poll_timeout_seconds)
        except Exception as exc:
            log.error("getUpdates failed: %s", exc)
            time.sleep(5)
            if once:
                raise
            continue

        for update in updates:
            update_id = update.get("update_id", 0)
            offset = max(offset, update_id + 1)
            result = handle_update(update)
            if not result:
                continue
            chat_id, reply, callback_id = result
            try:
                if callback_id:
                    client.answer_callback_query(callback_id)
                client.send_message(
                    chat_id,
                    reply.text,
                    parse_mode=reply.parse_mode,
                    inline_keyboard=reply.inline_keyboard or None,
                )
            except Exception as exc:
                log.error("send failed: %s", exc)

        if updates:
            write_offset(offset)

        if once:
            break
