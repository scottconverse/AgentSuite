"""Unit tests for founder.rubric."""
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC


def test_founder_rubric_dimension_count():
    assert len(FOUNDER_RUBRIC.dimensions) == 9


def test_founder_rubric_dimensions_present():
    names = [d.name for d in FOUNDER_RUBRIC.dimensions]
    assert "reusability" in names
    assert "brand_consistency" in names
    assert "claims_grounded" in names
    assert "voice_fit" in names
    assert "template_specificity" in names
    assert "goal_alignment" in names
    assert "anti_genericity" in names
    assert "constraint_adherence" in names
    assert "completeness" in names


def test_founder_rubric_all_questions_non_empty():
    for dim in FOUNDER_RUBRIC.dimensions:
        assert dim.question, f"dimension '{dim.name}' has empty question"


def test_founder_rubric_pass_threshold():
    assert FOUNDER_RUBRIC.pass_threshold == 7.0


def test_founder_rubric_scores_pass_path():
    scores = {d.name: 8.0 for d in FOUNDER_RUBRIC.dimensions}
    report = FOUNDER_RUBRIC.score(scores, revision_instructions=[])
    assert report.passed is True


def test_founder_rubric_scores_fail_path():
    scores = {d.name: 5.0 for d in FOUNDER_RUBRIC.dimensions}
    report = FOUNDER_RUBRIC.score(scores, revision_instructions=["fix x"])
    assert report.passed is False
    assert report.requires_revision is True
