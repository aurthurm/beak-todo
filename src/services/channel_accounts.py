"""Channel account linking (Telegram user ids, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.db.connection import get_db_connection


@dataclass
class ChannelAccount:
    id: int
    channel: str
    channel_user_id: str
    display_name: Optional[str]
    linked_user_id: Optional[int]


def upsert_account(
    channel: str,
    channel_user_id: str,
    display_name: Optional[str] = None,
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO channel_accounts (channel, channel_user_id, display_name)
        VALUES (?, ?, ?)
        ON CONFLICT(channel, channel_user_id) DO UPDATE SET
            display_name = COALESCE(excluded.display_name, display_name)
        """,
        (channel, channel_user_id, display_name),
    )
    cursor.execute(
        "SELECT id FROM channel_accounts WHERE channel = ? AND channel_user_id = ?",
        (channel, channel_user_id),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row[0]


def get_account(channel: str, channel_user_id: str) -> Optional[ChannelAccount]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, channel, channel_user_id, display_name, linked_user_id
        FROM channel_accounts WHERE channel = ? AND channel_user_id = ?
        """,
        (channel, channel_user_id),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return ChannelAccount(
        id=row[0],
        channel=row[1],
        channel_user_id=row[2],
        display_name=row[3],
        linked_user_id=row[4],
    )
