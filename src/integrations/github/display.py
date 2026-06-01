"""Display formatting and URL parsing for GitHub items."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

GITHUB_URL_RE = re.compile(
    r"github\.com/(?P<org>[^/]+)/(?P<repo>[^/]+)/(?P<kind>issues|pull)/(?P<number>\d+)",
    re.IGNORECASE,
)


@dataclass
class ParsedGitHubUrl:
    organisation: str
    repository: str
    item_type: str  # issue | pr
    item_number: int


def parse_github_url(url: str) -> Optional[ParsedGitHubUrl]:
    match = GITHUB_URL_RE.search(url)
    if not match:
        return None
    kind = match.group("kind").lower()
    item_type = "pr" if kind == "pull" else "issue"
    return ParsedGitHubUrl(
        organisation=match.group("org"),
        repository=match.group("repo"),
        item_type=item_type,
        item_number=int(match.group("number")),
    )


def format_display_source(
    organisation: str,
    repository: str,
    item_type: str,
    item_number: int,
) -> str:
    prefix = "PR" if item_type == "pr" else "#"
    num = f"{prefix}{item_number}" if item_type == "pr" else f"#{item_number}"
    return f"[GitHub] [{organisation}/{repository}] {num}"


def format_compact_source(
    organisation: str,
    repository: str,
    item_type: str,
    item_number: int,
) -> str:
    kind = "PR" if item_type == "pr" else "#"
    num = f"{kind}{item_number}"
    return f"GitHub · {organisation}/{repository} · {num}"


def github_issue_url(organisation: str, repository: str, number: int) -> str:
    return f"https://github.com/{organisation}/{repository}/issues/{number}"


def github_pr_url(organisation: str, repository: str, number: int) -> str:
    return f"https://github.com/{organisation}/{repository}/pull/{number}"


def normalize_repo_slug(slug: str) -> tuple[str, str]:
    """Parse org/repo from user input."""
    slug = slug.strip().strip("/")
    if slug.startswith("https://") or slug.startswith("http://"):
        path = urlparse(slug).path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
        raise ValueError(f"Invalid GitHub repo URL: {slug}")
    parts = slug.split("/")
    if len(parts) != 2:
        raise ValueError("Repo must be org/repo")
    return parts[0], parts[1]
