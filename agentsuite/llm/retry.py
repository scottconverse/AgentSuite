"""Retry + timeout wrapper for any LLMProvider.

Wraps the synchronous ``complete()`` call with tenacity-based retry logic.
Transient failures (rate limits, network hiccups, 5xx responses) are retried
with exponential back-off; non-retriable exceptions (ProviderNotInstalled,
KeyboardInterrupt, SystemExit) are re-raised immediately.

Configuration via environment variables (all optional):
- ``AGENTSUITE_LLM_MAX_ATTEMPTS``  — total attempts including the first (default: 3)
- ``AGENTSUITE_LLM_TIMEOUT_SECS``  — wall-clock seconds budget for the full sequence
                                      across all retry attempts (default: 120.0)
"""
from __future__ import annotations

import logging
import os

from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_not_exception_type,
    stop_after_attempt,
    stop_after_delay,
    stop_any,
    wait_exponential,
)

from agentsuite.llm.base import LLMProvider, LLMRequest, LLMResponse, ProviderNotInstalled

_log = logging.getLogger(__name__)

_DEFAULT_MAX_ATTEMPTS: int = 3
_DEFAULT_TIMEOUT_SECS: float = 120.0
_WAIT_MIN_SECS: float = 1.0
_WAIT_MAX_SECS: float = 16.0

# Exception types that must never trigger a retry.
_NO_RETRY_EXCEPTIONS = (ProviderNotInstalled, KeyboardInterrupt, SystemExit)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key) or default)
    except (ValueError, TypeError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key) or default)
    except (ValueError, TypeError):
        return default


class RetryingLLMProvider:
    """Wraps any :class:`LLMProvider` and adds retry + timeout to ``complete()``.

    All other methods (``name``, ``default_model``) are forwarded unchanged.

    Example::

        inner = AnthropicProvider()
        provider = RetryingLLMProvider(inner)
        response = provider.complete(request)  # retried up to 3× on transient errors
    """

    def __init__(self, inner: LLMProvider) -> None:
        self._inner = inner
        self.name: str = inner.name  # settable instance var — satisfies LLMProvider Protocol

    def default_model(self) -> str:
        return self._inner.default_model()

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Forward to inner provider, retrying on transient failures."""
        max_attempts = _env_int("AGENTSUITE_LLM_MAX_ATTEMPTS", _DEFAULT_MAX_ATTEMPTS)
        timeout_secs = _env_float("AGENTSUITE_LLM_TIMEOUT_SECS", _DEFAULT_TIMEOUT_SECS)

        for attempt in Retrying(
            stop=stop_any(
                stop_after_attempt(max_attempts),
                stop_after_delay(timeout_secs),
            ),
            wait=wait_exponential(multiplier=1, min=_WAIT_MIN_SECS, max=_WAIT_MAX_SECS),
            retry=retry_if_not_exception_type(_NO_RETRY_EXCEPTIONS),
            reraise=True,
            before_sleep=before_sleep_log(_log, logging.WARNING),
        ):
            with attempt:
                return self._inner.complete(request)

        raise AssertionError("unreachable — tenacity reraise=True guarantees an exception")
