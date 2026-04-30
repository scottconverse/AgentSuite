"""Unit tests for agentsuite.agents.marketing.stages.qa."""
from __future__ import annotations

import json
from pathlib import Path


from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.stages.qa import qa_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_PASSING_SCORES = {
    "audience_clarity": 8.0,
    "message_resonance": 7.5,
    "channel_fit": 8.0,
    "metric_specificity": 7.0,
    "budget_realism": 8.0,
    "anti_vanity_metrics": 7.5,
    "content_depth": 8.0,
    "competitive_awareness": 7.0,
    "launch_sequencing": 8.0,
}

_PASSING_RESPONSE = json.dumps({
    "scores": _PASSING_SCORES,
    "revision_instructions": ["Clarify post-launch measurement cadence"],
})

_PARTIAL_SCORES_RESPONSE = json.dumps({
    "scores": {
        "audience_clarity": 8.0,
        "message_resonance": 7.5,
        # remaining dimensions intentionally omitted
    },
    "revision_instructions": [],
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write(
        "campaign-brief.md",
        "# Campaign Brief\n\nContent.",
        kind="spec",
        stage="spec",
    )
    return writer


def _make_state() -> RunState:
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="launch a B2B SaaS product campaign",
        brand_name="AcmeCorp",
        campaign_goal="Generate 500 qualified leads in Q3",
        target_market="Mid-market SaaS buyers in North America",
    )
    return RunState(run_id="r1", agent="marketing", stage="qa", inputs=inp)


def test_qa_calls_llm_and_writes_report(tmp_path: Path) -> None:
    """Mock LLM returns valid scores JSON; assert qa_report.md and qa_scores.json written."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 marketing-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    assert (writer.run_dir / "qa_report.md").exists()
    assert (writer.run_dir / "qa_scores.json").exists()


def test_qa_advances_to_approval(tmp_path: Path) -> None:
    """Assert state.stage == 'approval' after qa_stage runs."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 marketing-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"


def test_qa_score_reflects_rubric_result(tmp_path: Path) -> None:
    """Assert qa_scores.json contains 'passed' key from rubric result."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 marketing-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    data = json.loads((writer.run_dir / "qa_scores.json").read_text(encoding="utf-8"))
    assert "passed" in data


def test_qa_handles_missing_scores_gracefully(tmp_path: Path) -> None:
    """Mock LLM returns partial scores; missing dims assigned 0.0 and stage completes."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 marketing-agent": _PARTIAL_SCORES_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"
    assert result.requires_revision is True
