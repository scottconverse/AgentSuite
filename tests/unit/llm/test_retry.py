"""Unit tests for agentsuite.llm.retry.RetryingLLMProvider."""
from __future__ import annotations

import pytest

from agentsuite.llm.base import LLMRequest, LLMResponse, ProviderNotInstalled
from agentsuite.llm.retry import RetryingLLMProvider


def _ok_response() -> LLMResponse:
    return LLMResponse(text="ok", model="m", input_tokens=1, output_tokens=1, usd=0.0)


class _SuccessProvider:
    name = "success"
    call_count = 0

    def default_model(self) -> str:
        return "m"

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        return _ok_response()


class _FailThenSucceedProvider:
    """Fails the first N calls, then succeeds."""

    name = "flaky"

    def __init__(self, fail_count: int) -> None:
        self.fail_count = fail_count
        self.call_count = 0

    def default_model(self) -> str:
        return "m"

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        if self.call_count <= self.fail_count:
            raise RuntimeError(f"transient error (call {self.call_count})")
        return _ok_response()


class _AlwaysFailProvider:
    name = "broken"
    call_count = 0

    def default_model(self) -> str:
        return "m"

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        raise RuntimeError("always fails")


class _ProviderNotInstalledProvider:
    name = "missing"

    def default_model(self) -> str:
        return "m"

    def complete(self, request: LLMRequest) -> LLMResponse:
        raise ProviderNotInstalled("SDK not installed")


def _req() -> LLMRequest:
    return LLMRequest(prompt="hello")


def test_retrying_provider_passes_through_on_success():
    inner = _SuccessProvider()
    provider = RetryingLLMProvider(inner)
    response = provider.complete(_req())
    assert response.text == "ok"
    assert inner.call_count == 1


def test_retrying_provider_forwards_name_and_default_model():
    inner = _SuccessProvider()
    provider = RetryingLLMProvider(inner)
    assert provider.name == "success"
    assert provider.default_model() == "m"


def test_retrying_provider_retries_on_transient_failure(monkeypatch):
    """2 failures then success should result in 3 calls total (within 3-attempt limit)."""
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AGENTSUITE_LLM_TIMEOUT_SECS", "60")
    # Override wait to avoid sleeping in tests
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    inner = _FailThenSucceedProvider(fail_count=2)
    provider = RetryingLLMProvider(inner)
    response = provider.complete(_req())
    assert response.text == "ok"
    assert inner.call_count == 3


def test_retrying_provider_gives_up_after_max_attempts(monkeypatch):
    """All 3 attempts fail → RuntimeError propagated after last attempt."""
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AGENTSUITE_LLM_TIMEOUT_SECS", "60")
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    inner = _AlwaysFailProvider()
    provider = RetryingLLMProvider(inner)
    with pytest.raises(RuntimeError, match="always fails"):
        provider.complete(_req())
    assert inner.call_count == 3


def test_retrying_provider_does_not_retry_provider_not_installed(monkeypatch):
    """ProviderNotInstalled must propagate immediately — no retries."""
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    inner = _ProviderNotInstalledProvider()
    provider = RetryingLLMProvider(inner)
    with pytest.raises(ProviderNotInstalled):
        provider.complete(_req())


def test_retrying_provider_respects_max_attempts_env(monkeypatch):
    """AGENTSUITE_LLM_MAX_ATTEMPTS=1 means no retries — fail immediately."""
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "1")
    monkeypatch.setenv("AGENTSUITE_LLM_TIMEOUT_SECS", "60")

    inner = _AlwaysFailProvider()
    provider = RetryingLLMProvider(inner)
    with pytest.raises(RuntimeError):
        provider.complete(_req())
    assert inner.call_count == 1
