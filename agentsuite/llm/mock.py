"""Deterministic mock LLM provider for tests."""
from __future__ import annotations

from agentsuite.llm.base import LLMRequest, LLMResponse


class NoMockResponseConfigured(RuntimeError):
    """Raised when MockLLMProvider has no canned response matching the prompt."""


class MockLLMProvider:
    """Test stub that returns canned responses keyed by prompt substrings."""
    name = "mock"

    def __init__(self, responses: dict[str, str], *, default_model: str = "mock-1") -> None:
        self.responses = responses
        self._default_model = default_model
        self.calls: list[LLMRequest] = []

    def default_model(self) -> str:
        return self._default_model

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        for keyword, text in self.responses.items():
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
