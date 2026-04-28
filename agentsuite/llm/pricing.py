"""Centralized LLM pricing tables.

USD per million tokens (input / output). Pinned at v0.x; update on bump.
Each provider imports its slice and uses it via the shared `_cost_usd` helper
(which lives in each provider for now to avoid a circular shape change).

Note: Ollama is intentionally absent from this module. The OllamaProvider
runs a local daemon and always reports usd=0.0; no pricing table required.
"""
from __future__ import annotations


# Source: https://docs.anthropic.com/en/docs/about-claude/pricing
# Verified: 2026-04-27
ANTHROPIC_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-7":           {"in":  5.00, "out": 25.00},
    "claude-sonnet-4-6":         {"in":  3.00, "out": 15.00},
    "claude-haiku-4-5-20251001": {"in":  1.00, "out":  5.00},
}

# Source: https://platform.openai.com/docs/pricing
# Verified: 2026-04-27
OPENAI_PRICING: dict[str, dict[str, float]] = {
    "gpt-5.5":      {"in":  5.00, "out":  30.00},
    "gpt-5.5-pro":  {"in": 30.00, "out": 180.00},
    "gpt-5.4":      {"in":  2.50, "out":  15.00},
    "gpt-5.4-mini": {"in":  0.75, "out":   4.50},
    "gpt-5.4-nano": {"in":  0.20, "out":   1.25},
    "gpt-5.4-pro":  {"in": 30.00, "out": 180.00},
}

# Source: https://cloud.google.com/vertex-ai/generative-ai/docs/pricing
# Verified: 2026-04-27
GEMINI_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-pro":        {"in": 1.25, "out": 10.00},
    "gemini-2.5-flash":      {"in": 0.30, "out":  2.50},
    "gemini-2.5-flash-lite": {"in": 0.10, "out":  0.40},
}
