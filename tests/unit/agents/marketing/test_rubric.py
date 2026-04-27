"""Unit tests for marketing.rubric."""
from agentsuite.agents.marketing.rubric import MARKETING_RUBRIC


def test_rubric_name_is_marketing():
    from agentsuite.agents.marketing.rubric import MARKETING_RUBRIC as _rubric
    assert _rubric is MARKETING_RUBRIC


def test_rubric_has_nine_dimensions():
    assert len(MARKETING_RUBRIC.dimensions) == 9


def test_rubric_pass_threshold_is_7_0():
    assert MARKETING_RUBRIC.pass_threshold == 7.0


def test_rubric_dimensions_include_all_nine():
    names = [d.name for d in MARKETING_RUBRIC.dimensions]
    assert "audience_clarity" in names
    assert "message_resonance" in names
    assert "channel_fit" in names
    assert "metric_specificity" in names
    assert "budget_realism" in names
    assert "anti_vanity_metrics" in names
    assert "content_depth" in names
    assert "competitive_awareness" in names
    assert "launch_sequencing" in names
