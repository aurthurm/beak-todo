"""LiteLLM-backed direct API provider."""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel

from src.ai.providers.base import ProviderInfo, extract_json_object

T = TypeVar("T", bound=BaseModel)


class LiteLLMProvider:
    name = "litellm"

    def __init__(self, model: str, detail: str = ""):
        self.model = model
        self._detail = detail or f"LiteLLM ({model})"

    def is_available(self) -> bool:
        return True

    def describe(self) -> str:
        return self._detail

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="litellm",
            backend="litellm",
            model=self.model,
            detail=self._detail,
        )

    def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        temperature: float = 0.2,
    ) -> T:
        import litellm

        schema_hint = json.dumps(schema.model_json_schema())
        augmented = list(messages)
        if augmented and augmented[0]["role"] == "system":
            augmented[0] = {
                "role": "system",
                "content": augmented[0]["content"]
                + f"\n\nJSON schema:\n{schema_hint}\nReturn only JSON.",
            }
        else:
            augmented.insert(
                0,
                {
                    "role": "system",
                    "content": f"Return only valid JSON matching:\n{schema_hint}",
                },
            )

        response = litellm.completion(
            model=self.model,
            messages=augmented,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Empty response from model")
        data = extract_json_object(content)
        return schema.model_validate(data)
