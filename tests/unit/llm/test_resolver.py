"""Unit tests for llm.resolver."""
import pytest

from agentsuite.llm.anthropic import AnthropicProvider
from agentsuite.llm.openai import OpenAIProvider
from agentsuite.llm.resolver import NoProviderConfigured, resolve_provider


def test_resolver_uses_explicit_provider_arg(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    p = resolve_provider("anthropic")
    assert isinstance(p, AnthropicProvider)


def test_resolver_uses_env_provider(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    p = resolve_provider()
    assert isinstance(p, OpenAIProvider)


def test_resolver_auto_detects_anthropic_first(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    p = resolve_provider()
    assert isinstance(p, AnthropicProvider)


def test_resolver_falls_back_to_openai_when_only_openai_present(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    p = resolve_provider()
    assert isinstance(p, OpenAIProvider)


def test_resolver_raises_when_no_keys(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("agentsuite.llm.resolver._ollama_daemon_running", lambda: False)
    with pytest.raises(NoProviderConfigured):
        resolve_provider()


def test_resolver_falls_back_to_ollama_when_no_keys(monkeypatch):
    from agentsuite.llm.ollama import OllamaProvider

    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("agentsuite.llm.resolver._ollama_daemon_running", lambda: True)
    p = resolve_provider()
    assert isinstance(p, OllamaProvider)


def test_resolver_named_ollama_works(monkeypatch):
    from agentsuite.llm.ollama import OllamaProvider

    monkeypatch.setattr("agentsuite.llm.resolver._ollama_daemon_running", lambda: True)
    p = resolve_provider("ollama")
    assert isinstance(p, OllamaProvider)


def test_resolver_named_ollama_raises_when_daemon_down(monkeypatch):
    monkeypatch.setattr("agentsuite.llm.resolver._ollama_daemon_running", lambda: False)
    with pytest.raises(NoProviderConfigured):
        resolve_provider("ollama")


def test_resolver_raises_for_unknown_provider_name(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    with pytest.raises(NoProviderConfigured):
        resolve_provider("groq")


def test_resolver_falls_back_to_gemini(monkeypatch):
    from agentsuite.llm.gemini import GeminiProvider

    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    p = resolve_provider()
    assert isinstance(p, GeminiProvider)


def test_resolver_named_gemini_works(monkeypatch):
    from agentsuite.llm.gemini import GeminiProvider

    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    p = resolve_provider("gemini")
    assert isinstance(p, GeminiProvider)


def test_resolver_accepts_google_api_key_alias(monkeypatch):
    from agentsuite.llm.gemini import GeminiProvider

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake")
    p = resolve_provider("gemini")
    assert isinstance(p, GeminiProvider)
