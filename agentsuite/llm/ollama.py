"""Ollama (local LLM) provider — zero cost, offline-capable."""
from __future__ import annotations

from typing import Any

from agentsuite.llm.base import LLMRequest, LLMResponse, ProviderNotInstalled


class OllamaProvider:
    """Adapter for Ollama's chat API. Always reports 0.0 USD cost."""

    name = "ollama"

    def __init__(self, client: Any | None = None, *, default_model: str = "gemma4:e4b") -> None:
        if client is None:
            try:
                import ollama as _ollama
            except ImportError as exc:
                raise ProviderNotInstalled(
                    "Ollama SDK not installed. Run: pip install \"agentsuite[ollama]\""
                ) from exc
            client = _ollama.Client()
        self.client = client
        self._default_model = default_model

    def default_model(self) -> str:
        return self._default_model

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model()
        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        result = self.client.chat(
            model=model,
            messages=messages,
            options={"temperature": request.temperature, "num_predict": request.max_tokens},
        )
        text = result["message"]["content"]
        in_tokens = result.get("prompt_eval_count", 0)
        out_tokens = result.get("eval_count", 0)
        return LLMResponse(
            text=text,
            model=result.get("model", model),
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd=0.0,
        )
