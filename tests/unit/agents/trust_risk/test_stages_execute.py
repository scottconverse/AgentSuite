"""Unit tests for agentsuite.agents.trust_risk.stages.execute."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.stages.execute import execute_stage
from agentsuite.agents.trust_risk.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState


_EXTRACTED = {
    "known_threats": ["SQL injection", "credential stuffing"],
    "existing_controls": ["WAF", "MFA enforcement"],
    "incident_patterns": ["data exfiltration attempt Q1 2025", "phishing campaign"],
    "vendor_risks": ["Acme Cloud Provider", "ThirdParty Auth SaaS"],
}


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="Assess cloud infrastructure security posture for Q2 2026",
        product_name="CloudVault",
        risk_domain="cloud infrastructure",
        stakeholder_context="CISO and DevSecOps team with low risk tolerance",
        regulatory_context="SOC 2 Type II, GDPR",
        compliance_frameworks="NIST CSF, ISO 27001, CIS Controls",
        threat_model_scope="external attackers, insider threats, supply chain",
    )
    return RunState(run_id="r1", agent="trust_risk", stage="execute", inputs=inp)


def _make_ctx(writer: ArtifactWriter) -> StageContext:
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_execute_advances_to_qa(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    result = execute_stage(_make_state(), _make_ctx(writer))
    assert result.stage == "qa"


def test_execute_renders_all_eight_templates(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    for name in TEMPLATE_NAMES:
        assert (writer.run_dir / "brief-template-library" / f"{name}.md").exists(), (
            f"Missing brief-template-library/{name}.md"
        )


def test_execute_writes_export_manifest(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    manifest_path = writer.run_dir / "export-manifest-template.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "product_name" in data
    assert "risk_domain" in data
    assert "brief_templates" in data
    assert "spec_artifacts" in data
    assert len(data["brief_templates"]) == 8


def test_execute_no_llm_call(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    ctx = _make_ctx(writer)
    execute_stage(_make_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens == 0
