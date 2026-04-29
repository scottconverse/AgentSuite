"""TEST-003: MockLLMProvider must match the most-specific keyword, not the first.

Pre-v1.0.1 the matcher iterated ``self.responses.items()`` and returned the
first keyword that appeared in the prompt. Test authors who wrote
``{"brand": ..., "brand-system": ...}`` got a ``brand`` response for a
``brand-system`` prompt -- a silent prompt-drift masking pattern. Audit
finding TEST-003 flagged this as a Major. Fix: sort by keyword length
descending so the most-specific match wins.
"""
from __future__ import annotations

import pytest

from agentsuite.llm.base import LLMRequest
from agentsuite.llm.mock import MockLLMProvider, NoMockResponseConfigured


def _req(prompt: str, system: str = "") -> LLMRequest:
    return LLMRequest(prompt=prompt, system=system)


def test_longest_keyword_wins_when_both_match() -> None:
    provider = MockLLMProvider({
        "brand": "short-keyword response",
        "brand-system": "specific-keyword response",
    })
    response = provider.complete(_req("write the brand-system spec for Acme"))
    assert response.text == "specific-keyword response", (
        "MockLLMProvider should prefer the longer/more-specific keyword "
        "match. Got the short-keyword response, which masks prompt drift."
    )


def test_longest_match_independent_of_dict_order() -> None:
    """Dict insertion order must not matter -- length is the discriminator."""
    a = MockLLMProvider({"brand": "A", "brand-system": "B"})
    b = MockLLMProvider({"brand-system": "B", "brand": "A"})
    prompt = "write the brand-system spec"
    assert a.complete(_req(prompt)).text == "B"
    assert b.complete(_req(prompt)).text == "B"


def test_only_keyword_still_matches() -> None:
    """Single keyword in dict -> that response always returns."""
    provider = MockLLMProvider({"hello": "world"})
    assert provider.complete(_req("hello there")).text == "world"


def test_no_match_raises() -> None:
    provider = MockLLMProvider({"foo": "bar"})
    with pytest.raises(NoMockResponseConfigured):
        provider.complete(_req("totally different prompt"))


def test_system_field_is_searched_too() -> None:
    """Keyword can match in either prompt or system field."""
    provider = MockLLMProvider({"persona": "ok"})
    response = provider.complete(_req("hi", system="you are a persona"))
    assert response.text == "ok"


def test_empty_keyword_does_not_silently_swallow_everything() -> None:
    """An empty-string keyword would match every prompt; document the
    behavior explicitly so a future contributor cannot quietly add it."""
    provider = MockLLMProvider({"": "trap", "real": "wanted"})
    # With longest-match, "real" beats "" (len 4 > 0).
    assert provider.complete(_req("real prompt")).text == "wanted"
    # If only the empty keyword exists, it does match (consistent with the
    # original semantics — empty substring is in every string).
    only_empty = MockLLMProvider({"": "trap"})
    assert only_empty.complete(_req("anything")).text == "trap"
