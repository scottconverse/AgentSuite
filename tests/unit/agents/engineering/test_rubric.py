"""Unit tests for engineering.rubric."""
from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC


def test_rubric_name_is_engineering():
    from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC as _rubric
    assert _rubric is ENGINEERING_RUBRIC


def test_rubric_has_nine_dimensions():
    assert len(ENGINEERING_RUBRIC.dimensions) == 9


def test_rubric_pass_threshold_is_7_0():
    assert ENGINEERING_RUBRIC.pass_threshold == 7.0


def test_rubric_dimensions_include_anti_overengineering():
    names = [d.name for d in ENGINEERING_RUBRIC.dimensions]
    assert "anti_overengineering" in names
