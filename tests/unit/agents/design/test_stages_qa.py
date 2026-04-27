"""Unit tests for agentsuite.agents.design.stages.qa."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.stages.qa import qa_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_PASSING_SCORES = {
    "spec_completeness": 8.0,
    "brand_fidelity": 8.0,
    "audience_fit": 8.0,
    "craft_specificity": 8.0,
    "accessibility_rigor": 7.5,
    "anti_genericity": 8.0,
    "revision_actionability": 7.5,
    "consistency": 8.0,
    "image_prompt_precision": 7.5,
}

_FAILING_SCORES = {k: 5.0 for k in _PASSING_SCORES}

_PASSING_RESPONSE = json.dumps({
    "scores": _PASSING_SCORES,
    "revision_instructions": ["Polish the color rationale in brand-rules-extracted.md"],
})

_FAILING_RESPONSE = json.dumps({
    "scores": _FAILING_SCORES,
    "revision_instructions": ["All dims below 7.0 — major rework needed"],
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write("visual-direction.md", "# Visual direction\n\nContent.", kind="spec", stage="spec")
    return writer


def _make_state() -> RunState:
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="marketing",
        user_request="campaign",
        target_audience="developers",
        campaign_goal="drive signups",
        channel="web",
    )
    return RunState(run_id="r1", agent="design", stage="qa", inputs=inp)


def test_qa_advances_to_approval_on_pass(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 design-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"
    assert result.requires_revision is False


def test_qa_requires_revision_on_fail(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 design-agent": _FAILING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"
    assert result.requires_revision is True


def test_qa_writes_report_and_scores(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 design-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    assert (writer.run_dir / "qa_report.md").exists()
    assert (writer.run_dir / "qa_scores.json").exists()


def test_qa_raises_on_invalid_json(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 design-agent": "not json"})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    with pytest.raises(ValueError, match="qa stage produced invalid JSON"):
        qa_stage(_make_state(), ctx)


def test_qa_tracks_cost(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 design-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens > 0
