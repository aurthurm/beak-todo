"""OS-agnostic configuration at ~/.todos/config.toml."""

from __future__ import annotations

import os
import sys
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore

from src.todos import get_data_dir

DEFAULT_CONFIG: dict[str, Any] = {
    "ai": {
        "enabled": True,
        "provider": "auto",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "show_provider_on_use": True,
    },
    "harness": {
        "codex_bin": "codex",
        "claude_bin": "claude",
        "timeout_seconds": 120,
    },
}

ALLOWED_PROVIDERS = frozenset(
    {
        "auto",
        "litellm",
        "openai",
        "anthropic",
        "gemini",
        "ollama",
        "codex",
        "claude",
        "none",
    }
)


@dataclass
class AiConfig:
    enabled: bool = True
    provider: str = "auto"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    show_provider_on_use: bool = True


@dataclass
class HarnessConfig:
    codex_bin: str = "codex"
    claude_bin: str = "claude"
    timeout_seconds: int = 120


def get_config_path() -> Path:
    return get_data_dir() / "config.toml"


def _deep_merge(base: dict, override: dict) -> dict:
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return deepcopy(DEFAULT_CONFIG)
    with path.open("rb") as f:
        user = tomllib.load(f)
    return _deep_merge(DEFAULT_CONFIG, user)


def _dump_toml(data: dict[str, Any]) -> str:
    if tomli_w is not None:
        out = tomli_w.dumps(data)
        return out.decode("utf-8") if isinstance(out, bytes) else out
    lines: list[str] = []
    for section, values in data.items():
        lines.append(f"[{section}]")
        if isinstance(values, dict):
            for k, v in values.items():
                if isinstance(v, bool):
                    lines.append(f"{k} = {'true' if v else 'false'}")
                elif isinstance(v, str):
                    lines.append(f'{k} = "{v}"')
                else:
                    lines.append(f"{k} = {v}")
        lines.append("")
    return "\n".join(lines)


def save_config(updates: dict[str, Any]) -> None:
    get_data_dir().mkdir(parents=True, exist_ok=True)
    current = load_config()
    merged = _deep_merge(current, updates)
    content = _dump_toml(merged)
    path = get_config_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".toml")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def get_ai_config() -> AiConfig:
    cfg = load_config().get("ai", {})
    return AiConfig(
        enabled=bool(cfg.get("enabled", True)),
        provider=str(cfg.get("provider", "auto")),
        model=str(cfg.get("model", "gpt-4o-mini")),
        temperature=float(cfg.get("temperature", 0.2)),
        show_provider_on_use=bool(cfg.get("show_provider_on_use", True)),
    )


def get_harness_config() -> HarnessConfig:
    cfg = load_config().get("harness", {})
    return HarnessConfig(
        codex_bin=str(cfg.get("codex_bin", "codex")),
        claude_bin=str(cfg.get("claude_bin", "claude")),
        timeout_seconds=int(cfg.get("timeout_seconds", 120)),
    )


def set_config_value(dotted_key: str, value: Any) -> None:
    """Set e.g. ai.provider -> openai."""
    parts = dotted_key.split(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Key must be section.field, got: {dotted_key}")
    section, field = parts
    save_config({section: {field: _coerce_value(field, value)}})


def _coerce_value(field: str, value: Any) -> Any:
    if field == "enabled" or field == "show_provider_on_use":
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if field == "temperature":
        return float(value)
    if field == "timeout_seconds":
        return int(value)
    return value


def get_config_value(dotted_key: str) -> Any:
    parts = dotted_key.split(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Key must be section.field, got: {dotted_key}")
    section, field = parts
    cfg = load_config()
    return cfg.get(section, {}).get(field)


def ensure_default_config() -> Path:
    get_data_dir().mkdir(parents=True, exist_ok=True)
    path = get_config_path()
    if not path.exists():
        save_config({})
    return path


def redact_config_for_display(cfg: Optional[dict] = None) -> dict[str, Any]:
    cfg = deepcopy(cfg or load_config())
    return cfg
