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


# ---------------------------------------------------------------------------
# Auth error no-retry tests
# ---------------------------------------------------------------------------

class _CountingProvider:
    """Inner provider that raises a given exception and counts calls."""

    name = "counting"

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc
        self.call_count = 0

    def default_model(self) -> str:
        return "m"

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        raise self._exc


def test_anthropic_auth_error_not_retried(monkeypatch):
    """anthropic.AuthenticationError must propagate immediately — no retries."""
    anthropic = pytest.importorskip("anthropic")
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    # Construct a minimal AuthenticationError using the real class so the
    # isinstance check inside tenacity fires correctly.
    exc = anthropic.AuthenticationError.__new__(anthropic.AuthenticationError)
    Exception.__init__(exc, "invalid api key")
    inner = _CountingProvider(exc)
    provider = RetryingLLMProvider(inner)
    with pytest.raises(anthropic.AuthenticationError):
        provider.complete(_req())
    assert inner.call_count == 1, (
        f"Expected 1 call (no retry), got {inner.call_count}"
    )


def test_anthropic_permission_denied_not_retried(monkeypatch):
    """anthropic.PermissionDeniedError must propagate immediately — no retries."""
    anthropic = pytest.importorskip("anthropic")
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    exc = anthropic.PermissionDeniedError.__new__(anthropic.PermissionDeniedError)
    Exception.__init__(exc, "permission denied")
    inner = _CountingProvider(exc)
    provider = RetryingLLMProvider(inner)
    with pytest.raises(anthropic.PermissionDeniedError):
        provider.complete(_req())
    assert inner.call_count == 1, (
        f"Expected 1 call (no retry), got {inner.call_count}"
    )


def test_openai_auth_error_not_retried(monkeypatch):
    """openai.AuthenticationError must propagate immediately — no retries."""
    openai = pytest.importorskip("openai")
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    exc = openai.AuthenticationError.__new__(openai.AuthenticationError)
    Exception.__init__(exc, "incorrect api key")
    inner = _CountingProvider(exc)
    provider = RetryingLLMProvider(inner)
    with pytest.raises(openai.AuthenticationError):
        provider.complete(_req())
    assert inner.call_count == 1, (
        f"Expected 1 call (no retry), got {inner.call_count}"
    )


def test_openai_permission_denied_not_retried(monkeypatch):
    """openai.PermissionDeniedError must propagate immediately — no retries."""
    openai = pytest.importorskip("openai")
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    exc = openai.PermissionDeniedError.__new__(openai.PermissionDeniedError)
    Exception.__init__(exc, "permission denied")
    inner = _CountingProvider(exc)
    provider = RetryingLLMProvider(inner)
    with pytest.raises(openai.PermissionDeniedError):
        provider.complete(_req())
    assert inner.call_count == 1, (
        f"Expected 1 call (no retry), got {inner.call_count}"
    )


def test_gemini_client_error_not_retried(monkeypatch):
    """google.genai.errors.ClientError (4xx) must propagate immediately — no retries."""
    pytest.importorskip("google.genai")
    from google.genai.errors import ClientError as GeminiClientError
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    # ClientError requires (code, response_json, response=None)
    exc = GeminiClientError(401, {"error": {"message": "API key not valid", "status": "UNAUTHENTICATED", "code": 401}})
    inner = _CountingProvider(exc)
    provider = RetryingLLMProvider(inner)
    with pytest.raises(GeminiClientError):
        provider.complete(_req())
    assert inner.call_count == 1, (
        f"Expected 1 call (no retry), got {inner.call_count}"
    )


def test_transient_runtime_error_is_retried(monkeypatch):
    """A plain RuntimeError (transient failure) MUST still be retried up to max_attempts."""
    monkeypatch.setenv("AGENTSUITE_LLM_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AGENTSUITE_LLM_TIMEOUT_SECS", "60")
    import agentsuite.llm.retry as retry_mod
    monkeypatch.setattr(retry_mod, "_WAIT_MIN_SECS", 0.0)
    monkeypatch.setattr(retry_mod, "_WAIT_MAX_SECS", 0.0)

    inner = _AlwaysFailProvider()
    provider = RetryingLLMProvider(inner)
    with pytest.raises(RuntimeError, match="always fails"):
        provider.complete(_req())
    assert inner.call_count == 3, (
        f"Expected 3 calls (full retry), got {inner.call_count}"
    )
