"""Unit tests for agentsuite.agents.product.stages.spec."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.stages.spec import (
    SPEC_ARTIFACTS,
    spec_stage,
)
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "user_pain_points": ["onboarding is too slow"],
    "competitor_gaps": ["no offline mode"],
    "market_signals": ["growing SMB segment"],
    "assumed_non_goals": ["enterprise SSO"],
    "open_questions": ["which payment provider?"],
}

_CONSISTENCY_OK = json.dumps({
    "mismatches": [
        {
            "dimension": "user personas",
            "status": "ok",
            "severity": "ok",
            "detail": "No issues found.",
        }
    ]
})

_CONSISTENCY_CRITICAL = json.dumps({
    "mismatches": [
        {
            "dimension": "feature alignment",
            "status": "mismatch",
            "severity": "critical",
            "detail": "P0 feature missing from roadmap",
        }
    ]
})

_CONSISTENCY_WARNING = json.dumps({
    "mismatches": [
        {
            "dimension": "metrics traceability",
            "status": "mismatch",
            "severity": "warning",
            "detail": "One metric lacks a PRD goal anchor",
        }
    ]
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product",
        user_request="build a task manager",
        product_name="TaskFlow",
        target_users="small business teams",
        core_problem="teams lose track of tasks across tools",
        technical_constraints="must work offline",
        timeline_constraint="MVP in 8 weeks",
        success_metric_goals="10% DAU increase in 30 days",
    )
    return RunState(run_id="r1", agent="product", stage="spec", inputs=inp)


def _spec_responses(consistency_json: str = _CONSISTENCY_OK) -> dict[str, str]:
    responses: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\n\nSpec content."
    responses["checking 9 product-agent artifacts"] = consistency_json
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


def test_spec_raises_on_critical_consistency_failure(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses(consistency_json=_CONSISTENCY_CRITICAL))
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.requires_revision is True
    assert new_state.stage == "execute"


def test_spec_passes_on_warning_consistency(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses(consistency_json=_CONSISTENCY_WARNING))
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.stage == "execute"


def test_spec_nine_artifact_count() -> None:
    assert len(SPEC_ARTIFACTS) == 9
