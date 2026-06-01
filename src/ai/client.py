"""AI client helpers with JSON retry."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from src.ai.providers.base import AIProvider
from src.config import get_ai_config

T = TypeVar("T", bound=BaseModel)


def complete_json(
    provider: AIProvider,
    messages: list[dict[str, str]],
    schema: type[T],
    verbose: bool = False,
) -> T:
    ai_cfg = get_ai_config()
    try:
        return provider.complete_json(messages, schema, temperature=ai_cfg.temperature)
    except Exception as first_error:
        repair_messages = messages + [
            {
                "role": "user",
                "content": "Your previous response was invalid. Return ONLY valid JSON matching the schema.",
            }
        ]
        try:
            return provider.complete_json(
                repair_messages, schema, temperature=ai_cfg.temperature
            )
        except Exception as second_error:
            if verbose:
                raise RuntimeError(
                    f"AI failed: {first_error}\nRetry: {second_error}"
                ) from second_error
            raise RuntimeError(f"AI request failed: {first_error}") from first_error
