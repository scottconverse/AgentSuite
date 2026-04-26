"""LLM provider Protocol and shared types."""
from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict


class LLMRequest(BaseModel):
    """Request envelope for an LLM completion call."""

    model_config = ConfigDict(extra="forbid")

    prompt: str
    system: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0
    model: str | None = None  # provider chooses default if None


class LLMResponse(BaseModel):
    """Response envelope including usage + cost metadata."""

    model_config = ConfigDict(extra="forbid")

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    usd: float


class LLMProvider(Protocol):
    """Protocol implemented by Anthropic / OpenAI / Mock providers."""

    name: str

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Synchronous completion."""

    def default_model(self) -> str:
        """Return the default model id used when LLMRequest.model is None."""
