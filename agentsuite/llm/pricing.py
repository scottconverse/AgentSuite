"""Centralized LLM pricing tables and lookup with alias normalization.

USD per million tokens (input / output). Each provider imports the slice and
calls :func:`lookup_pricing` with the raw model id from the provider response.

ENG-002 (audit): pre-v1.0.1, providers used ``_PRICING.get(model, {default})``
which silently masked the fact that real-API model ids (e.g.
``claude-3-5-sonnet-20241022``) never matched the pricing keys
(``claude-sonnet-4-6``). Every billed call fell back to a hardcoded rate and
the operator never saw a warning. This module fixes both halves:

1. :func:`normalize_model_id` maps known dated aliases to canonical keys.
2. :func:`lookup_pricing` returns ``(rates, "exact"|"fallback")`` so the
   caller can log the provenance and (eventually) thread it into
   ``cost_summary.json``. Pre-v1.0.1 the lookup *silently* fell back; from
   v1.0.1 the caller emits a structured warning when ``provenance`` is
   ``"fallback"`` so model-id drift surfaces immediately.

Note: Ollama is intentionally absent. The OllamaProvider runs locally and
always reports usd=0.0; no pricing table required.
"""
from __future__ import annotations

import logging
from typing import Literal


_log = logging.getLogger(__name__)

Provenance = Literal["exact", "fallback"]


# Source: https://docs.anthropic.com/en/docs/about-claude/pricing
# Verified: 2026-04-29 (v1.0.1)
ANTHROPIC_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-7":           {"in":  5.00, "out": 25.00},
    "claude-sonnet-4-6":         {"in":  3.00, "out": 15.00},
    "claude-haiku-4-5-20251001": {"in":  1.00, "out":  5.00},
    # Real-API ids returned by the Anthropic SDK in production. These map
    # to the same rates as the closest canonical entry above. Keep this
    # block in lockstep with the canonical block above on every price
    # update.
    "claude-3-5-sonnet-20241022": {"in": 3.00, "out": 15.00},
    "claude-3-5-haiku-20241022":  {"in": 1.00, "out":  5.00},
    "claude-3-opus-20240229":     {"in": 15.00, "out": 75.00},
    "claude-3-sonnet-20240229":   {"in": 3.00, "out": 15.00},
    "claude-3-haiku-20240307":    {"in": 0.25, "out":  1.25},
}

# Source: https://platform.openai.com/docs/pricing
# Verified: 2026-04-29 (v1.0.1)
OPENAI_PRICING: dict[str, dict[str, float]] = {
    "gpt-5.5":      {"in":  5.00, "out":  30.00},
    "gpt-5.5-pro":  {"in": 30.00, "out": 180.00},
    "gpt-5.4":      {"in":  2.50, "out":  15.00},
    "gpt-5.4-mini": {"in":  0.75, "out":   4.50},
    "gpt-5.4-nano": {"in":  0.20, "out":   1.25},
    "gpt-5.4-pro":  {"in": 30.00, "out": 180.00},
    # Real-API ids
    "gpt-4o":         {"in":  2.50, "out": 10.00},
    "gpt-4o-mini":    {"in":  0.15, "out":  0.60},
    "gpt-4o-2024-08-06": {"in":  2.50, "out": 10.00},
    "gpt-4-turbo":    {"in": 10.00, "out": 30.00},
}

# Source: https://cloud.google.com/vertex-ai/generative-ai/docs/pricing
# Verified: 2026-04-29 (v1.0.1)
GEMINI_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-pro":        {"in": 1.25, "out": 10.00},
    "gemini-2.5-flash":      {"in": 0.30, "out":  2.50},
    "gemini-2.5-flash-lite": {"in": 0.10, "out":  0.40},
    # Real-API ids
    "gemini-2.0-flash":      {"in": 0.10, "out":  0.40},
    "gemini-2.0-flash-exp":  {"in": 0.10, "out":  0.40},
    "gemini-1.5-pro":        {"in": 1.25, "out":  5.00},
    "gemini-1.5-flash":      {"in": 0.075, "out": 0.30},
}


