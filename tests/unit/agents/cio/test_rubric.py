"""Unit tests for cio.rubric."""
from agentsuite.agents.cio.rubric import CIO_RUBRIC


def test_rubric_has_9_dimensions():
    assert len(CIO_RUBRIC.dimensions) == 9


def test_rubric_pass_threshold_is_7():
    assert CIO_RUBRIC.pass_threshold == 7.0


def test_all_dimension_names_present():
    names = [d.name for d in CIO_RUBRIC.dimensions]
    assert "strategic_alignment" in names
    assert "technology_debt_awareness" in names
    assert "vendor_discipline" in names
    assert "digital_readiness" in names
    assert "governance_maturity" in names
    assert "budget_realism" in names
    assert "workforce_capability" in names
    assert "risk_tolerance_clarity" in names
    assert "innovation_balance" in names


def test_score_above_threshold_passes():
    scores = {d.name: 8.0 for d in CIO_RUBRIC.dimensions}
    report = CIO_RUBRIC.score(scores, revision_instructions=[])
    assert report.passed is True
    assert report.average >= 7.0


def test_score_below_threshold_fails():
    scores = {d.name: 5.0 for d in CIO_RUBRIC.dimensions}
    report = CIO_RUBRIC.score(scores, revision_instructions=["Improve coverage."])
    assert report.passed is False
    assert report.average < 7.0
    assert report.requires_revision is True


def test_perfect_score():
    scores = {d.name: 10.0 for d in CIO_RUBRIC.dimensions}
    report = CIO_RUBRIC.score(scores, revision_instructions=[])
    assert report.average == 10.0
    assert report.passed is True
