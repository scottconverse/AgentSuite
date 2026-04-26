"""Unit tests for llm.anthropic — uses a stub Anthropic client."""
from unittest.mock import MagicMock

import pytest

from agentsuite.llm.anthropic import AnthropicProvider, _PRICING
from agentsuite.llm.base import LLMRequest


def _stub_client(text: str = "Hi", in_tokens: int = 10, out_tokens: int = 2) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.model = "claude-sonnet-4-6"
    response.usage = MagicMock(input_tokens=in_tokens, output_tokens=out_tokens)
    client.messages.create.return_value = response
    return client


def test_provider_name():
    p = AnthropicProvider(client=_stub_client())
    assert p.name == "anthropic"


def test_default_model():
    p = AnthropicProvider(client=_stub_client())
    assert p.default_model() == "claude-sonnet-4-6"


def test_complete_returns_response_with_usage(monkeypatch):
    p = AnthropicProvider(client=_stub_client(text="hello", in_tokens=100, out_tokens=20))
    resp = p.complete(LLMRequest(prompt="hi", system="terse"))
    assert resp.text == "hello"
    assert resp.input_tokens == 100
    assert resp.output_tokens == 20
    assert resp.model == "claude-sonnet-4-6"
    expected_usd = (100 * _PRICING["claude-sonnet-4-6"]["in"] + 20 * _PRICING["claude-sonnet-4-6"]["out"]) / 1_000_000
    assert resp.usd == pytest.approx(expected_usd)


def test_complete_uses_request_model_override():
    client = _stub_client()
    p = AnthropicProvider(client=client)
    p.complete(LLMRequest(prompt="x", model="claude-opus-4-7"))
    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-7"
