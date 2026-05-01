"""Deterministic mock LLM provider for tests."""
from __future__ import annotations

from agentsuite.llm.base import LLMRequest, LLMResponse


class NoMockResponseConfigured(RuntimeError):
    """Raised when MockLLMProvider has no canned response matching the prompt."""


class MockLLMProvider:
    """Test stub that returns canned responses keyed by prompt substrings."""
    name = "mock"

    def __init__(
        self,
        responses: dict[str, str],
        *,
        default_model: str = "mock-1",
        name: str | None = None,
    ) -> None:
        self.responses = responses
        self._default_model = default_model
        self.calls: list[LLMRequest] = []
        if name is not None:
            self.name = name  # instance attr shadows class attr

    def default_model(self) -> str:
        return self._default_model

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Match the request to a canned response.

        TEST-003 (audit): match by *longest* matching keyword rather than
        dict-insertion order. With insertion-order matching, ``responses =
        {"brand": ..., "brand-system": ...}`` would return the ``brand``
        response for a ``brand-system`` prompt -- a silent prompt-drift
        masking pattern. With length-descending matching, the most-specific
        keyword wins. ``NoMockResponseConfigured`` still raises on no match
        so test authors cannot accidentally rely on a default response.
        """
        self.calls.append(request)
        # Sort by keyword length descending so the most-specific match wins.
        # Stable for ties via dict insertion order (Python >= 3.7).
        items = sorted(self.responses.items(), key=lambda kv: -len(kv[0]))
        for keyword, text in items:
            if keyword in request.prompt or keyword in request.system:
                return LLMResponse(
                    text=text,
                    model=request.model or self._default_model,
                    input_tokens=max(len(request.prompt.split()), 1),
                    output_tokens=max(len(text.split()), 1),
                    usd=0.0,
                )
        raise NoMockResponseConfigured(
            f"No canned response for prompt: {request.prompt[:80]!r}. "
            f"Configured keywords: {list(self.responses.keys())}"
        )


class SequentialMockLLMProvider:
    """Mock provider that returns responses in sequence for each matching key.

    Unlike ``MockLLMProvider`` (which always returns the same canned response),
    each key in ``sequences`` maps to an ordered list of responses. The first
    call to a matching key pops and returns the first item; subsequent calls
    return the next item, repeating the last item indefinitely once the list
    is exhausted.

    Useful for testing pipelines where the same prompt pattern fires N times
    but you want to inject a bad response on a specific call (e.g. the 5th
    artifact generation, or the second QA attempt).

    The longest-match-first rule from ``MockLLMProvider`` applies: when
    multiple keys match, the longest key wins.
    """
    name = "mock-sequential"

    def __init__(
        self,
        sequences: dict[str, list[str]],
        *,
        default_model: str = "mock-seq-1",
        name: str | None = None,
    ) -> None:
        # Store mutable copies so callers can't mutate our state
        self.sequences: dict[str, list[str]] = {k: list(v) for k, v in sequences.items()}
        self._default_model = default_model
        self.calls: list[LLMRequest] = []
        if name is not None:
            self.name = name

    def default_model(self) -> str:
        return self._default_model

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        items = sorted(self.sequences.items(), key=lambda kv: -len(kv[0]))
        for keyword, seq in items:
            if keyword in request.prompt or keyword in request.system:
                if len(seq) > 1:
                    text = seq.pop(0)
                else:
                    text = seq[0]  # repeat last item indefinitely
                return LLMResponse(
                    text=text,
                    model=request.model or self._default_model,
                    input_tokens=max(len(request.prompt.split()), 1),
                    output_tokens=max(len(text.split()), 1),
                    usd=0.0,
                )
        raise NoMockResponseConfigured(
            f"No canned response for prompt: {request.prompt[:80]!r}. "
            f"Configured keywords: {list(self.sequences.keys())}"
        )


def _default_mock_for_cli(provider_name: str | None = None) -> "MockLLMProvider":
    """Default mock provider used by tests + CLI smoke-runs when no real provider is configured.

    Assembles per-agent responses by calling each agent's ``build_mock_responses()``
    helper. Adding a new agent requires only adding that agent's ``build_mock_responses``
    function -- no change to this file.

    ``provider_name`` lets a caller simulate any concrete provider's identity
    (anthropic / openai / gemini / ollama) on the returned mock -- useful for
    tests that gate behavior on ``provider.name``.
    """
    from agentsuite.agents.cio.testing import build_mock_responses as _cio
    from agentsuite.agents.design.testing import build_mock_responses as _design
    from agentsuite.agents.engineering.testing import build_mock_responses as _engineering
    from agentsuite.agents.founder.testing import build_mock_responses as _founder
    from agentsuite.agents.marketing.testing import build_mock_responses as _marketing
    from agentsuite.agents.product.testing import build_mock_responses as _product
    from agentsuite.agents.trust_risk.testing import build_mock_responses as _trust_risk

    responses: dict[str, str] = {}
    for builder in (_founder, _design, _product, _engineering, _marketing, _trust_risk, _cio):
        responses.update(builder())
    return MockLLMProvider(responses=responses, name=provider_name or "mock")
