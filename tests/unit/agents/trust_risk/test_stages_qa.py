"""Unit tests for agentsuite.agents.trust_risk.stages.qa."""
from __future__ import annotations

import json
from pathlib import Path


from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.stages.qa import qa_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_PASSING_SCORES = {
    "threat_coverage": 8.0,
    "control_specificity": 7.5,
    "risk_quantification": 8.0,
    "regulatory_alignment": 7.0,
    "incident_readiness": 8.0,
    "zero_trust_posture": 7.5,
    "vendor_risk_awareness": 8.0,
    "audit_traceability": 7.0,
    "residual_risk_acceptance": 8.0,
}

_PASSING_RESPONSE = json.dumps({
    "scores": _PASSING_SCORES,
    "revision_instructions": ["Clarify residual risk review schedule"],
})

_PARTIAL_SCORES_RESPONSE = json.dumps({
    "scores": {
        "threat_coverage": 8.0,
        "control_specificity": 7.5,
        # remaining dimensions intentionally omitted
    },
    "revision_instructions": [],
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write(
        "threat-model.md",
        "# Threat Model\n\nContent.",
        kind="spec",
        stage="spec",
    )
    return writer


def _make_state() -> RunState:
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="assess security posture for AcmePay",
        product_name="AcmePay",
        risk_domain="financial services",
        stakeholder_context="CISO and CFO",
    )
    return RunState(run_id="r1", agent="trust_risk", stage="qa", inputs=inp)


def test_qa_calls_llm_and_writes_report(tmp_path: Path) -> None:
    """Mock LLM returns valid scores JSON; assert qa_report.md and qa_scores.json written."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 trust-risk-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    assert (writer.run_dir / "qa_report.md").exists()
    assert (writer.run_dir / "qa_scores.json").exists()


def test_qa_advances_to_approval(tmp_path: Path) -> None:
    """Assert state.stage == 'approval' after qa_stage runs."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 trust-risk-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"


def test_qa_score_reflects_rubric_result(tmp_path: Path) -> None:
    """Assert qa_scores.json contains 'passed' key from rubric result."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 trust-risk-agent": _PASSING_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    qa_stage(_make_state(), ctx)
    data = json.loads((writer.run_dir / "qa_scores.json").read_text(encoding="utf-8"))
    assert "passed" in data


def test_qa_handles_missing_scores_gracefully(tmp_path: Path) -> None:
    """Mock LLM returns partial scores; missing dims assigned 0.0 and stage completes."""
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses={"scoring 9 trust-risk-agent": _PARTIAL_SCORES_RESPONSE})
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    result = qa_stage(_make_state(), ctx)
    assert result.stage == "approval"
    assert result.requires_revision is True
