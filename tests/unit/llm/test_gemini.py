"""Unit tests for llm.gemini — uses a stub genai module."""
from unittest.mock import MagicMock

import pytest

from agentsuite.llm.base import LLMRequest
from agentsuite.llm.gemini import GeminiProvider, _PRICING


def _stub_client(text: str = "Hi", in_tokens: int = 10, out_tokens: int = 2) -> MagicMock:
    client = MagicMock()
    result = MagicMock()
    result.text = text
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
