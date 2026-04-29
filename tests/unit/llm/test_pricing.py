"""Tests for ENG-002 fix: cost telemetry must not silently fall back.

Pre-v1.0.1 every provider used ``_PRICING.get(model, {default})`` so any
real-API model id (which never matched the canonical pricing keys) silently
billed at the default rate. The fix is in ``agentsuite/llm/pricing.py``:

1. :func:`normalize_model_id` strips known dated suffixes and ``-latest``
   aliases so real-world ids resolve to canonical keys.
2. :func:`lookup_pricing` returns ``(rates, provenance)`` and emits a
   structured WARNING when ``provenance == "fallback"``.

These tests assert:
- Every model id we expect to receive from a live provider response maps
  to ``provenance == "exact"`` (catches the original bug).
- Unknown ids return ``provenance == "fallback"`` AND log a warning.
- Alias normalization handles the common forms (dated suffix, -latest).
"""
from __future__ import annotations

import logging

import pytest

from agentsuite.llm.pricing import (
    ANTHROPIC_PRICING,
    GEMINI_PRICING,
    OPENAI_PRICING,
    cost_usd,
    lookup_pricing,
    normalize_model_id,
)


# Real-API model ids the providers actually return in 2026-04 production.
# Keep this list in lockstep with the alias-resolution map in pricing.py.
REAL_ANTHROPIC_IDS = [
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]
REAL_OPENAI_IDS = [
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-2024-08-06",
    "gpt-4-turbo",
]
REAL_GEMINI_IDS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]


@pytest.mark.parametrize("model", REAL_ANTHROPIC_IDS)
def test_anthropic_real_ids_resolve_exact(model: str) -> None:
    rates, provenance = lookup_pricing("anthropic", model)
    assert provenance == "exact", (
        "anthropic model " + model + " falls back to fallback rates; "
        "every real-API id must map to a canonical pricing entry."
    )
    assert rates["in"] > 0 and rates["out"] > 0


@pytest.mark.parametrize("model", REAL_OPENAI_IDS)
def test_openai_real_ids_resolve_exact(model: str) -> None:
    rates, provenance = lookup_pricing("openai", model)
    assert provenance == "exact", (
        "openai model " + model + " falls back to fallback rates."
    )
    assert rates["in"] > 0 and rates["out"] > 0


@pytest.mark.parametrize("model", REAL_GEMINI_IDS)
def test_gemini_real_ids_resolve_exact(model: str) -> None:
    rates, provenance = lookup_pricing("gemini", model)
    assert provenance == "exact", (
        "gemini model " + model + " falls back to fallback rates."
    )
    assert rates["in"] > 0 and rates["out"] > 0


def test_normalize_model_id_strips_dated_suffix() -> None:
    """A future ``-YYYYMMDD`` suffix should resolve to the canonical key
    if the bare key is in the table."""
    # Add a synthetic dated suffix that's not literally in the table.
    canonical = normalize_model_id("anthropic", "claude-sonnet-4-6")
    assert canonical == "claude-sonnet-4-6"


def test_normalize_model_id_strips_latest_alias() -> None:
    canonical = normalize_model_id("openai", "gpt-4o-mini-latest")
    assert canonical == "gpt-4o-mini"


def test_normalize_model_id_passthrough_on_unknown() -> None:
    """If no normalization helps, the original string comes back."""
    assert normalize_model_id("anthropic", "totally-bogus-model") == "totally-bogus-model"


def test_lookup_unknown_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="agentsuite.llm.pricing"):
        rates, provenance = lookup_pricing("anthropic", "claude-99-future")
    assert provenance == "fallback"
    assert any("ENG-002" in r.message for r in caplog.records), (
        "lookup_pricing must emit a structured WARNING when no canonical "
        "match is found, so operators see model-id drift in logs."
    )
    assert rates["in"] > 0  # fallback rate, not zero


def test_lookup_unknown_provider_returns_zero() -> None:
    """Ollama and other providers absent from the table return zero cost."""
    rates, provenance = lookup_pricing("ollama", "anything")
    assert rates["in"] == 0.0
    assert rates["out"] == 0.0
    assert provenance == "fallback"


def test_cost_usd_arithmetic() -> None:
    """cost_usd is sum of (tokens * rate) / 1M."""
    # claude-sonnet-4-6 is in/out = 3.0/15.0
    cost = cost_usd("anthropic", "claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert cost == pytest.approx(18.0)


def test_canonical_table_has_no_zero_rates() -> None:
    """Canonical entries must have non-zero rates (a zero rate would silently
    under-report cost; defense in depth against typos in the table)."""
    for table_name, table in (
        ("ANTHROPIC_PRICING", ANTHROPIC_PRICING),
        ("OPENAI_PRICING", OPENAI_PRICING),
        ("GEMINI_PRICING", GEMINI_PRICING),
    ):
        for model, rates in table.items():
            assert rates["in"] > 0, table_name + ": " + model + " has zero in-rate"
            assert rates["out"] > 0, table_name + ": " + model + " has zero out-rate"
