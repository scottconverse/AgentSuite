"""Unit tests for founder.prompt_loader."""
import pytest

from agentsuite.agents.founder.prompt_loader import (
    UnknownPrompt,
    list_prompts,
    render_prompt,
)


def test_list_prompts_returns_all_known():
    names = list_prompts()
    assert "extract" in names
    assert "spec_brand_system" in names
    assert "consistency_check" in names
    assert "qa_score" in names


def test_render_prompt_substitutes_variables():
    out = render_prompt("extract", sources_summary="repo X, README Y", business_goal="ship")
    assert "repo X, README Y" in out
    assert "ship" in out


def test_render_prompt_unknown_raises():
    with pytest.raises(UnknownPrompt):
        render_prompt("nope")
