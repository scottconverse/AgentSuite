"""Unit tests for the centralized pricing module."""
from agentsuite.llm.pricing import (
    ANTHROPIC_PRICING,
    GEMINI_PRICING,
    OPENAI_PRICING,
)


def test_anthropic_pricing_has_known_models():
    assert "claude-sonnet-4-6" in ANTHROPIC_PRICING
    assert "claude-opus-4-7" in ANTHROPIC_PRICING
    assert "claude-haiku-4-5-20251001" in ANTHROPIC_PRICING


def test_openai_pricing_has_known_models():
    assert "gpt-5" in OPENAI_PRICING
    assert "gpt-4.1" in OPENAI_PRICING
    assert "gpt-4o-mini" in OPENAI_PRICING


def test_gemini_pricing_has_known_models():
    assert "gemini-2.5-pro" in GEMINI_PRICING
    assert "gemini-2.5-flash" in GEMINI_PRICING
    assert "gemini-2.5-flash-lite" in GEMINI_PRICING


def test_all_pricing_entries_have_in_and_out_keys():
    for table in (ANTHROPIC_PRICING, OPENAI_PRICING, GEMINI_PRICING):
        for model, rates in table.items():
            assert "in" in rates, f"{model} missing 'in' rate"
            assert "out" in rates, f"{model} missing 'out' rate"
            assert isinstance(rates["in"], (int, float))
            assert isinstance(rates["out"], (int, float))
