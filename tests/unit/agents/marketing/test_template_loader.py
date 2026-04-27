"""Unit tests for marketing.template_loader."""
import pytest

from agentsuite.agents.marketing.template_loader import (
    TEMPLATE_NAMES,
    UnknownTemplate,
    list_templates,
    render_template,
)


def test_list_templates_returns_eight():
    assert len(list_templates()) == 8


def test_all_template_names_present():
    available = set(list_templates())
    for name in TEMPLATE_NAMES:
        assert name in available, f"Expected template '{name}' not found in {available}"


def test_render_known_template_returns_string():
    result = render_template(
        "ad-copy-brief",
        brand_name="Acme Corp",
        campaign_goal="Drive trial sign-ups",
        audience_segment="SMB marketers",
        call_to_action="Start free trial",
        platform="Instagram",
        metric_target="500 new trials",
    )
    assert isinstance(result, str)
    assert "Acme Corp" in result
    assert "Drive trial sign-ups" in result
    assert "SMB marketers" in result


def test_unknown_template_raises():
    with pytest.raises(UnknownTemplate):
        render_template("does-not-exist", brand_name="X")


def test_missing_variable_raises():
    with pytest.raises(Exception):
        # Missing required variables — StrictUndefined raises UndefinedError
        render_template("ad-copy-brief")
