"""External source / item / link service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.db.connection import get_db_connection


@dataclass
class ExternalSourceRecord:
    id: int
    provider: str
    organisation: str
    repository: str
    enabled: bool
    sync_issues: bool
    sync_prs: bool
    last_synced_at: Optional[str] = None


@dataclass
class ExternalItemRecord:
    id: int
    source_id: int
    item_type: str
    item_number: int
    github_id: Optional[str]
    title: str
    state: str
    url: str
    assignees_json: Optional[str]
    updated_at_remote: Optional[str]
    last_synced_at: Optional[str]
    organisation: str = ""
    repository: str = ""
    provider: str = "github"


@dataclass
class TodoExternalLink:
    todo_id: int
    external_item_id: int
    link_kind: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def upsert_source(
    provider: str,
    organisation: str,
    repository: str,
    *,
    enabled: bool = True,
    sync_issues: bool = True,
    sync_prs: bool = True,
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO external_sources (
            provider, organisation, repository, enabled, sync_issues, sync_prs
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(provider, organisation, repository) DO UPDATE SET
            enabled = excluded.enabled,
            sync_issues = excluded.sync_issues,
            sync_prs = excluded.sync_prs
        """,
        (provider, organisation, repository, int(enabled), int(sync_issues), int(sync_prs)),
    )
    cursor.execute(
        """
        SELECT id FROM external_sources
        WHERE provider = ? AND organisation = ? AND repository = ?
        """,
        (provider, organisation, repository),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row[0]


def get_source(
    provider: str, organisation: str, repository: str
) -> Optional[ExternalSourceRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, provider, organisation, repository, enabled,
               sync_issues, sync_prs, last_synced_at
        FROM external_sources
        WHERE provider = ? AND organisation = ? AND repository = ?
        """,
        (provider, organisation, repository),
    )
    row = cursor.fetchone()
    conn.close()
    return _source_row(row) if row else None


def _source_row(row: tuple) -> ExternalSourceRecord:
    return ExternalSourceRecord(
        id=row[0],
        provider=row[1],
        organisation=row[2],
        repository=row[3],
        enabled=bool(row[4]),
        sync_issues=bool(row[5]),
        sync_prs=bool(row[6]),
        last_synced_at=row[7],
    )


def list_sources(provider: Optional[str] = None) -> list[ExternalSourceRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if provider:
        cursor.execute(
            """
            SELECT id, provider, organisation, repository, enabled,
                   sync_issues, sync_prs, last_synced_at
            FROM external_sources WHERE provider = ?
            ORDER BY organisation, repository
            """,
            (provider,),
        )
    else:
        cursor.execute(
            """
            SELECT id, provider, organisation, repository, enabled,
                   sync_issues, sync_prs, last_synced_at
            FROM external_sources
            ORDER BY provider, organisation, repository
            """
        )
    rows = cursor.fetchall()
    conn.close()
    return [_source_row(r) for r in rows]


def touch_source_synced(source_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE external_sources SET last_synced_at = ? WHERE id = ?",
        (_utc_now(), source_id),
    )
    conn.commit()
    conn.close()


def upsert_item(
    source_id: int,
    item_type: str,
    item_number: int,
    title: str,
    state: str,
    url: str,
    *,
    github_id: Optional[str] = None,
    assignees: Optional[list[str]] = None,
    updated_at_remote: Optional[str] = None,
) -> int:
    assignees_json = json.dumps(assignees) if assignees else None
    now = _utc_now()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO external_items (
            source_id, item_type, item_number, github_id, title, state, url,
            assignees_json, updated_at_remote, last_synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id, item_type, item_number) DO UPDATE SET
            github_id = COALESCE(excluded.github_id, external_items.github_id),
            title = excluded.title,
            state = excluded.state,
            url = excluded.url,
            assignees_json = excluded.assignees_json,
            updated_at_remote = excluded.updated_at_remote,
            last_synced_at = excluded.last_synced_at
        """,
        (
            source_id,
            item_type,
            item_number,
            github_id,
            title,
            state,
            url,
            assignees_json,
            updated_at_remote,
            now,
        ),
    )
    cursor.execute(
        """
        SELECT id FROM external_items
        WHERE source_id = ? AND item_type = ? AND item_number = ?
        """,
        (source_id, item_type, item_number),
    )
    item_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return item_id


def get_item(item_id: int) -> Optional[ExternalItemRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ei.id, ei.source_id, ei.item_type, ei.item_number, ei.github_id,
               ei.title, ei.state, ei.url, ei.assignees_json,
               ei.updated_at_remote, ei.last_synced_at,
               es.organisation, es.repository, es.provider
        FROM external_items ei
        JOIN external_sources es ON ei.source_id = es.id
        WHERE ei.id = ?
        """,
        (item_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _item_row(row) if row else None


def get_item_by_ref(
    source_id: int, item_type: str, item_number: int
) -> Optional[ExternalItemRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ei.id, ei.source_id, ei.item_type, ei.item_number, ei.github_id,
               ei.title, ei.state, ei.url, ei.assignees_json,
               ei.updated_at_remote, ei.last_synced_at,
               es.organisation, es.repository, es.provider
        FROM external_items ei
        JOIN external_sources es ON ei.source_id = es.id
        WHERE ei.source_id = ? AND ei.item_type = ? AND ei.item_number = ?
        """,
        (source_id, item_type, item_number),
    )
    row = cursor.fetchone()
    conn.close()
    return _item_row(row) if row else None


def _item_row(row: tuple) -> ExternalItemRecord:
    return ExternalItemRecord(
        id=row[0],
        source_id=row[1],
        item_type=row[2],
        item_number=row[3],
        github_id=row[4],
        title=row[5],
        state=row[6],
        url=row[7],
        assignees_json=row[8],
        updated_at_remote=row[9],
        last_synced_at=row[10],
        organisation=row[11],
        repository=row[12],
        provider=row[13],
    )


def link_todo(
    todo_id: int, external_item_id: int, link_kind: str = "sync"
) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO todo_external_links (todo_id, external_item_id, link_kind)
        VALUES (?, ?, ?)
        ON CONFLICT(todo_id) DO UPDATE SET
            external_item_id = excluded.external_item_id,
            link_kind = excluded.link_kind
        """,
        (todo_id, external_item_id, link_kind),
    )
    conn.commit()
    conn.close()


def unlink_todo(todo_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todo_external_links WHERE todo_id = ?", (todo_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_link_for_todo(todo_id: int) -> Optional[TodoExternalLink]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT todo_id, external_item_id, link_kind
        FROM todo_external_links WHERE todo_id = ?
        """,
        (todo_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return TodoExternalLink(todo_id=row[0], external_item_id=row[1], link_kind=row[2])


def get_external_for_todos(todo_ids: list[int]) -> dict[int, ExternalItemRecord]:
    if not todo_ids:
        return {}
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(todo_ids))
    cursor.execute(
        f"""
        SELECT tel.todo_id,
               ei.id, ei.source_id, ei.item_type, ei.item_number, ei.github_id,
               ei.title, ei.state, ei.url, ei.assignees_json,
               ei.updated_at_remote, ei.last_synced_at,
               es.organisation, es.repository, es.provider
        FROM todo_external_links tel
        JOIN external_items ei ON tel.external_item_id = ei.id
        JOIN external_sources es ON ei.source_id = es.id
        WHERE tel.todo_id IN ({placeholders})
        """,
        todo_ids,
    )
    result: dict[int, ExternalItemRecord] = {}
    for row in cursor.fetchall():
        todo_id = row[0]
        result[todo_id] = _item_row(row[1:])
    conn.close()
    return result


def find_linked_todo_id(external_item_id: int) -> Optional[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT todo_id FROM todo_external_links WHERE external_item_id = ?",
        (external_item_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def list_items_for_source(
    source_id: int, *, state: Optional[str] = None
) -> list[ExternalItemRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT ei.id, ei.source_id, ei.item_type, ei.item_number, ei.github_id,
               ei.title, ei.state, ei.url, ei.assignees_json,
               ei.updated_at_remote, ei.last_synced_at,
               es.organisation, es.repository, es.provider
        FROM external_items ei
        JOIN external_sources es ON ei.source_id = es.id
        WHERE ei.source_id = ?
    """
    params: list[Any] = [source_id]
    if state:
        query += " AND ei.state = ?"
        params.append(state)
    query += " ORDER BY ei.item_type, ei.item_number DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_item_row(r) for r in rows]


def sources_tree(provider: str = "github") -> dict[str, list[dict[str, Any]]]:
    """Org → list of repos for API."""
    sources = list_sources(provider)
    tree: dict[str, list[dict[str, Any]]] = {}
    for s in sources:
        tree.setdefault(s.organisation, []).append(
            {
                "organisation": s.organisation,
                "repository": s.repository,
                "enabled": s.enabled,
                "last_synced_at": s.last_synced_at,
            }
        )
    return tree
