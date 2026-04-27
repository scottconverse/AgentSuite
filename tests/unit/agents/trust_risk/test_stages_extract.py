"""Unit tests for agentsuite.agents.trust_risk.stages.extract."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.stages.extract import extract_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_VALID_EXTRACT_JSON = json.dumps({
    "known_threats": ["SQL injection via public API endpoints"],
    "existing_controls": ["WAF deployed at perimeter", "MFA enforced for all admin accounts"],
    "compliance_gaps": ["No formal data retention policy documented"],
    "incident_patterns": ["Three credential-stuffing attempts in past 12 months"],
    "vendor_risks": ["Third-party payment processor not SOC 2 certified"],
    "open_questions": ["What is the RTO/RPO for the primary database?"],
})


def _make_ctx(
    tmp_path: Path,
    llm: MockLLMProvider,
    sources: list[dict] | None = None,
) -> tuple[StageContext, ArtifactWriter]:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json(
        "inputs_manifest.json",
        {
            "product_name": "TestProduct",
            "sources": sources or [],
        },
        kind="data",
        stage="intake",
    )
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm}), writer


def _make_state() -> RunState:
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="assess security posture",
        product_name="TestProduct",
        risk_domain="cloud infrastructure",
        stakeholder_context="CISO and engineering leads; low risk tolerance",
    )
    return RunState(run_id="r1", agent="trust_risk", stage="extract", inputs=inp)


def test_extract_calls_llm_and_writes_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["known_threats"] == ["SQL injection via public API endpoints"]


def test_extract_advances_to_spec(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, _ = _make_ctx(tmp_path, llm)
    result = extract_stage(_make_state(), ctx)
    assert result.stage == "spec"


def test_extract_handles_invalid_json_gracefully(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": "not json"})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("parse_error") is True
    assert payload["known_threats"] == []


def test_extract_buckets_sources_by_kind(tmp_path: Path) -> None:
    sources = [
        {"path": "/docs/security-policy.pdf", "kind": "policy-doc"},
        {"path": "/docs/access-control.pdf", "kind": "policy-doc"},
        {"path": "/docs/incident-2024-03.pdf", "kind": "incident-report"},
        {"path": "/docs/other-doc.pdf", "kind": "other"},
    ]
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm, sources=sources)
    extract_stage(_make_state(), ctx)
    # Verify stage completed (sources were bucketed without error)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "parse_error" not in payload
