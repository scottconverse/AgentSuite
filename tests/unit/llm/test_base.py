"""Unit tests for llm.base."""
from agentsuite.llm.base import LLMRequest, LLMResponse


def test_llm_request_defaults():
    req = LLMRequest(prompt="Hello", system="be terse")
    assert req.max_tokens == 4096
    assert req.temperature == 0.0
    assert req.model is None


def test_llm_response_has_text_and_usage():
    resp = LLMResponse(
        text="Hi",
        model="claude-sonnet-4-6",
        input_tokens=10,
        output_tokens=2,
        usd=0.001,
    )
    assert resp.text == "Hi"
    assert resp.input_tokens == 10
    assert resp.usd == 0.001
