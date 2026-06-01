"""Report and email send persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.db.connection import get_db_connection


@dataclass
class ReportRecord:
    id: int
    report_type: str
    period_start: Optional[str]
    period_end: Optional[str]
    subject: str
    body_text: str
    body_html: Optional[str]
    status: str
    created_at: Optional[str]
    sent_at: Optional[str]


@dataclass
class EmailSendRecord:
    id: int
    report_id: Optional[int]
    provider: str
    recipient: str
    provider_message_id: Optional[str]
    status: str
    error_message: Optional[str]
    sent_at: Optional[str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _report_row(row: tuple) -> ReportRecord:
    return ReportRecord(
        id=row[0],
        report_type=row[1],
        period_start=row[2],
        period_end=row[3],
        subject=row[4],
        body_text=row[5],
        body_html=row[6],
        status=row[7],
        created_at=row[8],
        sent_at=row[9],
    )


def create_report(
    report_type: str,
    period_start: str,
    period_end: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    *,
    status: str = "draft",
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reports SET status = 'cancelled' WHERE status = 'draft'"
    )
    cursor.execute(
        """
        INSERT INTO reports (
            report_type, period_start, period_end, subject, body_text, body_html, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (report_type, period_start, period_end, subject, body_text, body_html, status),
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_report(report_id: int) -> Optional[ReportRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, report_type, period_start, period_end, subject, body_text,
               body_html, status, created_at, sent_at
        FROM reports WHERE id = ?
        """,
        (report_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _report_row(row) if row else None


def get_current_draft() -> Optional[ReportRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, report_type, period_start, period_end, subject, body_text,
               body_html, status, created_at, sent_at
        FROM reports WHERE status = 'draft'
        ORDER BY id DESC LIMIT 1
        """
    )
    row = cursor.fetchone()
    conn.close()
    return _report_row(row) if row else None


def cancel_drafts() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reports SET status = 'cancelled' WHERE status = 'draft'"
    )
    n = cursor.rowcount
    conn.commit()
    conn.close()
    return n


def mark_report_sent(report_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _utc_now()
    cursor.execute(
        "UPDATE reports SET status = 'sent', sent_at = ? WHERE id = ?",
        (now, report_id),
    )
    conn.commit()
    conn.close()


def list_reports(limit: int = 20) -> list[ReportRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, report_type, period_start, period_end, subject, body_text,
               body_html, status, created_at, sent_at
        FROM reports ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_report_row(r) for r in rows]


def record_email_send(
    report_id: Optional[int],
    provider: str,
    recipient: str,
    provider_message_id: Optional[str],
    status: str,
    error_message: Optional[str] = None,
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _utc_now()
    cursor.execute(
        """
        INSERT INTO email_sends (
            report_id, provider, recipient, provider_message_id, status,
            error_message, sent_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            provider,
            recipient,
            provider_message_id,
            status,
            error_message,
            now if status == "sent" else None,
        ),
    )
    send_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return send_id


def list_email_sends(limit: int = 20) -> list[EmailSendRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, report_id, provider, recipient, provider_message_id,
               status, error_message, sent_at
        FROM email_sends ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        EmailSendRecord(
            id=r[0],
            report_id=r[1],
            provider=r[2],
            recipient=r[3],
            provider_message_id=r[4],
            status=r[5],
            error_message=r[6],
            sent_at=r[7],
        )
        for r in rows
    ]
