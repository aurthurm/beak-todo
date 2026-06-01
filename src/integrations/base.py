"""Integration protocol for external work sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class SyncResult:
    provider: str
    created: int = 0
    updated: int = 0
    pushed: int = 0
    errors: list[str] = field(default_factory=list)


class Integration(Protocol):
    provider: str

    def doctor(self) -> list[str]:
        """Return list of issues; empty if healthy."""
        ...

    def sync(
        self,
        *,
        organisation: Optional[str] = None,
        repository: Optional[str] = None,
    ) -> SyncResult:
        ...

    def link_todo(self, todo_id: int, external_url: str) -> None:
        ...

    def unlink_todo(self, todo_id: int) -> bool:
        ...
