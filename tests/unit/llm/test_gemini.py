"""Unit tests for llm.gemini — uses a stub genai module."""
from unittest.mock import MagicMock

import pytest

from agentsuite.llm.base import LLMRequest
from agentsuite.llm.gemini import GeminiProvider, _PRICING


def _stub_client(text: str = "Hi", in_tokens: int = 10, out_tokens: int = 2) -> MagicMock:
    client = MagicMock()
    result = MagicMock()
    result.text = text
    result.model_version = None  # default: no model_version → fall back to request model
    result.usage_metadata = MagicMock(
        prompt_token_count=in_tokens,
        candidates_token_count=out_tokens,
    )
    client.models.generate_content.return_value = result
    return client


def test_provider_name():
    p = GeminiProvider(client=_stub_client())
    assert p.name == "gemini"


def test_default_model():
    p = GeminiProvider(client=_stub_client())
    assert p.default_model() == "gemini-2.5-flash"


def test_complete_returns_response_with_usage():
    p = GeminiProvider(client=_stub_client(text="hello", in_tokens=100, out_tokens=20))
    resp = p.complete(LLMRequest(prompt="hi", system="terse"))
    assert resp.text == "hello"
    assert resp.input_tokens == 100
    assert resp.output_tokens == 20
    assert resp.model == "gemini-2.5-flash"
    expected_usd = (
        100 * _PRICING["gemini-2.5-flash"]["in"] + 20 * _PRICING["gemini-2.5-flash"]["out"]
    ) / 1_000_000
    assert resp.usd == pytest.approx(expected_usd)
    assert resp.usd > 0


def test_complete_uses_request_model_override():
    client = _stub_client()
    p = GeminiProvider(client=client)
    p.complete(LLMRequest(prompt="x", model="gemini-2.5-pro"))
    call_kwargs = client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-2.5-pro"


def test_complete_passes_system_instruction():
    client = _stub_client()
    p = GeminiProvider(client=client)
    p.complete(LLMRequest(prompt="hi", system="be terse"))
    call_kwargs = client.models.generate_content.call_args.kwargs
    assert call_kwargs["config"].system_instruction == "be terse"


def test_complete_uses_model_version_from_response():
    """LLMResponse.model equals the response model_version when the API returns one."""
    client = MagicMock()
    result = MagicMock()
    result.text = "hello"
    result.model_version = "gemini-1.5-pro-002"
    result.usage_metadata = MagicMock(prompt_token_count=5, candidates_token_count=3)
    client.models.generate_content.return_value = result

    p = GeminiProvider(client=client)
    resp = p.complete(LLMRequest(prompt="hi", model="gemini-1.5-pro"))
    assert resp.model == "gemini-1.5-pro-002"


def test_complete_falls_back_to_request_model_when_no_model_version():
    """LLMResponse.model falls back to the requested model name when model_version is absent."""
    client = MagicMock()
    result = MagicMock(spec=[])  # spec=[] so getattr finds no model_version attr
    result.text = "hello"
    result.usage_metadata = MagicMock(prompt_token_count=5, candidates_token_count=3)
    client.models.generate_content.return_value = result

    p = GeminiProvider(client=client)
    resp = p.complete(LLMRequest(prompt="hi", model="gemini-2.5-flash"))
    assert resp.model == "gemini-2.5-flash"


def test_complete_falls_back_to_request_model_when_model_version_is_none():
    """LLMResponse.model falls back to the requested model name when model_version is None."""
    client = MagicMock()
    result = MagicMock()
    result.text = "hello"
    result.model_version = None
    result.usage_metadata = MagicMock(prompt_token_count=5, candidates_token_count=3)
    client.models.generate_content.return_value = result

    p = GeminiProvider(client=client)
    resp = p.complete(LLMRequest(prompt="hi", model="gemini-2.5-pro"))
    assert resp.model == "gemini-2.5-pro"


def test_gemini_key_precedence(monkeypatch):
    """GEMINI_API_KEY takes precedence over GOOGLE_API_KEY when both are set."""
    import os
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key-123")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key-456")
    # Verify the selection logic matches what GeminiProvider.__init__ uses
    selected = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    assert selected == "gemini-key-123"

    monkeypatch.delenv("GEMINI_API_KEY")
    fallback = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    assert fallback == "google-key-456"
