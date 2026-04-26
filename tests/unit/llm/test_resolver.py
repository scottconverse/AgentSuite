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
    with pytest.raises(NoProviderConfigured):
        resolve_provider()


def test_resolver_raises_for_unknown_provider_name(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    with pytest.raises(NoProviderConfigured):
        resolve_provider("groq")
