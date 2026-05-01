"""Unit tests for llm.mock — deterministic stub provider for tests."""
import pytest

from agentsuite.llm.base import LLMRequest
from agentsuite.llm.mock import MockLLMProvider, NoMockResponseConfigured, SequentialMockLLMProvider


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


# ===========================================================================
# TEST-002: SequentialMockLLMProvider
# ===========================================================================

def _req(prompt: str, system: str = "") -> LLMRequest:
    return LLMRequest(prompt=prompt, system=system)


# ---------------------------------------------------------------------------
# 1. Cycle through responses in sequence
# ---------------------------------------------------------------------------

def test_sequential_returns_responses_in_order() -> None:
    """Provider pops items from the front of the sequence, in order."""
    provider = SequentialMockLLMProvider(
        sequences={"hello": ["first", "second", "third"]}
    )
    assert provider.complete(_req("hello world")).text == "first"
    assert provider.complete(_req("hello world")).text == "second"
    assert provider.complete(_req("hello world")).text == "third"


def test_sequential_last_item_repeated_indefinitely() -> None:
    """Once the sequence is down to one item it repeats rather than raising."""
    provider = SequentialMockLLMProvider(
        sequences={"ping": ["once", "always"]}
    )
    assert provider.complete(_req("ping")).text == "once"
    assert provider.complete(_req("ping")).text == "always"
    assert provider.complete(_req("ping")).text == "always"
    assert provider.complete(_req("ping")).text == "always"


def test_sequential_single_item_sequence_always_repeats() -> None:
    """A one-item sequence behaves like MockLLMProvider — always the same reply."""
    provider = SequentialMockLLMProvider(sequences={"key": ["constant"]})
    for _ in range(5):
        assert provider.complete(_req("key phrase")).text == "constant"


# ---------------------------------------------------------------------------
# 2. NoMockResponseConfigured raised for unmatched prompts
#    (SequentialMockLLMProvider repeats the last item — it does not raise
#     StopIteration — but unmatched prompts raise NoMockResponseConfigured.)
# ---------------------------------------------------------------------------

def test_sequential_raises_for_unmatched_prompt() -> None:
    """NoMockResponseConfigured is raised when no keyword matches."""
    provider = SequentialMockLLMProvider(sequences={"extracting": ["reply"]})
    with pytest.raises(NoMockResponseConfigured):
        provider.complete(_req("scoring artifacts for the run"))


def test_sequential_error_message_contains_keyword_list() -> None:
    """Exception message names the configured keywords to aid debugging."""
    provider = SequentialMockLLMProvider(sequences={"extracting-context": ["x"]})
    with pytest.raises(NoMockResponseConfigured, match="extracting-context"):
        provider.complete(_req("scoring artifacts for the run"))


# ---------------------------------------------------------------------------
# 3. reset() — the canonical reset pattern is re-instantiation (the class
#    keeps mutable copies so the caller's original list is untouched).
# ---------------------------------------------------------------------------

def test_sequential_does_not_mutate_caller_list() -> None:
    """Sequences are deep-copied; the caller's original list is unchanged."""
    original = ["a", "b", "c"]
    provider = SequentialMockLLMProvider(sequences={"k": original})
    provider.complete(_req("k"))
    provider.complete(_req("k"))
    assert original == ["a", "b", "c"], "SequentialMockLLMProvider must not mutate caller data"


def test_sequential_reinstantiation_resets_to_start() -> None:
    """A fresh instance with the same sequences starts from position 0."""
    sequences = {"item": ["first", "second"]}
    p1 = SequentialMockLLMProvider(sequences=sequences)
    assert p1.complete(_req("item")).text == "first"
    # Re-instantiate — must start fresh
    p2 = SequentialMockLLMProvider(sequences=sequences)
    assert p2.complete(_req("item")).text == "first"


# ---------------------------------------------------------------------------
# 4. Longest-match-first response selection
# ---------------------------------------------------------------------------

