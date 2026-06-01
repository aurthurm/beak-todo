"""No AI provider — raises helpful errors."""

from __future__ import annotations

from pydantic import BaseModel

from src.ai.providers.base import ProviderInfo


class NoAIProvider:
    name = "none"

    def is_available(self) -> bool:
        return False

    def describe(self) -> str:
        return "AI disabled or not configured"

    def info(self) -> ProviderInfo:
        return ProviderInfo(name="none", backend="none", model="", detail=self.describe())

    def complete_json(self, messages, schema: type[BaseModel], temperature: float = 0.2):
        raise RuntimeError(
            "AI is not available. Run `t ai setup` and set an API key "
            "(OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY), "
            "or `t ai provider set codex` for harness mode."
        )
