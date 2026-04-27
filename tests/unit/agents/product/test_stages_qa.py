"""Unit tests for agentsuite.agents.product.stages.qa."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.stages.qa import qa_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_PASSING_SCORES = {
    "problem_clarity": 8.0,
    "user_grounding": 7.5,
    "scope_discipline": 8.0,
    "metric_specificity": 7.0,
    "feasibility_awareness": 8.0,
    "anti_feature_creep": 7.5,
    "acceptance_completeness": 8.0,
    "stakeholder_clarity": 7.0,
    "roadmap_sequencing": 8.0,
}

_PASSING_RESPONSE = json.dumps({
    "scores": _PASSING_SCORES,
    "revision_instructions": ["Clarify the success metrics timeframe"],
})

_PARTIAL_SCORES_RESPONSE = json.dumps({
    "scores": {
        "problem_clarity": 8.0,
        "user_grounding": 7.5,
        # remaining dimensions intentionally omitted
    },
    "revision_instructions": [],
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write(
        "product-requirements-doc.md",
        "# PRD\n\nContent.",
        kind="spec",
        stage="spec",
    )
    return writer


def _make_state() -> RunState:
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product",
        user_request="build a todo app",
        product_name="TodoApp",
        target_users="busy professionals",
        core_problem="people forget tasks",
    )
    return RunState(run_id="r1", agent="product", stage="qa", inputs=inp)


def test_qa_calls_llm_and_writes_report(tmp_path: Path) -> None:
    """Mock LLM returns valid scores JSON; assert qa_report.md and qa_scores.json written."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 product-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    assert (writer.run_dir / "qa_report.md").exists()
    assert (writer.run_dir / "qa_scores.json").exists()


def test_qa_advances_to_approval(tmp_path: Path) -> None:
    """Assert state.stage == 'approval' after qa_stage runs."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 product-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"


def test_qa_score_reflects_rubric_result(tmp_path: Path) -> None:
    """Assert qa_scores.json contains 'passed' key from rubric result."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 product-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    data = json.loads((writer.run_dir / "qa_scores.json").read_text(encoding="utf-8"))
    assert "passed" in data


def test_qa_handles_missing_scores_gracefully(tmp_path: Path) -> None:
    """Mock LLM returns JSON with only some dimensions; rubric raises ValueError for missing dims."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 product-agent": _PARTIAL_SCORES_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    # Rubric enforces all 9 dimensions — partial scores raise ValueError
    with pytest.raises(ValueError, match="Missing dimensions"):
        qa_stage(_make_state(), ctx)
