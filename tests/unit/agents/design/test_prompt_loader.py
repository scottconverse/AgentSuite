"""Unit tests for design.prompt_loader."""
import pytest

from agentsuite.agents.design.prompt_loader import (
    UnknownPrompt,
    list_prompts,
    render_prompt,
)


def test_list_prompts_returns_all_known():
    names = list_prompts()
    assert "extract" in names
    assert "spec_design_brief" in names
    assert "consistency_check" in names
    assert "qa_score" in names


def test_load_prompt_returns_jinja2_template_object():
    """Confirm render_prompt succeeds and returns a non-empty string."""
    result = render_prompt(
        "extract",
        brand_docs="Style guide v2, brand deck",
        references="Dribbble shot X, Behance project Y",
        anti_examples="Competitor A website",
        campaign_goal="Launch new product line",
        target_audience="Millennial professionals aged 28-40",
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_load_prompt_renders_with_required_variables():
    """Render extract.jinja2 with sample vars; assert output non-empty + contains key directive words."""
    out = render_prompt(
        "extract",
        brand_docs="Annual report, brand guidelines PDF",
        references="Apple.com homepage, Stripe brand system",
        anti_examples="Generic stock-photo landing pages",
        campaign_goal="Launch premium membership tier",
        target_audience="Design-literate product managers at Series B+ startups",
    )
    assert len(out) > 50
    assert "audience_profile" in out or "brand_voice" in out or "JSON" in out or "visual_signals" in out


def test_load_prompt_raises_on_unknown_name():
    """load_prompt('does_not_exist') raises UnknownPrompt."""
    with pytest.raises(UnknownPrompt):
        render_prompt("does_not_exist")


def test_list_prompts_contains_all_twelve():
    """All 12 design prompt templates must be discoverable."""
    names = list_prompts()
    expected = [
        "extract",
        "spec_design_brief",
        "spec_brand_rules_extracted",
        "spec_visual_direction",
        "spec_image_generation_prompt",
        "spec_design_qa_report",
        "spec_revision_instructions",
        "spec_final_asset_acceptance_checklist",
        "spec_mood_board_spec",
        "spec_accessibility_audit_template",
        "consistency_check",
        "qa_score",
    ]
    for name in expected:
        assert name in names, f"Missing prompt template: {name}"


def test_render_prompt_substitutes_variables():
    """Variables passed to render_prompt appear in rendered output."""
    out = render_prompt(
        "spec_design_brief",
        campaign_goal="Holiday campaign 2025",
        target_audience="Gen Z consumers 18-25",
        brand_voice="Playful, irreverent, warm",
        extracted_context="Brand uses bold typography, primary red #D32F2F",
        deliverables="Hero banner, social card, email header",
    )
    assert "Holiday campaign 2025" in out
    assert "Gen Z consumers 18-25" in out
