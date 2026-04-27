"""Unit tests for agentsuite.agents.cio.stages.qa."""
from __future__ import annotations

import json
from pathlib import Path


from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.rubric import CIO_RUBRIC
from agentsuite.agents.cio.stages.qa import qa_stage
from agentsuite.agents.cio.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_DIM_NAMES = [d.name for d in CIO_RUBRIC.dimensions]

_SCORES_ALL_PASS = {name: 8.0 for name in _DIM_NAMES}
# Average must be < 7.0 to trigger requires_revision.
# With all dims at 6.5, average = 6.5 < 7.0 threshold.
_SCORES_ONE_FAIL = {name: 6.5 for name in _DIM_NAMES}


def _qa_response(scores: dict[str, float]) -> str:
    return json.dumps({
        "scores": scores,
        "revision_instructions": [],
    })


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    for stem in SPEC_ARTIFACTS:
        (writer.run_dir / f"{stem}.md").write_text(
            f"# {stem.replace('-', ' ').title()}\n\nContent for {stem}.",
            encoding="utf-8",
        )
    return writer


def _make_state() -> RunState:
    inp = CIOAgentInput(
        agent_name="cio",
        role_domain="cio-ops",
        user_request="develop IT strategy and technology roadmap",
        organization_name="Acme Corp",
        strategic_priorities="Cloud-first, data-driven decision making",
        it_maturity_level="Level 2 – Repeatable",
        budget_context="$5M annual IT capex",
        digital_initiatives="ERP modernization, cloud migration phase 1",
        regulatory_environment="SOX, HIPAA",
    )
    return RunState(run_id="r1", agent="cio", stage="qa", inputs=inp)


def test_qa_writes_qa_scores_json(tmp_path: Path) -> None:
    """qa_stage writes qa_scores.json into the run directory."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 CIO artifacts": _qa_response(_SCORES_ALL_PASS)})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    assert (writer.run_dir / "qa_scores.json").exists()


def test_qa_advances_stage_to_approval(tmp_path: Path) -> None:
    """qa_stage returns state with stage == 'approval'."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 CIO artifacts": _qa_response(_SCORES_ALL_PASS)})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = qa_stage(_make_state(), ctx)
    assert new_state.stage == "approval"


def test_qa_scores_all_dims_present(tmp_path: Path) -> None:
    """qa_scores.json contains all 9 CIO rubric dimension names."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 CIO artifacts": _qa_response(_SCORES_ALL_PASS)})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    data = json.loads((writer.run_dir / "qa_scores.json").read_text(encoding="utf-8"))
    for dim in _DIM_NAMES:
        assert dim in data["scores"], f"Missing dimension in qa_scores.json: {dim}"


def test_qa_requires_revision_false_when_all_pass(tmp_path: Path) -> None:
    """requires_revision is False when all dimension scores meet the threshold."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 CIO artifacts": _qa_response(_SCORES_ALL_PASS)})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = qa_stage(_make_state(), ctx)
    assert new_state.requires_revision is False


def test_qa_requires_revision_true_when_below_threshold(tmp_path: Path) -> None:
    """requires_revision is True when the average score is below the pass threshold."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 CIO artifacts": _qa_response(_SCORES_ONE_FAIL)})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = qa_stage(_make_state(), ctx)
    assert new_state.requires_revision is True
