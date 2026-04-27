"""Unit tests for cio.template_loader."""
import pytest

from agentsuite.agents.cio.template_loader import (
    TEMPLATE_NAMES,
    UnknownTemplate,
    list_templates,
    render_template,
)


def test_list_templates_returns_8():
    assert len(list_templates()) == 8


def test_list_templates_all_names_present():
    available = set(list_templates())
    for name in TEMPLATE_NAMES:
        assert name in available, f"Expected template '{name}' not found in {available}"


def test_list_templates_is_sorted():
    templates = list_templates()
    assert templates == sorted(templates)


def test_render_template_returns_string():
    result = render_template(
        "board-technology-briefing",
        organization_name="Acme Corp",
        briefing_date="2026-04-27",
        cio_name="Jane Smith",
        reporting_period="Q1 2026",
        priority_1_title="Cloud Migration",
        priority_2_title="Cybersecurity Uplift",
        priority_3_title="Data Platform",
        fiscal_year="FY2026",
        total_it_budget="$12M",
    )
    assert isinstance(result, str)
    assert "Acme Corp" in result
    assert "Jane Smith" in result


def test_render_unknown_raises():
    with pytest.raises(UnknownTemplate):
        render_template("does-not-exist", organization_name="X")
