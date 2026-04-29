"""Anthropic Messages API provider."""
from __future__ import annotations

from typing import Any

from agentsuite.llm.base import LLMRequest, LLMResponse, ProviderNotInstalled
from agentsuite.llm.pricing import ANTHROPIC_PRICING as _PRICING  # back-compat re-export
from agentsuite.llm.pricing import cost_usd as _provider_cost_usd


def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    """Per-provider thin wrapper around pricing.cost_usd."""
    return _provider_cost_usd("anthropic", model, in_tokens, out_tokens)


class AnthropicProvider:
    """Adapter for Anthropic's Messages API conforming to LLMProvider."""
    name = "anthropic"

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            try:
                from anthropic import Anthropic
            except ImportError as exc:
                raise ProviderNotInstalled(
                    "Anthropic SDK not installed. Run: pip install \"agentsuite[anthropic]\""
                ) from exc
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
