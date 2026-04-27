"""Unit tests for trust_risk.template_loader."""
import pytest

from agentsuite.agents.trust_risk.template_loader import (
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
        "breach-notification",
        product_name="Acme Corp",
        incident_title="2024-Q1 Data Breach",
        severity="High",
        regulatory_context="GDPR",
        team_lead="Jane Smith",
    )
    assert isinstance(result, str)
    assert "Acme Corp" in result
    assert "2024-Q1 Data Breach" in result
    assert "Jane Smith" in result


def test_unknown_template_raises():
    with pytest.raises(UnknownTemplate):
        render_template("does-not-exist", product_name="X")


def test_missing_variable_raises():
    with pytest.raises(Exception):
        # Missing required variables — StrictUndefined raises UndefinedError
        render_template("breach-notification")
