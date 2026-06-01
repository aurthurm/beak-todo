"""Codex CLI harness (explicit opt-in only)."""

from __future__ import annotations

from src.ai.providers.harness_base import HarnessProviderBase
from src.config import get_harness_config


class CodexHarnessProvider(HarnessProviderBase):
    def __init__(self) -> None:
        harness = get_harness_config()
        super().__init__(
            name="codex",
            binary=harness.codex_bin,
            invoke_args=["exec"],
        )
