"""Unit tests for the marketing agent prompt loader."""
from __future__ import annotations

import pytest

from agentsuite.agents.marketing.prompt_loader import (
    UnknownPrompt,
    list_prompts,
    render_prompt,
)

_EXPECTED_PROMPTS = [
    "extract",
    "intake",
    "spec_campaign_brief",
    "spec_channel_strategy",
    "spec_competitive_positioning",
    "spec_consistency_check",
    "spec_content_calendar",
    "spec_launch_plan",
    "spec_measurement_framework",
    "spec_messaging_framework",
    "spec_seo_keyword_plan",
    "spec_target_audience_profile",
]


def test_list_prompts_returns_12() -> None:
    """list_prompts() must return exactly 12 templates."""
    prompts = list_prompts()
    assert len(prompts) == 12, f"Expected 12 prompts, got {len(prompts)}: {prompts}"


def test_list_prompts_all_names_present() -> None:
    """All 12 required template names must be present."""
    prompts = list_prompts()
    for name in _EXPECTED_PROMPTS:
        assert name in prompts, f"Missing expected prompt: {name!r}"


def test_list_prompts_is_sorted() -> None:
    """list_prompts() must return names in sorted order."""
    prompts = list_prompts()
    assert prompts == sorted(prompts)


def test_render_intake() -> None:
    """intake template renders with required variables."""
    result = render_prompt(
        "intake",
        brand_name="Acme Corp",
        campaign_goal="increase trial sign-ups by 25%",
        target_market="SMB software buyers",
        source_count=3,
    )
    assert "Acme Corp" in result
    assert "increase trial sign-ups by 25%" in result
    assert "SMB software buyers" in result
    assert "3" in result


def test_render_extract() -> None:
    """extract template renders with required variables."""
    result = render_prompt(
        "extract",
        brand_name="Acme Corp",
        campaign_goal="launch new product line",
        target_market="enterprise IT managers",
        source_count=5,
        brand_docs="Brand doc content here.",
        competitor_docs="Competitor doc content here.",
    )
    assert "Acme Corp" in result
    assert "launch new product line" in result
    assert "audience_insights" in result
    assert "competitor_gaps" in result
    assert "open_questions" in result


def test_render_spec_campaign_brief() -> None:
    """spec_campaign_brief template renders with required spec variables."""
    result = render_prompt(
        "spec_campaign_brief",
        brand_name="Acme Corp",
        campaign_goal="grow market share",
        target_market="mid-market retail",
        budget_range="$50k–$100k",
        timeline="Q3 2025",
        channels="LinkedIn, email, paid search",
        extracted_context="Audience prefers ROI-focused messaging.",
    )
    assert "Acme Corp" in result
    assert "$50k–$100k" in result
    assert "Q3 2025" in result


def test_render_spec_consistency_check_uses_dict_iteration() -> None:
    """spec_consistency_check iterates artifact_snippets as a dict."""
    snippets = {
        "campaign_brief": "Goal: grow market share.",
        "messaging_framework": "Tone: confident and direct.",
        "measurement_framework": "KPI: market share percentage.",
    }
    result = render_prompt(
        "spec_consistency_check",
        brand_name="Acme Corp",
        campaign_goal="grow market share",
        artifact_snippets=snippets,
    )
    assert "campaign_brief" in result
    assert "messaging_framework" in result
    assert "Goal: grow market share." in result
    assert "Tone: confident and direct." in result


def test_render_unknown_prompt_raises() -> None:
    """render_prompt raises UnknownPrompt for a non-existent template name."""
    with pytest.raises(UnknownPrompt):
        render_prompt("nonexistent_prompt_xyz")


def test_unknown_prompt_is_key_error() -> None:
    """UnknownPrompt must be a subclass of KeyError."""
    assert issubclass(UnknownPrompt, KeyError)
