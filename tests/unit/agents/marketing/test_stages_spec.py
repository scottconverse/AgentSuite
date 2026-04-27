"""Unit tests for agentsuite.agents.marketing.stages.spec."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.stages.spec import (
    SPEC_ARTIFACTS,
    ConsistencyCheckFailed,
    spec_stage,
)
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "audience_insights": ["millennials prefer short-form video"],
    "brand_themes": ["sustainability", "innovation"],
    "competitor_gaps": ["no competitor owns the eco angle"],
    "channel_performance": ["email CTR 3.2%", "paid social ROAS 2.1x"],
    "keyword_opportunities": ["sustainable fashion", "eco-friendly apparel"],
    "open_questions": ["which influencer tier?"],
}

_CONSISTENCY_OK = json.dumps({
    "mismatches": [
        {
            "dimension": "messaging alignment",
            "status": "ok",
            "severity": "ok",
            "detail": "No issues found.",
        }
    ]
})

_CONSISTENCY_CRITICAL = json.dumps({
    "mismatches": [
        {
            "dimension": "channel coverage",
            "status": "mismatch",
            "severity": "critical",
            "detail": "Channel strategy contradicts content calendar channels",
        }
    ]
})

_CONSISTENCY_WARNING = json.dumps({
    "mismatches": [
        {
            "dimension": "budget allocation",
            "status": "mismatch",
            "severity": "warning",
            "detail": "Launch plan budget exceeds channel strategy estimate",
        }
    ]
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="launch a Q3 campaign for our eco-friendly apparel line",
        brand_name="GreenThread",
        campaign_goal="drive 20% revenue growth in Q3 via eco-conscious positioning",
        target_market="millennials and Gen Z interested in sustainable fashion",
        budget_range="$75k over 12 weeks",
        timeline="Q3 2024, July–September",
        channels="paid social, email, content marketing, influencer",
    )
    return RunState(run_id="r1", agent="marketing", stage="spec", inputs=inp)


def _spec_responses(consistency_json: str = _CONSISTENCY_OK) -> dict[str, str]:
    responses: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md for a marketing team"] = (
            f"# {stem.replace('-', ' ').title()}\n\nContent here"
        )
    responses["checking 9 marketing-agent artifacts"] = consistency_json
    return responses


def test_spec_generates_all_nine_artifacts(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    for stem in SPEC_ARTIFACTS:
        assert (writer.run_dir / f"{stem}.md").exists(), f"missing {stem}.md"


def test_spec_advances_to_execute(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.stage == "execute"


def test_spec_runs_consistency_check(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    report_path = writer.run_dir / "consistency_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "mismatches" in report


def test_spec_llm_call_count(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    # 9 artifact calls + 1 consistency call = 10
    assert len(llm.calls) == 10


def test_spec_raises_on_critical_consistency_failure(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses(consistency_json=_CONSISTENCY_CRITICAL))
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    with pytest.raises(ConsistencyCheckFailed, match="critical"):
        spec_stage(_make_state(), ctx)


def test_spec_passes_on_warning_consistency(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses(consistency_json=_CONSISTENCY_WARNING))
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.stage == "execute"


def test_spec_artifact_count_constant() -> None:
    assert len(SPEC_ARTIFACTS) == 9
