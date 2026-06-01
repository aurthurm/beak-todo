"""Bidirectional GitHub sync."""

from __future__ import annotations

from typing import Optional

from src.integrations.base import SyncResult
from src.integrations.github.client import GitHubClient
from src.integrations.github.config import GitHubSettings, load_github_config, load_settings
from src.integrations.github.schemas import GitHubRemoteItem, RepoConfig
from src.services import external as ext_svc
from src.services import tags as tags_svc
from src.services.todos import create_todo, get_todo_by_id, update_todo


def _remote_completed(state: str) -> bool:
    return state in ("closed", "merged")


def _apply_remote_to_todo(
    todo_id: int,
    remote: GitHubRemoteItem,
    *,
    sync_title: bool,
) -> bool:
    todo = get_todo_by_id(todo_id)
    if todo is None:
        return False
    completed = _remote_completed(remote.state)
    changed = False
    if todo.completed != completed:
        update_todo(todo_id, completed=completed)
        changed = True
    if sync_title and todo.message != remote.title:
        update_todo(todo_id, message=remote.title)
        changed = True
    if remote.labels:
        tags_svc.merge_tags_for_todo(todo_id, remote.labels)
    return changed


def _push_local_to_github(
    client: GitHubClient,
    item: ext_svc.ExternalItemRecord,
    todo_id: int,
    *,
    sync_title: bool,
) -> bool:
    todo = get_todo_by_id(todo_id)
    if todo is None:
        return False
    org, repo = item.organisation, item.repository
    number = item.item_number
    pushed = False
    want_open = not todo.completed
    currently_closed = _remote_completed(item.state)
    if want_open != (not currently_closed):
        client.set_issue_state(org, repo, number, open=want_open)
        pushed = True
    if sync_title and todo.message != item.title:
        client.update_issue_title(org, repo, number, todo.message)
        pushed = True
    return pushed


def sync_repo(
    client: GitHubClient,
    settings: GitHubSettings,
    repo: RepoConfig,
) -> SyncResult:
    result = SyncResult(provider="github")
    if not repo.enabled:
        return result

    source_id = ext_svc.upsert_source(
        "github",
        repo.organisation,
        repo.repository,
        enabled=repo.enabled,
        sync_issues=repo.sync_issues,
        sync_prs=repo.sync_prs,
    )

    remotes: list[GitHubRemoteItem] = []
    try:
        if repo.sync_issues:
            remotes.extend(client.list_issues(repo.organisation, repo.repository))
        if repo.sync_prs:
            remotes.extend(client.list_pulls(repo.organisation, repo.repository))
    except Exception as e:
        result.errors.append(f"{repo.organisation}/{repo.repository}: {e}")
        return result

    for remote in remotes:
        try:
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
            todo_id = ext_svc.find_linked_todo_id(item_id)
            if todo_id is None:
                todo_id = create_todo(
                    remote.title,
                    priority=0,
                    category="General",
                    completed=int(_remote_completed(remote.state)),
                )
                ext_svc.link_todo(todo_id, item_id, link_kind="sync")
                if remote.labels:
                    tags_svc.merge_tags_for_todo(todo_id, remote.labels)
                result.created += 1
            else:
                if _apply_remote_to_todo(
                    todo_id, remote, sync_title=settings.sync_title_to_github
                ):
                    result.updated += 1
                ext_svc.upsert_item(
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

            linked_id = ext_svc.find_linked_todo_id(item_id)
            if linked_id is not None:
                item = ext_svc.get_item(item_id)
                if item and _push_local_to_github(
                    client, item, linked_id, sync_title=settings.sync_title_to_github
                ):
                    result.pushed += 1
        except Exception as e:
            result.errors.append(
                f"{repo.organisation}/{repo.repository} "
                f"{remote.item_type}#{remote.item_number}: {e}"
            )

    ext_svc.touch_source_synced(source_id)
    return result


def run_sync(
    *,
    organisation: Optional[str] = None,
    repository: Optional[str] = None,
) -> SyncResult:
    settings = load_settings()
    client = GitHubClient(settings.token)
    cfg = load_github_config()
    repos = settings.repos
    if organisation and repository:
        repos = [
            r
            for r in repos
            if r.organisation == organisation and r.repository == repository
        ]
    if not repos:
        for entry in cfg.get("repos") or []:
            if isinstance(entry, dict):
                org = str(entry.get("organisation", ""))
                rep = str(entry.get("repository", ""))
                if org and rep:
                    ext_svc.upsert_source("github", org, rep)
        repos = settings.repos

    aggregate = SyncResult(provider="github")
    for repo in repos:
        if organisation and repo.organisation != organisation:
            continue
        if repository and repo.repository != repository:
            continue
        partial = sync_repo(client, settings, repo)
        aggregate.created += partial.created
        aggregate.updated += partial.updated
        aggregate.pushed += partial.pushed
        aggregate.errors.extend(partial.errors)
    return aggregate
