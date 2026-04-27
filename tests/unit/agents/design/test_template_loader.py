"""Unit tests for agentsuite.agents.design.template_loader."""
import pytest

from agentsuite.agents.design.template_loader import (
    UnknownTemplate,
    list_templates,
    render_template,
)


def test_list_templates_returns_eight():
    names = list_templates()
    assert len(names) == 8


def test_list_templates_sorted():
    names = list_templates()
    assert names == sorted(names)


def test_all_expected_names_present():
    names = list_templates()
    for expected in [
        "banner-ad",
        "email-header",
        "social-graphic",
        "landing-hero",
        "deck-slide",
        "print-flyer",
        "video-thumbnail",
        "icon-set",
    ]:
        assert expected in names


def test_render_social_graphic():
    result = render_template(
        "social-graphic",
        product="Acme",
        target_audience="developers",
        campaign_goal="launch awareness",
        core_message="Ship faster",
        brand_voice="confident",
        visual_direction="bold typography",
        tone="punchy",
        format_constraint="1080x1080",
        required_text="Ship faster",
        exclusions="stock photos",
    )
    assert "Acme" in result
    assert "developers" in result


def test_render_banner_ad():
    result = render_template(
        "banner-ad",
        product="Acme",
        target_audience="SaaS buyers",
        campaign_goal="trial signups",
        core_message="Try free",
        brand_voice="direct",
        visual_direction="clean white bg",
        tone="urgent",
        format_constraint="728x90",
        required_text="Start free trial",
        exclusions="animated GIFs",
    )
    assert "SaaS buyers" in result
    assert "728x90" in result


def test_render_unknown_raises():
    with pytest.raises(UnknownTemplate):
        render_template("does-not-exist", product="X")


def test_render_missing_var_raises():
    with pytest.raises(Exception):
        render_template("social-graphic", product="X")  # missing required vars → StrictUndefined raises


def test_render_all_templates_smoke():
    common_vars = dict(
        product="AcmeCo",
        target_audience="devs",
        campaign_goal="adoption",
        core_message="Build better",
        brand_voice="friendly",
        visual_direction="modern",
        tone="upbeat",
        format_constraint="standard",
        required_text="Get started",
        exclusions="none",
    )
    for name in list_templates():
        result = render_template(name, **common_vars)
        assert len(result) > 50  # non-empty rendered output


def test_unknown_template_is_key_error():
    with pytest.raises(KeyError):
        render_template("nonexistent")
