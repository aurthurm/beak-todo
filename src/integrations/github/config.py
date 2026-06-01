"""GitHub integration config at ~/.todos/integrations/github.toml."""

from __future__ import annotations

import os
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore

from src.integrations.github.schemas import RepoConfig
from src.todos import get_data_dir

DEFAULT_GITHUB_CONFIG: dict[str, Any] = {
    "token_env": "GITHUB_TOKEN",
    "token_file": "",
    "sync_title_to_github": False,
    "repos": [],
}


def get_config_path() -> Path:
    return get_data_dir() / "integrations" / "github.toml"


def load_github_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.is_file():
        return deepcopy(DEFAULT_GITHUB_CONFIG)
    with path.open("rb") as f:
        data = tomllib.load(f)
    merged = deepcopy(DEFAULT_GITHUB_CONFIG)
    if isinstance(data, dict):
        merged.update(data)
    return merged


def save_github_config(data: dict[str, Any]) -> Path:
    if tomli_w is None:
        raise RuntimeError("tomli-w required to save GitHub config")
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(data, f)
    return path


def write_default_config() -> Path:
    sample = deepcopy(DEFAULT_GITHUB_CONFIG)
    sample["repos"] = [
        {
            "organisation": "your-org",
            "repository": "your-repo",
            "enabled": True,
            "sync_issues": True,
            "sync_prs": True,
        }
    ]
    return save_github_config(sample)


@dataclass
class GitHubSettings:
    token: str
    sync_title_to_github: bool
    repos: list[RepoConfig]


def get_token(cfg: Optional[dict[str, Any]] = None) -> Optional[str]:
    cfg = cfg or load_github_config()
    token_env = str(cfg.get("token_env") or "GITHUB_TOKEN")
    token = os.environ.get(token_env)
    if token:
        return token.strip()
    token_file = str(cfg.get("token_file") or "").strip()
    if token_file:
        path = Path(token_file).expanduser()
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    return None


def parse_repos(cfg: dict[str, Any]) -> list[RepoConfig]:
    repos: list[RepoConfig] = []
    for entry in cfg.get("repos") or []:
        if not isinstance(entry, dict):
            continue
        repos.append(
            RepoConfig(
                organisation=str(entry.get("organisation", "")),
                repository=str(entry.get("repository", "")),
                enabled=bool(entry.get("enabled", True)),
                sync_issues=bool(entry.get("sync_issues", True)),
                sync_prs=bool(entry.get("sync_prs", True)),
            )
        )
    return [r for r in repos if r.organisation and r.repository]


def load_settings() -> GitHubSettings:
    cfg = load_github_config()
    token = get_token(cfg)
    if not token:
        raise RuntimeError(
            "GitHub token not found. Set GITHUB_TOKEN or configure token_file in github.toml"
        )
    return GitHubSettings(
        token=token,
        sync_title_to_github=bool(cfg.get("sync_title_to_github", False)),
        repos=parse_repos(cfg),
    )


def add_repo_to_config(organisation: str, repository: str) -> Path:
    cfg = load_github_config()
    repos = cfg.get("repos") or []
    if not isinstance(repos, list):
        repos = []
    for entry in repos:
        if (
            isinstance(entry, dict)
            and entry.get("organisation") == organisation
            and entry.get("repository") == repository
        ):
            return get_config_path()
    repos.append(
        {
            "organisation": organisation,
            "repository": repository,
            "enabled": True,
            "sync_issues": True,
            "sync_prs": True,
        }
    )
    cfg["repos"] = repos
    return save_github_config(cfg)
