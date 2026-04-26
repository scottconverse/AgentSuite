"""Centralized LLM pricing tables.

USD per million tokens (input / output). Pinned at v0.x; update on bump.
Each provider imports its slice and uses it via the shared `_cost_usd` helper
(which lives in each provider for now to avoid a circular shape change).
"""
from __future__ import annotations


ANTHROPIC_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"in": 3.0, "out": 15.0},
    "claude-opus-4-7": {"in": 15.0, "out": 75.0},
    "claude-haiku-4-5-20251001": {"in": 0.25, "out": 1.25},
}

OPENAI_PRICING: dict[str, dict[str, float]] = {
    "gpt-5": {"in": 5.0, "out": 15.0},
    "gpt-4.1": {"in": 2.5, "out": 10.0},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
}

GEMINI_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-pro": {"in": 1.25, "out": 10.0},
    "gemini-2.5-flash": {"in": 0.30, "out": 2.50},
    "gemini-2.5-flash-lite": {"in": 0.10, "out": 0.40},
}
