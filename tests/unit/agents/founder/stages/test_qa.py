"""Unit tests for founder.stages.qa."""
import json
from pathlib import Path

import pytest

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.qa import qa_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import Constraints, RunState
from agentsuite.llm.mock import MockLLMProvider


def _seed_with_artifacts(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    for stem in [
        "brand-system",
        "founder-voice-guide",
        "product-positioning",
        "audience-map",
        "claims-and-proof-library",
        "visual-style-guide",
        "campaign-production-workflow",
        "asset-qa-checklist",
        "reusable-prompt-library",
    ]:
        writer.write(f"{stem}.md", f"# {stem}\nContent.", kind="spec", stage="spec")
    return writer


def _state() -> RunState:
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship pfl",
        constraints=Constraints(),
    )
    return RunState(run_id="r1", agent="founder", stage="qa", inputs=inp)


def _passing_score_response() -> str:
    return json.dumps({
        "scores": {d.name: 8.0 for d in FOUNDER_RUBRIC.dimensions},
        "revision_instructions": [],
    })


def _failing_score_response() -> str:
    return json.dumps({
        "scores": {d.name: 5.0 for d in FOUNDER_RUBRIC.dimensions},
        "revision_instructions": ["tighten audience definition"],
    })


def test_qa_writes_qa_report_and_advances_to_approval(tmp_path):
    writer = _seed_with_artifacts(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 founder": _passing_score_response()})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = qa_stage(_state(), ctx)
    assert new_state.stage == "approval"
    assert new_state.requires_revision is False
    qa_md = (writer.run_dir / "qa_report.md").read_text(encoding="utf-8")
    assert "Average score" in qa_md


def test_qa_marks_requires_revision_on_low_score(tmp_path):
    writer = _seed_with_artifacts(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 founder": _failing_score_response()})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = qa_stage(_state(), ctx)
    assert new_state.requires_revision is True
    assert new_state.stage == "approval"


def test_qa_raises_on_invalid_json(tmp_path):
    writer = _seed_with_artifacts(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 founder": "not json"})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    with pytest.raises(ValueError, match="qa stage produced invalid JSON"):
        qa_stage(_state(), ctx)
