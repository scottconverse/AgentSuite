"""Stress tests for spec stage consistency check — shapes that real LLMs produce.

Uses the Founder agent as a representative specimen; the consistency-check
defensive code path is identical across all 7 agents.
"""
from __future__ import annotations

import json
from pathlib import Path


from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS, spec_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import Constraints, RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "mission": "test mission",
    "audience": {"primary_persona": "developer", "secondary_personas": []},
    "positioning": "test positioning",
    "tone_signals": ["direct"],
    "visual_signals": [],
    "recurring_claims": [],
    "recurring_vocabulary": [],
    "prohibited_language": [],
    "gaps": [],
}


def _seed(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _state() -> RunState:
    return RunState(
        run_id="r1",
        agent="founder",
        stage="spec",
        inputs=FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="stress test",
            business_goal="test",
            constraints=Constraints(),
        ),
    )


def _artifact_responses() -> dict[str, str]:
    return {f"writing {stem}.md": f"# {stem}\n\nContent." for stem in SPEC_ARTIFACTS}


def _run_spec(tmp_path: Path, consistency_response: str):
    writer = _seed(tmp_path)
    responses = _artifact_responses()
    responses["checking 9 artifacts"] = consistency_response
    llm = MockLLMProvider(responses=responses)
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    state = spec_stage(_state(), ctx)
    return state, writer


# ---------------------------------------------------------------------------
# Happy-path shapes
# ---------------------------------------------------------------------------

def test_empty_mismatches(tmp_path: Path) -> None:
    state, _ = _run_spec(tmp_path, json.dumps({"mismatches": []}))
    assert state.stage == "execute"
    assert state.requires_revision is False


def test_warning_only_mismatches(tmp_path: Path) -> None:
    response = json.dumps({"mismatches": [
        {"dimension": "tone", "severity": "warning", "detail": "minor issue"},
    ]})
    state, _ = _run_spec(tmp_path, response)
    assert state.requires_revision is False


def test_critical_mismatch_sets_requires_revision(tmp_path: Path) -> None:
    response = json.dumps({"mismatches": [
        {"dimension": "tone", "severity": "critical", "detail": "conflict"},
    ]})
    state, _ = _run_spec(tmp_path, response)
    assert state.requires_revision is True
    assert state.stage == "execute"


def test_mixed_critical_and_warning(tmp_path: Path) -> None:
    response = json.dumps({"mismatches": [
        {"dimension": "tone", "severity": "warning", "detail": "minor"},
        {"dimension": "audience", "severity": "critical", "detail": "conflict"},
    ]})
    state, _ = _run_spec(tmp_path, response)
    assert state.requires_revision is True


def test_many_critical_mismatches(tmp_path: Path) -> None:
    mismatches = [
        {"dimension": f"dim_{i}", "severity": "critical", "detail": f"conflict {i}"}
        for i in range(20)
    ]
    state, _ = _run_spec(tmp_path, json.dumps({"mismatches": mismatches}))
    assert state.requires_revision is True


# ---------------------------------------------------------------------------
# Structural edge cases — the bugs we fixed
# ---------------------------------------------------------------------------

def test_missing_mismatches_key(tmp_path: Path) -> None:
    """LLM returns {} with no mismatches key — must not crash."""
    state, _ = _run_spec(tmp_path, json.dumps({}))
    assert state.stage == "execute"
    assert state.requires_revision is False


def test_mismatches_null(tmp_path: Path) -> None:
    """LLM returns {"mismatches": null} — was a live-test crash, must not crash now."""
    state, _ = _run_spec(tmp_path, json.dumps({"mismatches": None}))
    assert state.stage == "execute"
    assert state.requires_revision is False


def test_report_is_array_not_dict(tmp_path: Path) -> None:
    """LLM returns a JSON array instead of object — must not crash."""
    state, _ = _run_spec(tmp_path, json.dumps([{"dimension": "tone", "severity": "critical"}]))
    assert state.stage == "execute"
    assert state.requires_revision is False


def test_mismatch_item_missing_severity(tmp_path: Path) -> None:
    """Mismatch object has no severity key — must not count as critical."""
    response = json.dumps({"mismatches": [{"dimension": "tone", "detail": "something"}]})
    state, _ = _run_spec(tmp_path, response)
    assert state.requires_revision is False


def test_mismatch_item_is_string_not_dict(tmp_path: Path) -> None:
    """Some mismatch items are strings (non-dict) — must be skipped gracefully."""
    response = json.dumps({"mismatches": [
        "just a string",
        {"dimension": "tone", "severity": "critical", "detail": "real conflict"},
    ]})
    state, _ = _run_spec(tmp_path, response)
    assert state.requires_revision is True  # the dict item counts


def test_mismatches_list_entirely_non_dict(tmp_path: Path) -> None:
    """All mismatch items are non-dicts — no critical items, no crash."""
    response = json.dumps({"mismatches": ["string1", 42, None, True]})
    state, _ = _run_spec(tmp_path, response)
    assert state.requires_revision is False


def test_unknown_severity_value(tmp_path: Path) -> None:
    """Mismatch with unknown severity string — must not count as critical."""
    response = json.dumps({"mismatches": [
        {"dimension": "tone", "severity": "high", "detail": "conflict"},
    ]})
    state, _ = _run_spec(tmp_path, response)
    assert state.requires_revision is False


# ---------------------------------------------------------------------------
# Format edge cases
# ---------------------------------------------------------------------------

def test_consistency_response_fenced(tmp_path: Path) -> None:
    fenced = "```json\n" + json.dumps({"mismatches": []}) + "\n```"
    state, _ = _run_spec(tmp_path, fenced)
    assert state.stage == "execute"
    assert state.requires_revision is False


def test_consistency_response_with_preamble(tmp_path: Path) -> None:
    preamble = "Here is the consistency report:\n" + json.dumps({"mismatches": []})
    state, _ = _run_spec(tmp_path, preamble)
    assert state.stage == "execute"
    assert state.requires_revision is False


def test_consistency_response_fenced_critical(tmp_path: Path) -> None:
    payload = json.dumps({"mismatches": [{"dimension": "tone", "severity": "critical", "detail": "x"}]})
    fenced = "```json\n" + payload + "\n```"
    state, _ = _run_spec(tmp_path, fenced)
    assert state.requires_revision is True


# ---------------------------------------------------------------------------
# Report written to disk regardless of shape
# ---------------------------------------------------------------------------

def test_consistency_report_always_written(tmp_path: Path) -> None:
    state, writer = _run_spec(tmp_path, json.dumps({"mismatches": []}))
    assert (writer.run_dir / "consistency_report.json").exists()


def test_consistency_report_written_on_critical(tmp_path: Path) -> None:
    response = json.dumps({"mismatches": [{"dimension": "tone", "severity": "critical", "detail": "x"}]})
    _, writer = _run_spec(tmp_path, response)
    assert (writer.run_dir / "consistency_report.json").exists()
