"""Unit tests for llm.ollama — uses a stub ollama client."""
from unittest.mock import MagicMock

from agentsuite.llm.base import LLMRequest
from agentsuite.llm.ollama import OllamaProvider


def _stub_client(text: str = "Hi", in_tokens: int = 10, out_tokens: int = 2) -> MagicMock:
    client = MagicMock()
    response = {
        "model": "gemma4:e4b",
        "message": {"content": text},
        "prompt_eval_count": in_tokens,
        "eval_count": out_tokens,
    }
    client.chat.return_value = response
    return client


def test_provider_name():
    p = OllamaProvider(client=_stub_client())
    assert p.name == "ollama"


def test_default_model():
    p = OllamaProvider(client=_stub_client())
    assert p.default_model() == "gemma4:e4b"


def test_complete_returns_response_with_zero_cost():
    p = OllamaProvider(client=_stub_client(text="hello", in_tokens=100, out_tokens=20))
    resp = p.complete(LLMRequest(prompt="hi", system="terse"))
    assert resp.text == "hello"
    assert resp.input_tokens == 100
    assert resp.output_tokens == 20
    assert resp.usd == 0.0


def test_complete_uses_request_model_override():
    client = _stub_client()
    p = OllamaProvider(client=client)
    p.complete(LLMRequest(prompt="x", model="gemma4:e2b"))
    call_kwargs = client.chat.call_args.kwargs
    assert call_kwargs["model"] == "gemma4:e2b"


def test_complete_combines_system_and_user_messages():
    client = _stub_client()
    p = OllamaProvider(client=client)
    p.complete(LLMRequest(prompt="user-text", system="system-text"))
    call_kwargs = client.chat.call_args.kwargs
    msgs = call_kwargs["messages"]
    assert msgs[0]["role"] == "system" and msgs[0]["content"] == "system-text"
    assert msgs[1]["role"] == "user" and msgs[1]["content"] == "user-text"
