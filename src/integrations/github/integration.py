"""GitHub integration entry point."""

from __future__ import annotations

from typing import Optional

from src.integrations.base import SyncResult
from src.integrations.github import link as link_mod
from src.integrations.github.client import GitHubClient
from src.integrations.github.config import get_token, load_github_config, parse_repos
from src.integrations.github.sync import run_sync


class GitHubIntegration:
    provider = "github"

    def doctor(self) -> list[str]:
        issues: list[str] = []
        cfg = load_github_config()
        path = cfg.get("token_env", "GITHUB_TOKEN")
        token = get_token(cfg)
        if not token:
            issues.append(
                f"No GitHub token: set {path} or token_file in ~/.todos/integrations/github.toml"
            )
            return issues
        try:
            client = GitHubClient(token)
            user = client.verify_token()
            login = user.get("login", "?")
            issues.append(f"OK: authenticated as {login}")
        except Exception as e:
            issues.append(f"Token verification failed: {e}")
            return issues

        repos = parse_repos(cfg)
        if not repos:
            issues.append("No repos configured in github.toml")
        else:
            issues.append(f"Configured repos: {len(repos)}")
        return issues

    def sync(
        self,
        *,
        organisation: Optional[str] = None,
        repository: Optional[str] = None,
    ) -> SyncResult:
        return run_sync(organisation=organisation, repository=repository)

    def link_todo(self, todo_id: int, external_url: str) -> None:
        link_mod.link_todo_by_url(todo_id, external_url)

    def unlink_todo(self, todo_id: int) -> bool:
        return link_mod.unlink_todo(todo_id)
