"""Google Gemini provider."""
from __future__ import annotations

from typing import Any

from agentsuite.llm.base import LLMRequest, LLMResponse, ProviderNotInstalled
from agentsuite.llm.pricing import GEMINI_PRICING as _PRICING  # noqa: F401  # back-compat re-export for existing tests
from agentsuite.llm.pricing import cost_usd as _provider_cost_usd


def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    """Per-provider thin wrapper around pricing.cost_usd."""
    return _provider_cost_usd("gemini", model, in_tokens, out_tokens)


class GeminiProvider:
    """Adapter for Google Gemini API conforming to LLMProvider."""

    name = "gemini"

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            import os
            try:
                from google import genai
            except ImportError as exc:
                raise ProviderNotInstalled(
                    "Google Generative AI SDK not installed. Run: pip install \"agentsuite[gemini]\""
                ) from exc
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", ""))
        self.client = client

    def default_model(self) -> str:
        return "gemini-2.5-flash"

    def complete(self, request: LLMRequest) -> LLMResponse:
        from google.genai import types as genai_types

        model = request.model or self.default_model()
        config = genai_types.GenerateContentConfig(
            max_output_tokens=request.max_tokens,
            temperature=request.temperature,
            system_instruction=request.system or None,
        )
        result = self.client.models.generate_content(
            model=model,
            contents=request.prompt,
            config=config,
        )
        text: str = result.text or ""
        usage = result.usage_metadata
        in_tokens: int = (usage.prompt_token_count or 0) if usage else 0
        out_tokens: int = (usage.candidates_token_count or 0) if usage else 0
        return LLMResponse(
            text=text,
            model=getattr(result, 'model_version', None) or model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd=_cost_usd(model, in_tokens, out_tokens),
        )
