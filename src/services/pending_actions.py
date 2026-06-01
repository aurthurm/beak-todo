"""Pending confirmation actions for channels."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.db.connection import get_db_connection


@dataclass
class PendingAction:
    id: int
    channel: str
    channel_user_id: str
    action_type: str
    payload: dict[str, Any]
    expires_at: Optional[str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_pending(
    channel: str,
    channel_user_id: str,
    action_type: str,
    payload: dict[str, Any],
    *,
    ttl_minutes: int = 60,
) -> int:
    expires = (
        datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    ).replace(microsecond=0).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO pending_actions (
            channel, channel_user_id, action_type, payload_json, expires_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (channel, channel_user_id, action_type, json.dumps(payload), expires),
    )
    action_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return action_id


def get_pending(action_id: int) -> Optional[PendingAction]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, channel, channel_user_id, action_type, payload_json, expires_at
        FROM pending_actions WHERE id = ?
        """,
        (action_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    if row[5]:
        try:
            exp = datetime.fromisoformat(row[5].replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < datetime.now(timezone.utc):
                delete_pending(action_id)
                return None
        except ValueError:
            pass
    return PendingAction(
        id=row[0],
        channel=row[1],
        channel_user_id=row[2],
        action_type=row[3],
        payload=json.loads(row[4]),
        expires_at=row[5],
    )


def delete_pending(action_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_actions WHERE id = ?", (action_id,))
    conn.commit()
    conn.close()
