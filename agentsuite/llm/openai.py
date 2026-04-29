"""OpenAI Chat Completions provider."""
from __future__ import annotations

from typing import Any

from agentsuite.llm.base import LLMRequest, LLMResponse, ProviderNotInstalled
from agentsuite.llm.pricing import OPENAI_PRICING as _PRICING  # back-compat re-export
from agentsuite.llm.pricing import cost_usd as _provider_cost_usd


def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    """Per-provider thin wrapper around pricing.cost_usd."""
    return _provider_cost_usd("openai", model, in_tokens, out_tokens)


class OpenAIProvider:
    """Adapter for OpenAI's Chat Completions API conforming to LLMProvider."""
    name = "openai"

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ProviderNotInstalled(
                    "OpenAI SDK not installed. Run: pip install \"agentsuite[openai]\""
                ) from exc
            client = OpenAI()
        self.client = client

    def default_model(self) -> str:
        return "gpt-5.4"

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
            messages=messages,  # type: ignore[arg-type]
        )
        text = result.choices[0].message.content or ""
        if result.usage is None:
            raise RuntimeError("OpenAI returned no usage info")
        in_tokens = result.usage.prompt_tokens
        out_tokens = result.usage.completion_tokens
        return LLMResponse(
            text=text,
            model=result.model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd=_cost_usd(result.model, in_tokens, out_tokens),
        )
