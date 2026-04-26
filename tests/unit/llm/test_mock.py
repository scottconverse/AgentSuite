"""Unit tests for llm.mock — deterministic stub provider for tests."""
import pytest

from agentsuite.llm.base import LLMRequest
from agentsuite.llm.mock import MockLLMProvider, NoMockResponseConfigured


def test_mock_returns_canned_response_by_keyword():
    p = MockLLMProvider(responses={"extract": "extracted-content"})
    resp = p.complete(LLMRequest(prompt="please extract this", system=""))
    assert resp.text == "extracted-content"
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0


def test_mock_falls_through_keywords_in_order():
    p = MockLLMProvider(responses={"alpha": "A", "beta": "B"})
    resp = p.complete(LLMRequest(prompt="contains beta only"))
    assert resp.text == "B"


def test_mock_raises_when_no_match():
    p = MockLLMProvider(responses={"alpha": "A"})
    with pytest.raises(NoMockResponseConfigured):
        p.complete(LLMRequest(prompt="no match"))


def test_mock_records_calls_for_assertions():
    p = MockLLMProvider(responses={"x": "y"})
    p.complete(LLMRequest(prompt="contains x", system="sys"))
    assert len(p.calls) == 1
    assert p.calls[0].prompt == "contains x"
    assert p.calls[0].system == "sys"


def test_mock_default_name_is_mock():
    p = MockLLMProvider(responses={"hi": "hello"})
    assert p.name == "mock"


def test_mock_accepts_name_override():
    from agentsuite.llm.mock import _default_mock_for_cli

    p = MockLLMProvider(responses={"hi": "hello"}, name="ollama")
    assert p.name == "ollama"
    assert _default_mock_for_cli(provider_name="gemini").name == "gemini"
    assert _default_mock_for_cli().name == "mock"
