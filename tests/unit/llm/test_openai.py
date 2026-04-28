"""Unit tests for llm.openai — uses a stub OpenAI client."""
from unittest.mock import MagicMock

import pytest

from agentsuite.llm.base import LLMRequest
from agentsuite.llm.openai import OpenAIProvider, _PRICING


_DEFAULT_MODEL = "gpt-5.4"


def _stub_client(text: str = "Hi", in_tokens: int = 10, out_tokens: int = 2) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=text))]
    response.model = _DEFAULT_MODEL
    response.usage = MagicMock(prompt_tokens=in_tokens, completion_tokens=out_tokens)
    client.chat.completions.create.return_value = response
    return client


def test_provider_name():
    p = OpenAIProvider(client=_stub_client())
    assert p.name == "openai"


def test_default_model():
    p = OpenAIProvider(client=_stub_client())
    assert p.default_model() == _DEFAULT_MODEL


def test_complete_returns_response_with_usage():
    p = OpenAIProvider(client=_stub_client(text="hello", in_tokens=100, out_tokens=20))
    resp = p.complete(LLMRequest(prompt="hi", system="terse"))
    assert resp.text == "hello"
    assert resp.input_tokens == 100
    assert resp.output_tokens == 20
    expected_usd = (100 * _PRICING[_DEFAULT_MODEL]["in"] + 20 * _PRICING[_DEFAULT_MODEL]["out"]) / 1_000_000
    assert resp.usd == pytest.approx(expected_usd)


def test_complete_uses_request_model_override():
    client = _stub_client()
    p = OpenAIProvider(client=client)
    p.complete(LLMRequest(prompt="x", model="gpt-5.5"))
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-5.5"
