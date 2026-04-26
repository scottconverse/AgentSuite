"""Unit tests for founder.template_loader."""
import pytest

from agentsuite.agents.founder.template_loader import (
    TEMPLATE_NAMES,
    UnknownTemplate,
    list_templates,
    render_template,
)


def test_list_templates_returns_eleven():
    names = list_templates()
    assert len(names) == 11
    assert "landing-hero" in names
    assert "readme-graphic" in names
    assert "launch-announce" in names
    assert "investor-one-pager" in names
    assert "municipal-buyer-email" in names
    assert "product-explainer" in names
    assert "social-graphic" in names
    assert "conference-slide" in names
    assert "press-pitch" in names
    assert "demo-script" in names
    assert "comparison-page" in names


def test_template_names_constant_matches_disk():
    assert sorted(TEMPLATE_NAMES) == sorted(list_templates())


def test_render_template_substitutes_variables():
    out = render_template(
        "landing-hero",
        product="PatentForgeLocal",
        audience="independent inventors",
        core_message="patent drafting on your laptop",
        proof="works offline with Ollama",
        visual_metaphor="workshop bench",
        tone="practical, technical, no-hype",
        format_constraint="hero section, ~120 words",
        required_text="Try the local installer",
        exclusions="no neon gradients",
    )
    assert "PatentForgeLocal" in out
    assert "independent inventors" in out
    assert "no neon gradients" in out


def test_render_unknown_raises():
    with pytest.raises(UnknownTemplate):
        render_template("nope", product="x")
