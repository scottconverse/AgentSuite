"""Unit tests for kernel.qa."""
import pytest

from agentsuite.kernel.qa import QAReport, QARubric, RubricDimension


def test_rubric_pass_threshold_default():
    r = QARubric(dimensions=[RubricDimension(name="x", question="?")])
    assert r.pass_threshold == 7.0


def test_rubric_score_average_above_threshold_passes():
    r = QARubric(
        dimensions=[
            RubricDimension(name="a", question="?"),
            RubricDimension(name="b", question="?"),
        ],
        pass_threshold=7.0,
    )
    report = r.score({"a": 8.0, "b": 7.5}, revision_instructions=[])
    assert report.passed is True
    assert report.average == pytest.approx(7.75)
    assert report.requires_revision is False


def test_rubric_score_average_below_threshold_fails():
    r = QARubric(
        dimensions=[
            RubricDimension(name="a", question="?"),
            RubricDimension(name="b", question="?"),
        ],
        pass_threshold=7.0,
    )
    report = r.score(
        {"a": 5.0, "b": 6.0},
        revision_instructions=["fix audience", "tighten claims"],
    )
    assert report.passed is False
    assert report.requires_revision is True
    assert "fix audience" in report.revision_instructions


def test_rubric_score_rejects_unknown_dimension():
    r = QARubric(dimensions=[RubricDimension(name="a", question="?")])
    with pytest.raises(ValueError):
        r.score({"a": 5.0, "unknown": 7.0}, revision_instructions=[])


def test_rubric_score_missing_dimensions_assigned_zero():
    """Missing dimensions no longer raise — they get 0.0 and a revision note."""
    r = QARubric(
        dimensions=[
            RubricDimension(name="a", question="?"),
            RubricDimension(name="b", question="?"),
        ],
    )
    report = r.score({"a": 7.0}, revision_instructions=[])
    assert report.scores["b"] == 0.0
    assert any("b" in inst for inst in report.revision_instructions)
    assert report.passed is False  # 0.0 drags average below 7.0


def test_score_assigns_zero_for_missing_dimensions():
    rubric = QARubric(dimensions=[
        RubricDimension(name="a", question="q1"),
        RubricDimension(name="b", question="q2"),
        RubricDimension(name="c", question="q3"),
    ])
    # LLM only returned 2 of 3 dimensions
    report = rubric.score(scores={"a": 8.0, "b": 7.0}, revision_instructions=[])
    assert report.scores["c"] == 0.0
    assert any("c" in r for r in report.revision_instructions)
    assert report.passed is False  # 0.0 drags average below 7.0


def test_qa_report_renders_markdown():
    report = QAReport(
        scores={"a": 8.0, "b": 6.0},
        average=7.0,
        passed=True,
        revision_instructions=["x"],
        requires_revision=False,
    )
    md = report.to_markdown()
    assert "Average score: 7.00" in md
    assert "| a | 8.00 |" in md
    assert "| b | 6.00 |" in md


def test_qa_boundary_exactly_at_threshold_passes():
    """Score exactly at threshold should pass (>= not >)."""
    r = QARubric(
        dimensions=[RubricDimension(name="a", question="?")],
        pass_threshold=7.0,
    )
    result = r.score({"a": 7.0}, revision_instructions=[])
    assert result.passed is True


def test_qa_boundary_just_below_threshold_fails():
    """Score 0.01 below threshold should fail."""
    r = QARubric(
        dimensions=[RubricDimension(name="a", question="?")],
        pass_threshold=7.0,
    )
    result = r.score({"a": 6.99}, revision_instructions=["fix it"])
    assert result.passed is False
