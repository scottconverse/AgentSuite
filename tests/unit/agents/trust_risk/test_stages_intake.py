"""Unit tests for agentsuite.agents.trust_risk.stages.intake."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.stages.intake import intake_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _make_state(tmp_path: Path, **overrides: object) -> RunState:
    defaults: dict[str, object] = {
        "agent_name": "trust_risk",
        "role_domain": "trust-risk-ops",
        "user_request": "assess cloud infrastructure risk posture",
        "product_name": "AcmeCloud",
        "risk_domain": "cloud infrastructure",
        "stakeholder_context": "engineering and security leadership",
    }
    defaults.update(overrides)
    inp = TrustRiskAgentInput(**defaults)  # type: ignore[arg-type]
    return RunState(run_id="r1", agent="trust_risk", inputs=inp)


def _make_ctx(tmp_path: Path) -> StageContext:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_intake_creates_manifest_json(tmp_path: Path) -> None:
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    for key in ("product_name", "risk_domain", "stakeholder_context", "regulatory_context",
                 "threat_model_scope", "compliance_frameworks", "sources", "source_count"):
        assert key in data


def test_intake_classifies_existing_policies(tmp_path: Path) -> None:
    doc = tmp_path / "security-policy.pdf"
    doc.write_text("security policy content")
    state = _make_state(tmp_path, existing_policies=[doc])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "policy-doc" in kinds


def test_intake_classifies_incident_reports(tmp_path: Path) -> None:
    doc = tmp_path / "incident-2024-01.docx"
    doc.write_text("incident report content")
    state = _make_state(tmp_path, incident_reports=[doc])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "incident-report" in kinds


def test_intake_advances_to_extract(tmp_path: Path) -> None:
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    result = intake_stage(state, ctx)
    assert result.stage == "extract"


def test_intake_source_count(tmp_path: Path) -> None:
    policy1 = tmp_path / "policy-access-control.pdf"
    policy1.write_text("access control policy")
    policy2 = tmp_path / "data-governance.md"
    policy2.write_text("data governance")
    incident1 = tmp_path / "incident-report-q1.txt"
    incident1.write_text("incident report Q1")
    state = _make_state(
        tmp_path,
        existing_policies=[policy1, policy2],
        incident_reports=[incident1],
    )
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    assert data["source_count"] == 3
