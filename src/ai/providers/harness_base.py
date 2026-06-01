"""Shared subprocess harness for Codex / Claude CLI."""

from __future__ import annotations

import json
import subprocess
from typing import TypeVar

from pydantic import BaseModel

from src.ai.providers.base import ProviderInfo, extract_json_object
from src.config import get_harness_config

T = TypeVar("T", bound=BaseModel)


class HarnessProviderBase:
    def __init__(self, name: str, binary: str, invoke_args: list[str]):
        self.name = name
        self.binary = binary
        self.invoke_args = invoke_args

    def is_available(self) -> bool:
        import shutil

        return shutil.which(self.binary) is not None

    def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        temperature: float = 0.2,
    ) -> T:
        harness = get_harness_config()
        schema_json = json.dumps(schema.model_json_schema())
        parts = []
        for m in messages:
            role = m.get("role", "user")
            parts.append(f"[{role}]\n{m.get('content', '')}")
        prompt = "\n\n".join(parts)
        full_prompt = (
            f"{prompt}\n\nReturn ONLY valid JSON matching this schema:\n{schema_json}"
        )

        cmd = [self.binary, *self.invoke_args, full_prompt]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=harness.timeout_seconds,
            shell=False,
        )

        if result.returncode != 0:
            err = result.stderr.strip() or result.stdout.strip() or "harness failed"
            raise RuntimeError(f"{self.name} harness error: {err}")

        output = result.stdout.strip()
        if not output:
            raise RuntimeError(f"{self.name} harness returned empty output")

        data = extract_json_object(output)
        return schema.model_validate(data)

    def describe(self) -> str:
        import shutil

        path = shutil.which(self.binary) or "not found"
        return f"{self.name} harness ({path})"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            backend="harness",
            model=self.binary,
            detail=self.describe(),
        )
