"""GitHub REST API client (httpx)."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.integrations.github.schemas import GitHubRemoteItem


class GitHubClient:
    def __init__(self, token: str, timeout: float = 30.0):
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._timeout = timeout
        self._base = "https://api.github.com"

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        with httpx.Client(timeout=self._timeout) as client:
            r = client.get(f"{self._base}{path}", headers=self._headers, params=params)
            r.raise_for_status()
            return r.json()

    def _patch(self, path: str, body: dict) -> Any:
        with httpx.Client(timeout=self._timeout) as client:
            r = client.patch(f"{self._base}{path}", headers=self._headers, json=body)
            r.raise_for_status()
            return r.json()

    def _paginate(self, path: str, params: Optional[dict] = None) -> list[dict]:
        params = dict(params or {})
        params.setdefault("per_page", 100)
        params.setdefault("state", "all")
        page = 1
        items: list[dict] = []
        while True:
            params["page"] = page
            batch = self._get(path, params)
            if not batch:
                break
            items.extend(batch)
            if len(batch) < params["per_page"]:
                break
            page += 1
        return items

    def verify_token(self) -> dict:
        return self._get("/user")

    def list_issues(self, org: str, repo: str) -> list[GitHubRemoteItem]:
        raw = self._paginate(f"/repos/{org}/{repo}/issues", {"state": "all"})
        result: list[GitHubRemoteItem] = []
        for item in raw:
            if item.get("pull_request"):
                continue
            result.append(_parse_issue(item, org, repo))
        return result

    def list_pulls(self, org: str, repo: str) -> list[GitHubRemoteItem]:
        raw = self._paginate(f"/repos/{org}/{repo}/pulls", {"state": "all"})
        return [_parse_pr(item, org, repo) for item in raw]

    def get_issue(self, org: str, repo: str, number: int) -> GitHubRemoteItem:
        data = self._get(f"/repos/{org}/{repo}/issues/{number}")
        if data.get("pull_request"):
            return self.get_pull(org, repo, number)
        return _parse_issue(data, org, repo)

    def get_pull(self, org: str, repo: str, number: int) -> GitHubRemoteItem:
        data = self._get(f"/repos/{org}/{repo}/pulls/{number}")
        return _parse_pr(data, org, repo)

    def set_issue_state(self, org: str, repo: str, number: int, *, open: bool) -> None:
        self._patch(
            f"/repos/{org}/{repo}/issues/{number}",
            {"state": "open" if open else "closed"},
        )

    def update_issue_title(self, org: str, repo: str, number: int, title: str) -> None:
        self._patch(f"/repos/{org}/{repo}/issues/{number}", {"title": title})


def _labels(item: dict) -> list[str]:
    return [lb.get("name", "") for lb in item.get("labels") or [] if lb.get("name")]


def _assignees(item: dict) -> list[str]:
    return [u.get("login", "") for u in item.get("assignees") or [] if u.get("login")]


def _parse_issue(item: dict, org: str, repo: str) -> GitHubRemoteItem:
    number = int(item["number"])
    state = "closed" if item.get("state") == "closed" else "open"
    return GitHubRemoteItem(
        item_type="issue",
        item_number=number,
        title=item.get("title") or "",
        state=state,
        url=item.get("html_url") or f"https://github.com/{org}/{repo}/issues/{number}",
        github_id=str(item.get("node_id") or ""),
        labels=_labels(item),
        updated_at=item.get("updated_at"),
        assignees=_assignees(item),
    )


def _parse_pr(item: dict, org: str, repo: str) -> GitHubRemoteItem:
    number = int(item["number"])
    state_raw = item.get("state", "open")
    merged = item.get("merged_at")
    if merged:
        state = "merged"
    elif state_raw == "closed":
        state = "closed"
    else:
        state = "open"
    return GitHubRemoteItem(
        item_type="pr",
        item_number=number,
        title=item.get("title") or "",
        state=state,
        url=item.get("html_url") or f"https://github.com/{org}/{repo}/pull/{number}",
        github_id=str(item.get("node_id") or ""),
        labels=_labels(item),
        updated_at=item.get("updated_at"),
        assignees=_assignees(item),
    )
