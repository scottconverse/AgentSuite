"""Anthropic Messages API provider."""
from __future__ import annotations

from typing import Any

from agentsuite.llm.base import LLMRequest, LLMResponse


# USD per million tokens (input / output) — pricing pinned at v0.1.0; update on bump.
_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"in": 3.0, "out": 15.0},
    "claude-opus-4-7": {"in": 15.0, "out": 75.0},
    "claude-haiku-4-5-20251001": {"in": 0.25, "out": 1.25},
}


def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    rates = _PRICING.get(model, {"in": 3.0, "out": 15.0})
    return (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000


class AnthropicProvider:
    """Adapter for Anthropic's Messages API conforming to LLMProvider."""
    name = "anthropic"

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            from anthropic import Anthropic

            client = Anthropic()
        self.client = client

    def default_model(self) -> str:
        return "claude-sonnet-4-6"

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model()
        result = self.client.messages.create(
            model=model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=request.system or "",
            messages=[{"role": "user", "content": request.prompt}],
        )
        text = "".join(block.text for block in result.content if hasattr(block, "text"))
        in_tokens = result.usage.input_tokens
        out_tokens = result.usage.output_tokens
        return LLMResponse(
            text=text,
            model=result.model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd=_cost_usd(result.model, in_tokens, out_tokens),
        )
