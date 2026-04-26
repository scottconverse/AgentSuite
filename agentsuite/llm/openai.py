"""OpenAI Chat Completions provider."""
from __future__ import annotations

from typing import Any

from agentsuite.llm.base import LLMRequest, LLMResponse


# USD per million tokens (input / output) — pricing pinned at v0.1.0; update on bump.
_PRICING: dict[str, dict[str, float]] = {
    "gpt-5": {"in": 5.0, "out": 15.0},
    "gpt-4.1": {"in": 2.5, "out": 10.0},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
}


def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    rates = _PRICING.get(model, {"in": 5.0, "out": 15.0})
    return (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000


class OpenAIProvider:
    """Adapter for OpenAI's Chat Completions API conforming to LLMProvider."""
    name = "openai"

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client

    def default_model(self) -> str:
        return "gpt-5"

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model()
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        result = self.client.chat.completions.create(
            model=model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=messages,
        )
        text = result.choices[0].message.content or ""
        in_tokens = result.usage.prompt_tokens
        out_tokens = result.usage.completion_tokens
        return LLMResponse(
            text=text,
            model=result.model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd=_cost_usd(result.model, in_tokens, out_tokens),
        )
