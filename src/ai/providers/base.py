"""AI provider protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class ProviderInfo:
    name: str
    backend: str
    model: str
    detail: str


class AIProvider(Protocol):
    name: str

    def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        temperature: float = 0.2,
    ) -> T: ...

    def is_available(self) -> bool: ...

    def describe(self) -> str: ...

    def info(self) -> ProviderInfo: ...


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse JSON from model output, stripping markdown fences if present."""
    import json
    import re

    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    elif text.find("[") != -1:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)
