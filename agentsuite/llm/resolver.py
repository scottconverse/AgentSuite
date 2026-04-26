"""Provider resolution: explicit > env > auto-detect."""
from __future__ import annotations

import os

from agentsuite.llm.anthropic import AnthropicProvider
from agentsuite.llm.base import LLMProvider
from agentsuite.llm.openai import OpenAIProvider


class NoProviderConfigured(RuntimeError):
    """Raised when no LLM provider can be resolved from explicit arg, env, or detection."""


_PROVIDERS: dict[str, type] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


def resolve_provider(name: str | None = None) -> LLMProvider:
    """Resolve an LLMProvider via explicit name, AGENTSUITE_LLM_PROVIDER env, or auto-detect.

    Auto-detect order: Anthropic first (if ANTHROPIC_API_KEY set), then OpenAI.
    Raises NoProviderConfigured when no key is present, an unknown provider is named,
    or the named provider's API key env var is missing.
    """
    chosen = name or os.environ.get("AGENTSUITE_LLM_PROVIDER")
    if chosen:
        if chosen not in _PROVIDERS:
            raise NoProviderConfigured(f"Unknown provider: {chosen}")
        cls = _PROVIDERS[chosen]
        # Verify the corresponding key is present
        key_name = "ANTHROPIC_API_KEY" if chosen == "anthropic" else "OPENAI_API_KEY"
        if not os.environ.get(key_name):
            raise NoProviderConfigured(f"{key_name} not set for provider '{chosen}'")
        return cls()
    # Auto-detect: Anthropic first, then OpenAI
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicProvider()
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIProvider()
    raise NoProviderConfigured(
        "No provider configured. Set AGENTSUITE_LLM_PROVIDER, ANTHROPIC_API_KEY, or OPENAI_API_KEY."
    )
