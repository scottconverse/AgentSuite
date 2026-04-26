"""Google Gemini provider."""
from __future__ import annotations

from typing import Any

from agentsuite.llm.base import LLMRequest, LLMResponse


# USD per million tokens — pinned at v0.x; update on bump
_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-pro": {"in": 1.25, "out": 10.0},
    "gemini-2.5-flash": {"in": 0.30, "out": 2.50},
    "gemini-2.5-flash-lite": {"in": 0.10, "out": 0.40},
}


def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    rates = _PRICING.get(model, {"in": 1.25, "out": 10.0})
    return (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000


class GeminiProvider:
    """Adapter for Google Gemini API conforming to LLMProvider."""

    name = "gemini"

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            import google.generativeai as genai

            client = genai
        self.client = client

    def default_model(self) -> str:
        return "gemini-2.5-flash"

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model()
        gen_model = self.client.GenerativeModel(
            model_name=model,
            system_instruction=request.system or None,
        )
        result = gen_model.generate_content(
            request.prompt,
            generation_config={
                "max_output_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
        )
        text = result.text
        usage = result.usage_metadata
        in_tokens = usage.prompt_token_count
        out_tokens = usage.candidates_token_count
        return LLMResponse(
            text=text,
            model=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd=_cost_usd(model, in_tokens, out_tokens),
        )
