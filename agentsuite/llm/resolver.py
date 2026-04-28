"""Provider resolution: explicit > env > auto-detect."""
from __future__ import annotations

import os
import urllib.error
import urllib.request
from collections.abc import Callable

from agentsuite.llm.anthropic import AnthropicProvider
from agentsuite.llm.base import LLMProvider
from agentsuite.llm.gemini import GeminiProvider
from agentsuite.llm.ollama import OllamaProvider
from agentsuite.llm.openai import OpenAIProvider
from agentsuite.llm.retry import RetryingLLMProvider


class NoProviderConfigured(RuntimeError):
    """Raised when no LLM provider can be resolved from explicit arg, env, or detection."""


_PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def _ollama_daemon_running() -> bool:
    """Probe http://localhost:11434/api/tags; True if reachable."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="HEAD")
        with urllib.request.urlopen(req, timeout=0.5) as resp:  # noqa: S310 (fixed URL)
            return bool(resp.status == 200)
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        return False


def _check_anthropic() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _check_openai() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _check_gemini() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _check_ollama() -> bool:
    return _ollama_daemon_running()


_PROVIDER_CHECKS: dict[str, Callable[[], bool]] = {
    "anthropic": _check_anthropic,
    "openai": _check_openai,
    "gemini": _check_gemini,
    "ollama": _check_ollama,
}

# Auto-detect priority. Cloud providers first; local Ollama as last-resort fallback.
_AUTO_DETECT_ORDER = ("anthropic", "openai", "gemini", "ollama")


def _unmet_msg(provider: str) -> str:
    return {
        "anthropic": "ANTHROPIC_API_KEY not set",
        "openai": "OPENAI_API_KEY not set",
        "gemini": "GEMINI_API_KEY or GOOGLE_API_KEY not set",
        "ollama": "Ollama daemon not running at localhost:11434",
    }[provider]


def resolve_provider(name: str | None = None) -> LLMProvider:
    """Resolve an LLMProvider via explicit name, AGENTSUITE_LLM_PROVIDER env, or auto-detect.

    Auto-detect order: anthropic -> openai -> gemini -> ollama (local daemon).
    Raises NoProviderConfigured when no provider check succeeds, an unknown provider
    is named, or the named provider's prerequisite (api key or daemon) is missing.
    """
    chosen = name or os.environ.get("AGENTSUITE_LLM_PROVIDER")
    if chosen:
        if chosen not in _PROVIDERS:
            raise NoProviderConfigured(f"Unknown provider: {chosen}")
        if not _PROVIDER_CHECKS[chosen]():
            raise NoProviderConfigured(f"{_unmet_msg(chosen)} (provider '{chosen}')")
        return RetryingLLMProvider(_PROVIDERS[chosen]())
    for prov in _AUTO_DETECT_ORDER:
        if _PROVIDER_CHECKS[prov]():
            return RetryingLLMProvider(_PROVIDERS[prov]())
    raise NoProviderConfigured(
        "No provider configured. Set AGENTSUITE_LLM_PROVIDER, "
        "ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY (or GOOGLE_API_KEY), "
        "or start a local Ollama daemon at localhost:11434."
    )
