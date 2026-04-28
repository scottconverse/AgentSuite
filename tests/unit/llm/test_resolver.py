"""Unit tests for llm.resolver."""
import sys
from unittest.mock import MagicMock

import pytest

from agentsuite.llm.anthropic import AnthropicProvider
from agentsuite.llm.openai import OpenAIProvider
from agentsuite.llm.resolver import NoProviderConfigured, resolve_provider


def _make_ollama_mock() -> MagicMock:
    """Return a minimal mock of the ollama package."""
    mock_pkg = MagicMock()
    mock_pkg.Client.return_value = MagicMock()
    return mock_pkg


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
    mock_ollama = _make_ollama_mock()
    with pytest.MonkeyPatch().context() as mp:
        mp.setitem(sys.modules, "ollama", mock_ollama)
        p = resolve_provider()
    assert isinstance(p, OllamaProvider)


def test_resolver_named_ollama_works(monkeypatch):
    from agentsuite.llm.ollama import OllamaProvider

    monkeypatch.setattr("agentsuite.llm.resolver._ollama_daemon_running", lambda: True)
    mock_ollama = _make_ollama_mock()
    with pytest.MonkeyPatch().context() as mp:
        mp.setitem(sys.modules, "ollama", mock_ollama)
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


# ---------------------------------------------------------------------------
# C3: ProviderNotInstalled (NoProviderConfigured) message quality tests
# Each test verifies that when a named provider's prerequisite is missing,
# the raised NoProviderConfigured exception carries a message that includes
# both the provider name and an actionable install/setup hint.
# ---------------------------------------------------------------------------

_PROVIDER_MISSING_PARAMS = [
    pytest.param(
        "anthropic",
        {"ANTHROPIC_API_KEY": None},
        {},
        "ANTHROPIC_API_KEY",
        id="anthropic-missing-key",
    ),
    pytest.param(
        "openai",
        {"OPENAI_API_KEY": None},
        {},
        "OPENAI_API_KEY",
        id="openai-missing-key",
    ),
    pytest.param(
        "gemini",
        {"GEMINI_API_KEY": None, "GOOGLE_API_KEY": None},
        {},
        "GEMINI_API_KEY",
        id="gemini-missing-key",
    ),
    pytest.param(
        "ollama",
        {},
        {"agentsuite.llm.resolver._ollama_daemon_running": lambda: False},
        "localhost:11434",
        id="ollama-daemon-not-running",
    ),
]


@pytest.mark.parametrize(
    "provider,unset_envs,patches,expected_hint",
    _PROVIDER_MISSING_PARAMS,
)
def test_no_provider_configured_message_contains_provider_name(
    monkeypatch, provider, unset_envs, patches, expected_hint
):
    """NoProviderConfigured message must contain the provider name when prerequisite is absent."""
    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    for key, val in unset_envs.items():
        if val is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, val)
    for target, replacement in patches.items():
        monkeypatch.setattr(target, replacement)

    with pytest.raises(NoProviderConfigured) as exc_info:
        resolve_provider(provider)

    msg = str(exc_info.value)
    assert provider in msg, (
        f"Expected provider name '{provider}' in error message, got: {msg!r}"
    )


@pytest.mark.parametrize(
    "provider,unset_envs,patches,expected_hint",
    _PROVIDER_MISSING_PARAMS,
)
def test_no_provider_configured_message_contains_actionable_hint(
    monkeypatch, provider, unset_envs, patches, expected_hint
):
    """NoProviderConfigured message must contain an actionable setup hint."""
    monkeypatch.delenv("AGENTSUITE_LLM_PROVIDER", raising=False)
    for key, val in unset_envs.items():
        if val is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, val)
    for target, replacement in patches.items():
        monkeypatch.setattr(target, replacement)

    with pytest.raises(NoProviderConfigured) as exc_info:
        resolve_provider(provider)

    msg = str(exc_info.value)
    assert expected_hint in msg, (
        f"Expected hint '{expected_hint}' in error message, got: {msg!r}"
    )
