"""Provider registry."""

from __future__ import annotations

from src.integrations.base import Integration
from src.integrations.github.integration import GitHubIntegration

_REGISTRY: dict[str, type[GitHubIntegration]] = {
    "github": GitHubIntegration,
}


def get_integration(provider: str) -> Integration:
    cls = _REGISTRY.get(provider.lower())
    if cls is None:
        raise ValueError(f"Unknown integration provider: {provider}")
    return cls()
