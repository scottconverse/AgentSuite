"""Unit tests for agentsuite.agents.trust_risk.stages.spec."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.stages.spec import (
    SPEC_ARTIFACTS,
    spec_stage,
)
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "threat_actors": ["external attackers", "malicious insiders"],
    "control_gaps": ["no MFA on admin consoles", "unencrypted backups"],
    "regulatory_findings": ["HIPAA PHI handling incomplete"],
    "vendor_risks": ["third-party data processor unaudited"],
    "open_questions": ["scope of penetration test?"],
}

_CONSISTENCY_OK = json.dumps({
    "mismatches": [
        {
            "dimension": "control coverage",
            "status": "ok",
            "severity": "ok",
            "detail": "No issues found.",
        }
    ]
})

_CONSISTENCY_CRITICAL = json.dumps({
    "mismatches": [
        {
            "dimension": "compliance scope",
            "status": "mismatch",
            "severity": "critical",
            "detail": "Compliance matrix contradicts control framework scope",
        }
    ]
})

_CONSISTENCY_WARNING = json.dumps({
    "mismatches": [
        {
            "dimension": "residual risk",
            "status": "mismatch",
            "severity": "warning",
            "detail": "Residual risk acceptance threshold exceeds risk register values",
        }
    ]
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="assess security posture for our SaaS platform prior to SOC 2 audit",
        product_name="VaultSaaS",
        risk_domain="cloud infrastructure",
        stakeholder_context="CTO and compliance team; low risk tolerance for data breaches",
        regulatory_context="SOC 2 Type II, HIPAA",
        threat_model_scope="external attackers, insider threats, supply chain",
        compliance_frameworks="NIST CSF, ISO 27001, CIS Controls",
    )
    return RunState(run_id="r1", agent="trust_risk", stage="spec", inputs=inp)


def _spec_responses(consistency_json: str = _CONSISTENCY_OK) -> dict[str, str]:
    responses: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md for a trust and risk team"] = (
            f"# {stem.replace('-', ' ').title()}\n\nContent here"
        )
    responses["checking 9 trust-risk-agent artifacts"] = consistency_json
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
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.requires_revision is True
    assert new_state.stage == "execute"


def test_spec_passes_on_warning_consistency(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses(consistency_json=_CONSISTENCY_WARNING))
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.stage == "execute"


def test_spec_artifact_count_constant() -> None:
    assert len(SPEC_ARTIFACTS) == 9