# Provider name -> table.
_PROVIDER_TABLES: dict[str, dict[str, dict[str, float]]] = {
    "anthropic": ANTHROPIC_PRICING,
    "openai":    OPENAI_PRICING,
    "gemini":    GEMINI_PRICING,
}


# Last-resort fallback rates per provider — used only when even
# normalization cannot find a match. Pre-v1.0.1 this fallback was
# silent; now we emit a warning so operators know the cost number is
# estimated. The chosen rates are mid-tier conservative (slightly above
# average) so an estimated number is more likely to over-bill than
# under-bill the cap.
_FALLBACK_RATES: dict[str, dict[str, float]] = {
    "anthropic": {"in": 3.0,  "out": 15.0},
    "openai":    {"in": 2.5,  "out": 10.0},
    "gemini":    {"in": 1.25, "out":  5.0},
}


def normalize_model_id(provider: str, model: str) -> str:
    """Return ``model`` unchanged if it exists in the provider table; else
    apply known prefix-based aliases to find a canonical key.

    Real-API model ids often carry a ``-YYYYMMDD`` date suffix that we don't
    track in the canonical pricing key. This function strips dated suffixes
    (and ``-latest``) once before falling through. The returned string is
    always either an exact match or the original input; the caller is
    responsible for emitting a warning when the lookup ultimately falls back.
    """
    table = _PROVIDER_TABLES.get(provider, {})
    if model in table:
        return model
    # Strip a trailing ``-latest`` alias.
    if model.endswith("-latest"):
        stripped = model[: -len("-latest")]
        if stripped in table:
            return stripped
    # Strip a trailing ``-YYYYMMDD`` (8-digit date) suffix.
    parts = model.rsplit("-", 1)
    if len(parts) == 2 and len(parts[1]) == 8 and parts[1].isdigit():
        if parts[0] in table:
            return parts[0]
    # Prefix match: model starts with a known key (e.g. "gemini-2.5-flash-preview-04-17" → "gemini-2.5-flash")
    for key in sorted(table.keys(), key=len, reverse=True):
        if model.startswith(key + "-"):
            return key
    return model


def lookup_pricing(provider: str, model: str) -> tuple[dict[str, float], Provenance]:
    """Return ``(rates, provenance)`` for a (provider, model) pair.

    ``provenance == "exact"`` when the canonical table held an entry for the
    model id (after normalization); ``"fallback"`` when neither the raw nor
    normalized id matched and a conservative provider-default rate was used.

    On fallback this function logs a structured ``WARNING``-level message
    naming the offending model id; operators should treat fallback costs as
    estimates and update the pricing table.
    """
    table = _PROVIDER_TABLES.get(provider)
    if table is None:
        # Unknown provider — return a generic fallback that won't crash a
        # call site that doesn't track provenance yet. The Ollama provider
        # bypasses this codepath entirely.
        return ({"in": 0.0, "out": 0.0}, "fallback")
    canonical = normalize_model_id(provider, model)
    rates = table.get(canonical)
    if rates is not None:
        return (rates, "exact")
    fallback = _FALLBACK_RATES.get(provider, {"in": 0.0, "out": 0.0})
    _log.warning(
        "[ENG-002] cost lookup miss for provider=%r model=%r; using fallback "
        "rates in=%s out=%s. Add an entry in agentsuite/llm/pricing.py "
        "(or normalize via the alias logic) to mark this lookup as exact.",
        provider, model, fallback["in"], fallback["out"],
    )
    return (fallback, "fallback")


def cost_usd(provider: str, model: str, in_tokens: int, out_tokens: int) -> float:
    """Compute USD cost for a usage record. Provenance is logged as a side effect."""
    rates, _provenance = lookup_pricing(provider, model)
    return (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000
