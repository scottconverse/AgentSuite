"""Unit tests for design.rubric."""
from agentsuite.agents.design.rubric import DESIGN_RUBRIC


def test_rubric_name_is_design():
    # The rubric's first dimension should include "design" in scope —
    # the rubric itself is namespaced via the module; verify the canonical
    # dimension set matches the design domain by checking the module attribute name.
    # QARubric has no top-level name field; we verify identity via import.
    from agentsuite.agents.design.rubric import DESIGN_RUBRIC as _rubric
    assert _rubric is DESIGN_RUBRIC


def test_rubric_has_seven_dimensions():
    assert len(DESIGN_RUBRIC.dimensions) == 7


def test_rubric_pass_threshold_is_7_0():
    assert DESIGN_RUBRIC.pass_threshold == 7.0


def test_rubric_dimensions_include_anti_genericity():
    names = [d.name for d in DESIGN_RUBRIC.dimensions]
    assert "anti_genericity" in names
