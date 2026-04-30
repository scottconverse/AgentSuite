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


# ---------------------------------------------------------------------------
# E2: Legacy rubric migration — 7-dimension (old format) must not KeyError
# ---------------------------------------------------------------------------

# The 9-dimension rubric was introduced in v0.8.  Prior runs may have persisted
# qa_scores.json with only the original 7 keys (missing constraint_adherence
# and completeness).  The rubric's .score() method must raise a clear ValueError
# (not a bare KeyError) so callers can handle or surface the error gracefully.

_LEGACY_7_DIMS = [
    "reusability",
    "brand_consistency",
    "claims_grounded",
    "voice_fit",
    "template_specificity",
    "goal_alignment",
    "anti_genericity",
]

_MISSING_DIMS = {"constraint_adherence", "completeness"}


def test_founder_rubric_legacy_7dim_assigns_zero_for_missing():
    """Missing dimensions are assigned 0.0 instead of raising ValueError."""
    legacy_scores = {name: 8.0 for name in _LEGACY_7_DIMS}
    report = FOUNDER_RUBRIC.score(legacy_scores, revision_instructions=[])
    for dim in _MISSING_DIMS:
        assert report.scores[dim] == 0.0, f"Expected 0.0 for missing dim '{dim}'"


def test_founder_rubric_legacy_7dim_missing_dims_named_in_revision():
    """Missing dimension names appear in revision_instructions, not in an exception."""
    legacy_scores = {name: 8.0 for name in _LEGACY_7_DIMS}
    report = FOUNDER_RUBRIC.score(legacy_scores, revision_instructions=[])
    combined = " ".join(report.revision_instructions)
    for dim in _MISSING_DIMS:
        assert dim in combined, f"Expected missing dim '{dim}' in revision instructions: {combined}"


def test_founder_rubric_legacy_7dim_no_key_error():
    """Passing 7-dim scores must not raise KeyError or ValueError (regression guard)."""
    legacy_scores = {name: 7.5 for name in _LEGACY_7_DIMS}
    # Should complete without raising
    FOUNDER_RUBRIC.score(legacy_scores, revision_instructions=[])
