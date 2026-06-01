"""Optional audit log for channel messages."""

from __future__ import annotations

from typing import Optional

from src.db.connection import get_db_connection


def log_message(
    channel: str,
    channel_user_id: str,
    direction: str,
    message_text: Optional[str] = None,
    action_type: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO channel_messages (
            channel, channel_user_id, direction, message_text, action_type, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (channel, channel_user_id, direction, message_text, action_type, status),
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id
