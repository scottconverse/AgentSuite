"""Unit tests for founder.stages.spec."""
import json
from pathlib import Path

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.spec import (
    SPEC_ARTIFACTS,
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
