"""Unit tests for founder.stages.spec."""
import json
from pathlib import Path

import pytest

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.spec import (
    SPEC_ARTIFACTS,
    _read_voice_samples,
    spec_stage,
)
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import Constraints, RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "mission": "x",
    "audience": {"primary_persona": "y", "secondary_personas": []},
    "positioning": "z",
    "tone_signals": ["practical"],
    "visual_signals": [],
    "recurring_claims": [],
    "recurring_vocabulary": [],
    "prohibited_language": [],
    "gaps": [],
}


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _state() -> RunState:
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship pfl",
        constraints=Constraints(),
    )
    return RunState(run_id="r1", agent="founder", stage="spec", inputs=inp)


def _passing_consistency_response() -> str:
    return json.dumps({"mismatches": []})


def _critical_mismatch_response() -> str:
    return json.dumps({
        "mismatches": [{
            "field": "audience",
            "files": ["brand-system.md", "audience-map.md"],
            "details": "audience differs",
            "severity": "critical",
        }]
    })


def _spec_responses() -> dict[str, str]:
    """One canned response per spec artifact + consistency check."""
    responses: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        keyword = f"writing {stem}.md"
        responses[keyword] = f"# {stem}\n\nReal content for {stem}."
    responses["checking 9 artifacts"] = _passing_consistency_response()
    return responses


def test_spec_writes_all_nine_artifacts(tmp_path):
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_state(), ctx)
    assert new_state.stage == "execute"
    for stem in SPEC_ARTIFACTS:
        assert (writer.run_dir / f"{stem}.md").exists()
    assert (writer.run_dir / "consistency_report.json").exists()


def test_spec_writes_consistency_report(tmp_path):
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_state(), ctx)
    report = json.loads((writer.run_dir / "consistency_report.json").read_text(encoding="utf-8"))
    assert "mismatches" in report


def test_spec_fails_on_critical_consistency_mismatch(tmp_path):
    writer = _seed_run_dir(tmp_path)
    responses = _spec_responses()
    responses["checking 9 artifacts"] = _critical_mismatch_response()
    llm = MockLLMProvider(responses=responses)
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_state(), ctx)
    assert new_state.requires_revision is True
    assert new_state.stage == "execute"


# ENG-S2-001: path confinement tests for _read_voice_samples

def test_read_voice_samples_rejects_out_of_project_path(tmp_path: Path) -> None:
    """ENG-S2-001: _read_voice_samples raises ValueError for a path outside project_dir."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("sensitive content", encoding="utf-8")

    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="test",
        business_goal="test",
        founder_voice_samples=[outside_file],
    )
    with pytest.raises(ValueError, match="outside the project directory"):
        _read_voice_samples(inp, project_dir)


def test_read_voice_samples_accepts_in_project_path(tmp_path: Path) -> None:
    """ENG-S2-001: _read_voice_samples reads files within project_dir without error."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    sample = project_dir / "voice.txt"
    sample.write_text("Hello founder", encoding="utf-8")

    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="test",
        business_goal="test",
        founder_voice_samples=[sample],
    )
    result = _read_voice_samples(inp, project_dir)
    assert "Hello founder" in result
