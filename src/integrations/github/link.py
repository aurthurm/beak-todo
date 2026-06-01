"""Manual link / unlink todos to GitHub items."""

from __future__ import annotations

from src.integrations.github.client import GitHubClient
from src.integrations.github.config import load_settings
from src.integrations.github.display import parse_github_url
from src.services import external as ext_svc
from src.services.todos import get_todo_by_id


def link_todo_by_url(todo_id: int, url: str) -> ext_svc.ExternalItemRecord:
    if get_todo_by_id(todo_id) is None:
        raise ValueError(f"Todo #{todo_id} not found")
    parsed = parse_github_url(url)
    if parsed is None:
        raise ValueError(f"Not a GitHub issue/PR URL: {url}")

    settings = load_settings()
    client = GitHubClient(settings.token)
    if parsed.item_type == "pr":
        remote = client.get_pull(
            parsed.organisation, parsed.repository, parsed.item_number
        )
    else:
        remote = client.get_issue(
            parsed.organisation, parsed.repository, parsed.item_number
        )

    source_id = ext_svc.upsert_source(
        "github", parsed.organisation, parsed.repository
    )
    item_id = ext_svc.upsert_item(
        source_id,
        remote.item_type,
        remote.item_number,
        remote.title,
        remote.state,
        remote.url,
        github_id=remote.github_id,
        assignees=remote.assignees,
        updated_at_remote=remote.updated_at,
    )
    ext_svc.link_todo(todo_id, item_id, link_kind="manual")
    item = ext_svc.get_item(item_id)
    if item is None:
        raise RuntimeError("Failed to load linked item")
    return item


def unlink_todo(todo_id: int) -> bool:
    return ext_svc.unlink_todo(todo_id)
