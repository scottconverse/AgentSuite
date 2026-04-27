"""Unit tests for agentsuite.agents.engineering.stages.spec."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.stages.spec import (
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
    "existing_patterns": ["repository pattern", "CQRS"],
    "known_bottlenecks": ["database connection pooling"],
    "security_risks": ["SQL injection vectors"],
    "tech_debt_items": ["legacy auth module"],
    "integration_points": ["payment gateway", "email service"],
    "open_questions": ["which message queue?"],
}

_CONSISTENCY_OK = json.dumps({
    "checks": [
        {
            "dimension": "api alignment",
            "status": "ok",
            "severity": "ok",
            "detail": "No issues found.",
        }
    ]
})

_CONSISTENCY_CRITICAL = json.dumps({
    "checks": [
        {
            "dimension": "security coverage",
            "status": "mismatch",
            "severity": "critical",
            "detail": "Security review contradicts deployment plan",
        }
    ]
})

_CONSISTENCY_WARNING = json.dumps({
    "checks": [
        {
            "dimension": "performance targets",
            "status": "mismatch",
            "severity": "warning",
            "detail": "One latency target lacks a data-model anchor",
        }
    ]
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering",
        user_request="design a payment processing system",
        system_name="PaymentCore",
        problem_domain="payment processing and settlement",
        tech_stack="Python + FastAPI + PostgreSQL + Redis",
        scale_requirements="10k RPM, 99.9% uptime, <200ms p99",
        security_requirements="PCI-DSS Level 1, OWASP Top 10",
        team_size="4 engineers, 1 SRE",
    )
    return RunState(run_id="r1", agent="engineering", stage="spec", inputs=inp)


def _spec_responses(consistency_json: str = _CONSISTENCY_OK) -> dict[str, str]:
    responses: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md for an engineering team"] = (
            f"# {stem.replace('-', ' ').title()}\n\nContent here"
        )
    responses["checking 9 engineering-agent artifacts"] = consistency_json
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
    assert "checks" in report


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
