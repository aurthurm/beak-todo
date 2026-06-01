"""GitHub integration DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RepoConfig:
    organisation: str
    repository: str
    enabled: bool = True
    sync_issues: bool = True
    sync_prs: bool = True


@dataclass
class GitHubRemoteItem:
    item_type: str
    item_number: int
    title: str
    state: str
    url: str
    github_id: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    updated_at: Optional[str] = None
    assignees: list[str] = field(default_factory=list)
