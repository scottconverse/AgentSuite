"""Unit tests for product.rubric."""
from agentsuite.agents.product.rubric import PRODUCT_RUBRIC


def test_rubric_name_is_product():
    from agentsuite.agents.product.rubric import PRODUCT_RUBRIC as _rubric
    assert _rubric is PRODUCT_RUBRIC


def test_rubric_has_nine_dimensions():
    assert len(PRODUCT_RUBRIC.dimensions) == 9


def test_rubric_pass_threshold_is_7_0():
    assert PRODUCT_RUBRIC.pass_threshold == 7.0


def test_rubric_dimensions_include_anti_feature_creep():
    names = [d.name for d in PRODUCT_RUBRIC.dimensions]
    assert "anti_feature_creep" in names
