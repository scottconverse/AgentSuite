"""Stress tests for qa stage — shapes that real LLMs produce for scoring responses.

Uses the Founder agent as a representative specimen; the defensive code path in
qa_stage is identical across all 7 agents, and QARubric.score() is shared kernel code.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.qa import qa_stage
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import Constraints, RunState
from agentsuite.llm.mock import MockLLMProvider


_ALL_DIMS = [d.name for d in FOUNDER_RUBRIC.dimensions]
_QA_KEY = "scoring 9 founder-agent"


def _seed(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    for stem in SPEC_ARTIFACTS:
        writer.write(f"{stem}.md", f"# {stem}\n\nContent.", kind="spec", stage="spec")
    return writer


def _state() -> RunState:
    return RunState(
        run_id="r1",
        agent="founder",
        stage="qa",
        inputs=FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="stress test",
            business_goal="test",
            constraints=Constraints(),
        ),
    )


def _run_qa(tmp_path: Path, qa_response: str):
    writer = _seed(tmp_path)
    llm = MockLLMProvider(responses={_QA_KEY: qa_response})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    state = qa_stage(_state(), ctx)
    return state, writer


# ---------------------------------------------------------------------------
# Happy-path shapes
# ---------------------------------------------------------------------------

def test_all_dimensions_passing(tmp_path: Path) -> None:
    scores = {d: 8.0 for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is False


def test_all_dimensions_failing(tmp_path: Path) -> None:
    scores = {d: 5.0 for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": ["fix x"]}))
    assert state.stage == "approval"
    assert state.requires_revision is True


def test_score_at_exactly_threshold(tmp_path: Path) -> None:
    """Scores at exactly pass_threshold (7.0) should pass."""
    scores = {d: 7.0 for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.requires_revision is False


def test_score_just_below_threshold(tmp_path: Path) -> None:
    scores = {d: 6.9 for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.requires_revision is True


# ---------------------------------------------------------------------------
# Missing dimensions (CR-104 class)
# ---------------------------------------------------------------------------

def test_one_dimension_missing(tmp_path: Path) -> None:
    """LLM returns N-1 dimensions — missing dim gets 0.0, stage completes.

    8 of 9 dims at 8.0 → weighted avg = 64/9 ≈ 7.11, which is above the 7.0
    pass threshold, so requires_revision stays False.  The important assertion
    is that the stage doesn't crash and the missing dim is recorded as 0.0.
    """
    scores = {d: 8.0 for d in _ALL_DIMS[:-1]}
    state, writer = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is False  # 64/9 ≈ 7.11 > 7.0 threshold
    data = json.loads((writer.run_dir / "qa_scores.json").read_text())
    assert data["scores"][_ALL_DIMS[-1]] == 0.0


def test_one_dimension_missing_borderline_triggers_revision(tmp_path: Path) -> None:
    """Missing dim forces revision when other scores are borderline.

    8 dims at 7.5 + 1 missing (0.0) → weighted avg = 60/9 ≈ 6.67 < 7.0.
    """
    scores = {d: 7.5 for d in _ALL_DIMS[:-1]}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is True  # 60/9 ≈ 6.67 < 7.0 threshold


@pytest.mark.parametrize("missing_dim", _ALL_DIMS)
def test_each_dimension_can_be_missing_individually(tmp_path: Path, missing_dim: str) -> None:
    """Each individual dimension may be absent — must never crash."""
    scores = {d: 8.0 for d in _ALL_DIMS if d != missing_dim}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"


def test_all_dimensions_missing_empty_scores_dict(tmp_path: Path) -> None:
    """LLM returns empty scores dict — all assigned 0.0."""
    state, writer = _run_qa(tmp_path, json.dumps({"scores": {}, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is True
    data = json.loads((writer.run_dir / "qa_scores.json").read_text())
    for dim in _ALL_DIMS:
        assert data["scores"][dim] == 0.0


# ---------------------------------------------------------------------------
# scores key structural issues
# ---------------------------------------------------------------------------

def test_scores_key_missing_entirely(tmp_path: Path) -> None:
    """LLM returns JSON without a 'scores' key — must not KeyError."""
    state, _ = _run_qa(tmp_path, json.dumps({"revision_instructions": ["fix something"]}))
    assert state.stage == "approval"
    assert state.requires_revision is True


def test_scores_key_is_null(tmp_path: Path) -> None:
    """LLM returns {"scores": null} — must not crash."""
    state, _ = _run_qa(tmp_path, json.dumps({"scores": None, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is True


def test_scores_key_is_list_not_dict(tmp_path: Path) -> None:
    """LLM returns {"scores": [...]} (array instead of object) — must not crash."""
    state, _ = _run_qa(tmp_path, json.dumps({"scores": [8.0, 7.0], "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is True


def test_parsed_is_array_not_object(tmp_path: Path) -> None:
    """LLM returns a JSON array at root instead of object — must not crash."""
    state, _ = _run_qa(tmp_path, json.dumps([{"dimension": "reusability", "score": 8.0}]))
    assert state.stage == "approval"
    assert state.requires_revision is True


def test_parsed_is_plain_string(tmp_path: Path) -> None:
    """extract_json returns a bare string (unlikely but defensive) — must not crash."""
    # To get extract_json to return a string we need valid JSON that is a string
    state, _ = _run_qa(tmp_path, '"just a string"')
    assert state.stage == "approval"
    assert state.requires_revision is True


# ---------------------------------------------------------------------------
# Score type coercion
# ---------------------------------------------------------------------------

def test_scores_as_strings(tmp_path: Path) -> None:
    """LLM returns score values as strings ('8.0') — must coerce to float."""
    scores = {d: "8.0" for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is False


def test_scores_as_integer_strings(tmp_path: Path) -> None:
    """LLM returns integer strings ('8') — must coerce to float."""
    scores = {d: "8" for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is False


def test_scores_with_null_values(tmp_path: Path) -> None:
    """LLM returns null for some scores — must coerce to 0.0."""
    scores: dict = {d: (8.0 if i % 2 == 0 else None) for i, d in enumerate(_ALL_DIMS)}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"


def test_scores_with_integer_values(tmp_path: Path) -> None:
    """LLM returns integer scores (8 not 8.0) — valid, should pass cleanly."""
    scores = {d: 8 for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"
    assert state.requires_revision is False


def test_scores_with_mixed_types(tmp_path: Path) -> None:
    """Some scores float, some string, some null — must all coerce without crashing."""
    scores: dict = {}
    for i, d in enumerate(_ALL_DIMS):
        if i % 3 == 0:
            scores[d] = 8.0       # float
        elif i % 3 == 1:
            scores[d] = "7.5"     # string
        else:
            scores[d] = None      # null
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert state.stage == "approval"


# ---------------------------------------------------------------------------
# revision_instructions type variants
# ---------------------------------------------------------------------------

def test_revision_instructions_key_missing(tmp_path: Path) -> None:
    """LLM omits revision_instructions key — must not crash."""
    scores = {d: 8.0 for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores}))
    assert state.stage == "approval"


def test_revision_instructions_null(tmp_path: Path) -> None:
    """LLM returns {"revision_instructions": null} — must not crash."""
    scores = {d: 8.0 for d in _ALL_DIMS}
    state, _ = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": None}))
    assert state.stage == "approval"


def test_revision_instructions_is_string(tmp_path: Path) -> None:
    """LLM returns revision_instructions as a plain string — must not produce char-list."""
    scores = {d: 8.0 for d in _ALL_DIMS}
    state, writer = _run_qa(
        tmp_path,
        json.dumps({"scores": scores, "revision_instructions": "fix the voice tone"}),
    )
    assert state.stage == "approval"
    data = json.loads((writer.run_dir / "qa_scores.json").read_text())
    # revision_instructions must be a list, not a list of individual characters
    for item in data.get("revision_instructions", []):
        assert len(item) > 1, "revision_instructions was incorrectly split into characters"


def test_revision_instructions_is_dict(tmp_path: Path) -> None:
    """LLM returns revision_instructions as an object (CIO mock does this) — must not crash."""
    scores = {d: 8.0 for d in _ALL_DIMS}
    state, _ = _run_qa(
        tmp_path,
        json.dumps({"scores": scores, "revision_instructions": {"note": "fix x"}}),
    )
    assert state.stage == "approval"


# ---------------------------------------------------------------------------
# Format edge cases
# ---------------------------------------------------------------------------

def test_qa_response_fenced_json(tmp_path: Path) -> None:
    """LLM wraps QA scores in markdown fences."""
    scores = {d: 8.0 for d in _ALL_DIMS}
    fenced = "```json\n" + json.dumps({"scores": scores, "revision_instructions": []}) + "\n```"
    state, _ = _run_qa(tmp_path, fenced)
    assert state.stage == "approval"
    assert state.requires_revision is False


def test_qa_response_with_preamble(tmp_path: Path) -> None:
    """LLM adds prose before the JSON."""
    scores = {d: 8.0 for d in _ALL_DIMS}
    preamble = "Here are my scores for the artifacts:\n" + json.dumps(
        {"scores": scores, "revision_instructions": []}
    )
    state, _ = _run_qa(tmp_path, preamble)
    assert state.stage == "approval"


# ---------------------------------------------------------------------------
# Disk output
# ---------------------------------------------------------------------------

def test_qa_report_and_scores_written_to_disk(tmp_path: Path) -> None:
    scores = {d: 8.0 for d in _ALL_DIMS}
    _, writer = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    assert (writer.run_dir / "qa_report.md").exists()
    assert (writer.run_dir / "qa_scores.json").exists()


def test_qa_scores_json_contains_passed_key(tmp_path: Path) -> None:
    scores = {d: 8.0 for d in _ALL_DIMS}
    _, writer = _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
    data = json.loads((writer.run_dir / "qa_scores.json").read_text())
    assert "passed" in data


# ---------------------------------------------------------------------------
# Unknown dimension — existing strict behavior preserved
# ---------------------------------------------------------------------------

def test_unknown_dimension_raises(tmp_path: Path) -> None:
    """LLM returns a dimension not in the rubric — raises ValueError (strict mode preserved)."""
    scores = {d: 8.0 for d in _ALL_DIMS}
    scores["nonexistent_dimension_xyz"] = 9.0
    with pytest.raises(ValueError, match="Unknown dimensions"):
        _run_qa(tmp_path, json.dumps({"scores": scores, "revision_instructions": []}))
