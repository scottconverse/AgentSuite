"""Unit tests for agentsuite.agents.engineering.stages.qa."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.stages.qa import qa_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_PASSING_SCORES = {
    "implementation_specificity": 8.0,
    "testability": 7.5,
    "security_posture": 8.0,
    "scalability_awareness": 7.0,
    "dependency_hygiene": 8.0,
    "anti_overengineering": 7.5,
    "operational_completeness": 8.0,
    "decision_traceability": 7.0,
    "api_contract_clarity": 8.0,
}

_PASSING_RESPONSE = json.dumps({
    "scores": _PASSING_SCORES,
    "revision_instructions": ["Clarify deployment rollback procedure"],
})

_PARTIAL_SCORES_RESPONSE = json.dumps({
    "scores": {
        "implementation_specificity": 8.0,
        "testability": 7.5,
        # remaining dimensions intentionally omitted
    },
    "revision_instructions": [],
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write(
        "system-design.md",
        "# System Design\n\nContent.",
        kind="spec",
        stage="spec",
    )
    return writer


def _make_state() -> RunState:
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering",
        user_request="build a distributed task queue",
        system_name="TaskQueue",
        problem_domain="distributed task processing at scale",
        tech_stack="Python + FastAPI + PostgreSQL + Redis",
        scale_requirements="10k RPM, 99.9% uptime, <200ms p99",
    )
    return RunState(run_id="r1", agent="engineering", stage="qa", inputs=inp)


def test_qa_calls_llm_and_writes_report(tmp_path: Path) -> None:
    """Mock LLM returns valid scores JSON; assert qa_report.md and qa_scores.json written."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 engineering-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    assert (writer.run_dir / "qa_report.md").exists()
    assert (writer.run_dir / "qa_scores.json").exists()


def test_qa_advances_to_approval(tmp_path: Path) -> None:
    """Assert state.stage == 'approval' after qa_stage runs."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 engineering-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"


def test_qa_score_reflects_rubric_result(tmp_path: Path) -> None:
    """Assert qa_scores.json contains 'passed' key from rubric result."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 engineering-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    data = json.loads((writer.run_dir / "qa_scores.json").read_text(encoding="utf-8"))
    assert "passed" in data


def test_qa_handles_missing_scores_raises(tmp_path: Path) -> None:
    """Mock LLM returns JSON with only some dimensions; rubric raises ValueError for missing dims."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 engineering-agent": _PARTIAL_SCORES_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    # Rubric enforces all 9 dimensions — partial scores raise ValueError
    with pytest.raises(ValueError, match="Missing dimensions"):
        qa_stage(_make_state(), ctx)
