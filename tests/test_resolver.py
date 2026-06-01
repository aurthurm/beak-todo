import pytest

from src.ai.resolver import detect_api_keys, resolve_auto
from src.config import AiConfig


def test_detect_api_keys_empty(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    keys = detect_api_keys()
    assert keys["OPENAI_API_KEY"] is False


def test_resolve_auto_no_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_API_BASE", raising=False)
    ai_cfg = AiConfig(provider="auto", enabled=True)
    provider, info = resolve_auto(ai_cfg)
    assert info.name == "none"
