"""Claude Code CLI harness (explicit opt-in only)."""

from __future__ import annotations

from src.ai.providers.harness_base import HarnessProviderBase
from src.config import get_harness_config


class ClaudeHarnessProvider(HarnessProviderBase):
    def __init__(self) -> None:
        harness = get_harness_config()
        super().__init__(
            name="claude",
            binary=harness.claude_bin,
            invoke_args=["-p"],
        )
