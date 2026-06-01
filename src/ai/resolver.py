"""Resolve AI provider from config, env, and CLI override."""

from __future__ import annotations

import os
import shutil
from typing import Optional

from src.ai.providers import (
    ClaudeHarnessProvider,
    CodexHarnessProvider,
    LiteLLMProvider,
    NoAIProvider,
)
from src.ai.providers.base import AIProvider, ProviderInfo
from src.config import get_ai_config, load_config

_shown_provider_this_session = False


def _env_set(name: str) -> bool:
    val = os.getenv(name)
    return bool(val and val.strip())


def detect_api_keys() -> dict[str, bool]:
    return {
        "OPENAI_API_KEY": _env_set("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": _env_set("ANTHROPIC_API_KEY"),
        "GOOGLE_API_KEY": _env_set("GOOGLE_API_KEY"),
        "GEMINI_API_KEY": _env_set("GEMINI_API_KEY"),
        "OLLAMA_API_BASE": _env_set("OLLAMA_API_BASE"),
    }


def detect_harnesses() -> dict[str, Optional[str]]:
    cfg = load_config().get("harness", {})
    codex_bin = cfg.get("codex_bin", "codex")
    claude_bin = cfg.get("claude_bin", "claude")
    return {
        "codex": shutil.which(codex_bin),
        "claude": shutil.which(claude_bin),
    }


def _default_litellm_model(provider_hint: str, configured_model: str) -> str:
    model = configured_model
    if "/" in model:
        return model
    hints = {
        "openai": "openai/gpt-4o-mini",
        "anthropic": "anthropic/claude-3-5-haiku-latest",
        "gemini": "gemini/gemini-2.0-flash",
        "ollama": "ollama/llama3.2",
    }
    if provider_hint in hints:
        return hints[provider_hint]
    if _env_set("OPENAI_API_KEY"):
        return f"openai/{model}"
    if _env_set("ANTHROPIC_API_KEY"):
        return f"anthropic/{model}" if not model.startswith("claude") else f"anthropic/{model}"
    if _env_set("GOOGLE_API_KEY") or _env_set("GEMINI_API_KEY"):
        return f"gemini/{model}" if not model.startswith("gemini") else model
    if _env_set("OLLAMA_API_BASE"):
        return f"ollama/{model}"
    return f"openai/{model}"


def _litellm_provider(provider_hint: str, ai_cfg) -> LiteLLMProvider:
    model = _default_litellm_model(provider_hint, ai_cfg.model)
    keys = detect_api_keys()
    detail_parts = [f"LiteLLM → {model}"]
    for k, found in keys.items():
        if found:
            detail_parts.append(f"({k})")
            break
    return LiteLLMProvider(model=model, detail=" ".join(detail_parts))


def _build_provider(name: str, ai_cfg) -> AIProvider:
    name = name.lower()
    if name in ("none", "disabled"):
        return NoAIProvider()
    if name == "codex":
        p = CodexHarnessProvider()
        if not p.is_available():
            raise RuntimeError("Codex CLI not found. Install codex or set harness.codex_bin in config.")
        return p
    if name == "claude":
        p = ClaudeHarnessProvider()
        if not p.is_available():
            raise RuntimeError("Claude CLI not found. Install claude or set harness.claude_bin in config.")
        return p
    if name in ("litellm", "openai", "anthropic", "gemini", "ollama"):
        if not ai_cfg.enabled:
            return NoAIProvider()
        keys = detect_api_keys()
        if name == "openai" and not keys["OPENAI_API_KEY"]:
            raise RuntimeError("OPENAI_API_KEY not set")
        if name == "anthropic" and not keys["ANTHROPIC_API_KEY"]:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        if name == "gemini" and not (keys["GOOGLE_API_KEY"] or keys["GEMINI_API_KEY"]):
            raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
        if name == "ollama" and not keys["OLLAMA_API_BASE"]:
            raise RuntimeError("OLLAMA_API_BASE not set")
        return _litellm_provider(name, ai_cfg)
    raise ValueError(f"Unknown provider: {name}")


def resolve_auto(ai_cfg) -> tuple[AIProvider, ProviderInfo]:
    if not ai_cfg.enabled:
        p = NoAIProvider()
        return p, p.info()

    keys = detect_api_keys()
    if keys["OPENAI_API_KEY"]:
        p = _litellm_provider("openai", ai_cfg)
        return p, p.info()
    if keys["ANTHROPIC_API_KEY"]:
        p = _litellm_provider("anthropic", ai_cfg)
        return p, p.info()
    if keys["GOOGLE_API_KEY"] or keys["GEMINI_API_KEY"]:
        p = _litellm_provider("gemini", ai_cfg)
        return p, p.info()
    if keys["OLLAMA_API_BASE"]:
        p = _litellm_provider("ollama", ai_cfg)
        return p, p.info()

    configured = ai_cfg.provider.lower()
    if configured in ("codex", "claude"):
        return _build_provider(configured, ai_cfg), _build_provider(configured, ai_cfg).info()

    p = NoAIProvider()
    return p, p.info()


def resolve_provider(override: Optional[str] = None) -> tuple[AIProvider, ProviderInfo]:
    ai_cfg = get_ai_config()
    chosen = (override or ai_cfg.provider or "auto").lower()

    if chosen == "auto":
        provider, info = resolve_auto(ai_cfg)
    else:
        provider = _build_provider(chosen, ai_cfg)
        info = provider.info()

    if not provider.is_available():
        raise RuntimeError(
            f"Provider '{chosen}' is not available. Run `t ai doctor` for diagnostics."
        )
    return provider, info


def maybe_show_provider(info: ProviderInfo) -> None:
    global _shown_provider_this_session
    ai_cfg = get_ai_config()
    if not ai_cfg.show_provider_on_use or _shown_provider_this_session:
        return
    _shown_provider_this_session = True
    import typer

    typer.echo(f"Using {info.detail}")


def peek_auto_resolution() -> str:
    """Human-readable resolution for doctor (no network)."""
    try:
        _, info = resolve_auto(get_ai_config())
        if info.name == "none":
            return "No provider (set API keys or configure harness)"
        return info.detail
    except Exception as e:
        return str(e)