def test_sequential_longest_keyword_wins_over_shorter_prefix() -> None:
    """Longer keyword takes priority when multiple keywords match."""
    provider = SequentialMockLLMProvider(
        sequences={
            "brand": ["generic-brand"],
            "brand-system": ["specific-brand-system"],
        }
    )
    result = provider.complete(_req("writing brand-system.md for the project"))
    assert result.text == "specific-brand-system", (
        "Longest-match-first must select 'brand-system' over 'brand'"
    )


def test_sequential_shorter_keyword_used_when_longer_absent() -> None:
    """When only the short keyword matches, the short keyword is used."""
    provider = SequentialMockLLMProvider(
        sequences={
            "brand": ["short-match"],
            "brand-system": ["long-match"],
        }
    )
    result = provider.complete(_req("update brand guidelines only"))
    assert result.text == "short-match"


def test_sequential_three_keywords_longest_wins() -> None:
    """Among three candidates the longest matching key wins."""
    provider = SequentialMockLLMProvider(
        sequences={
            "a": ["shortest"],
            "ab": ["medium"],
            "abc": ["longest"],
        }
    )
    assert provider.complete(_req("abc sequence")).text == "longest"


def test_sequential_system_field_also_matched() -> None:
    """Keywords are searched in both prompt and system fields."""
    provider = SequentialMockLLMProvider(
        sequences={"system-keyword": ["found-in-system"]}
    )
    result = provider.complete(_req(prompt="no keyword here", system="system-keyword present"))
    assert result.text == "found-in-system"


# ---------------------------------------------------------------------------
# 5. Edge case: empty sequences dict
# ---------------------------------------------------------------------------

def test_sequential_empty_sequences_raises_for_any_call() -> None:
    """An empty sequences dict always raises NoMockResponseConfigured."""
    provider = SequentialMockLLMProvider(sequences={})
    with pytest.raises(NoMockResponseConfigured):
        provider.complete(_req("anything at all"))


# ---------------------------------------------------------------------------
# 6. Call recording
# ---------------------------------------------------------------------------

def test_sequential_calls_list_records_every_request() -> None:
    """provider.calls accumulates every LLMRequest in insertion order."""
    provider = SequentialMockLLMProvider(sequences={"x": ["r1", "r2"]})
    provider.complete(_req("x first"))
    provider.complete(_req("x second"))
    assert len(provider.calls) == 2
    assert provider.calls[0].prompt == "x first"
    assert provider.calls[1].prompt == "x second"


# ---------------------------------------------------------------------------
# 7. LLMResponse shape
# ---------------------------------------------------------------------------

def test_sequential_uses_provider_default_model() -> None:
    """When request.model is None, the provider's default_model is used."""
    provider = SequentialMockLLMProvider(
        sequences={"q": ["answer"]}, default_model="mock-seq-custom"
    )
    r = provider.complete(_req("q"))
    assert r.model == "mock-seq-custom"


def test_sequential_usd_is_zero() -> None:
    """Mock provider always returns usd=0.0."""
    provider = SequentialMockLLMProvider(sequences={"q": ["answer"]})
    assert provider.complete(_req("q")).usd == 0.0


def test_sequential_output_tokens_reflect_word_count() -> None:
    """output_tokens is the word count of the response text (>= 1)."""
    provider = SequentialMockLLMProvider(sequences={"q": ["one two three four"]})
    assert provider.complete(_req("q")).output_tokens == 4


# ---------------------------------------------------------------------------
# 8. name and default_model()
# ---------------------------------------------------------------------------

def test_sequential_class_default_name() -> None:
    assert SequentialMockLLMProvider(sequences={}).name == "mock-sequential"


def test_sequential_custom_name_overrides_default() -> None:
    provider = SequentialMockLLMProvider(sequences={}, name="anthropic")
    assert provider.name == "anthropic"


def test_sequential_default_model_method() -> None:
    provider = SequentialMockLLMProvider(sequences={}, default_model="my-model")
    assert provider.default_model() == "my-model"
