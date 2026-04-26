"""Provider resolution: explicit > env > auto-detect."""
from __future__ import annotations

import os

from agentsuite.llm.anthropic import AnthropicProvider
from agentsuite.llm.base import LLMProvider
from agentsuite.llm.gemini import GeminiProvider
from agentsuite.llm.openai import OpenAIProvider


class NoProviderConfigured(RuntimeError):
    """Raised when no LLM provider can be resolved from explicit arg, env, or detection."""


_PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}

# Each provider accepts one or more env var names for its API key.
# Auto-detect walks this dict in insertion order.
_KEY_ENV_VARS: dict[str, tuple[str, ...]] = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "openai": ("OPENAI_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
}


def _has_key(provider: str) -> bool:
    return any(os.environ.get(v) for v in _KEY_ENV_VARS[provider])


def resolve_provider(name: str | None = None) -> LLMProvider:
    """Resolve an LLMProvider via explicit name, AGENTSUITE_LLM_PROVIDER env, or auto-detect.

    Auto-detect order: anthropic -> openai -> gemini.
    Gemini accepts either GEMINI_API_KEY or GOOGLE_API_KEY.
    Raises NoProviderConfigured when no key is present, an unknown provider is named,
    or the named provider's API key env var is missing.
    """
    chosen = name or os.environ.get("AGENTSUITE_LLM_PROVIDER")
    if chosen:
        if chosen not in _PROVIDERS:
            raise NoProviderConfigured(f"Unknown provider: {chosen}")
        if not _has_key(chosen):
            keys = " or ".join(_KEY_ENV_VARS[chosen])
            raise NoProviderConfigured(f"{keys} not set for provider '{chosen}'")
        return _PROVIDERS[chosen]()
    for prov in ("anthropic", "openai", "gemini"):
        if _has_key(prov):
            return _PROVIDERS[prov]()
    raise NoProviderConfigured(
        "No provider configured. Set AGENTSUITE_LLM_PROVIDER, "
        "ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY (or GOOGLE_API_KEY)."
    )
