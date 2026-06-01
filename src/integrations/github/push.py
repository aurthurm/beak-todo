"""Push local todo changes to GitHub when linked."""

from __future__ import annotations

from src.integrations.github.client import GitHubClient
from src.integrations.github.config import get_token, load_github_config
from src.services import external as ext_svc
from src.services.todos import get_todo_by_id


def push_todo_if_linked(todo_id: int) -> bool:
    """Push completed state and optionally title to GitHub. Returns True if pushed."""
    link = ext_svc.get_link_for_todo(todo_id)
    if link is None:
        return False
    item = ext_svc.get_item(link.external_item_id)
    if item is None or item.provider != "github":
        return False
    todo = get_todo_by_id(todo_id)
    if todo is None:
        return False
    token = get_token()
    if not token:
        return False
    cfg = load_github_config()
    sync_title = bool(cfg.get("sync_title_to_github", False))
    client = GitHubClient(token)
    org, repo, num = item.organisation, item.repository, item.item_number
    want_open = not todo.completed
    closed_remote = item.state in ("closed", "merged")
    if want_open == closed_remote:
        client.set_issue_state(org, repo, num, open=want_open)
        new_state = "open" if want_open else ("merged" if item.item_type == "pr" else "closed")
        ext_svc.upsert_item(
            item.source_id,
            item.item_type,
            item.item_number,
            item.title,
            new_state,
            item.url,
            github_id=item.github_id,
            updated_at_remote=item.updated_at_remote,
        )
    if sync_title and todo.message != item.title:
        client.update_issue_title(org, repo, num, todo.message)
    return True
