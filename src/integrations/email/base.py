"""Email provider protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class DoctorResult:
    ok: bool
    messages: list[str]


class EmailProvider(Protocol):
    name: str

    def doctor(self) -> DoctorResult: ...

    def send(
        self,
        *,
        to: list[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_address: Optional[str] = None,
    ) -> str: ...
