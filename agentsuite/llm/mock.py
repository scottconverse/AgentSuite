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


def _default_mock_for_cli(provider_name: str | None = None) -> "MockLLMProvider":
    """Default mock provider used by tests + CLI smoke-runs when no real provider is configured.

    ``provider_name`` lets a caller simulate any concrete provider's identity
    (anthropic / openai / gemini / ollama) on the returned mock — useful for
    tests that gate behavior on ``provider.name``.
    """
    import json as _json

    from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
    from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS

    extracted = {
        "mission": "x",
        "audience": {"primary_persona": "y", "secondary_personas": []},
        "positioning": "z",
        "tone_signals": ["practical"],
        "visual_signals": [],
        "recurring_claims": [],
        "recurring_vocabulary": [],
        "prohibited_language": [],
        "gaps": [],
    }
    responses = {
        "extracting": _json.dumps(extracted),
        "checking 9 artifacts": _json.dumps({"mismatches": []}),
        "scoring 9 founder": _json.dumps({
            "scores": {d.name: 8.0 for d in FOUNDER_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\nMocked content."
    return MockLLMProvider(responses=responses, name=provider_name or "mock")
