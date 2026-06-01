from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.schemas import GitHubSourcesResponse, GitHubStatusResponse, GitHubSyncResponse
from src.integrations.github.config import parse_repos, load_github_config
from src.integrations.registry import get_integration
from src.services import external as ext_svc

router = APIRouter(prefix="/integrations/github", tags=["integrations"])


@router.get("/sources", response_model=GitHubSourcesResponse)
def github_sources():
    tree = ext_svc.sources_tree("github")
    return GitHubSourcesResponse(organisations=tree)


@router.get("/status", response_model=GitHubStatusResponse)
def github_status():
    cfg = load_github_config()
    repos = parse_repos(cfg)
    sources = ext_svc.list_sources("github")
    issues = [line for line in get_integration("github").doctor() if not line.startswith("OK:")]
    return GitHubStatusResponse(
        configured_repos=len(repos),
        sources_in_db=len(sources),
        last_errors=issues,
    )


@router.post("/sync", response_model=GitHubSyncResponse)
def github_sync():
    try:
        result = get_integration("github").sync()
    except RuntimeError as e:
        raise HTTPException(400, str(e)) from e
    return GitHubSyncResponse(
        created=result.created,
        updated=result.updated,
        pushed=result.pushed,
        errors=result.errors,
    )
