"""End-to-end Trust/Risk pipeline integration test (mock LLM)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agentsuite.agents.registry import default_registry
from agentsuite.agents.trust_risk.agent import TrustRiskAgent
from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC
from agentsuite.agents.trust_risk.stages.spec import SPEC_ARTIFACTS, ConsistencyCheckFailed
from agentsuite.llm.mock import MockLLMProvider, _default_mock_for_cli


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_trust_risk_full_pipeline_mock(tmp_path: Path) -> None:
    """Full Trust/Risk pipeline integration test against MockLLMProvider."""
    agent = TrustRiskAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = TrustRiskAgentInput(
        user_request="Run trust risk assessment",
        product_name="SecureOps Platform",
        risk_domain="hybrid cloud",
        stakeholder_context="CISO and risk committee",
    )
    state = agent.run(request=inp, run_id="integration-tr1")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-tr1"
    # All 9 spec artifacts (.md files)
    for stem in SPEC_ARTIFACTS:
        assert (run_dir / f"{stem}.md").exists(), f"missing spec artifact {stem}.md"
    # qa_scores.json
    assert (run_dir / "qa_scores.json").exists(), "missing qa_scores.json"


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_trust_risk_qa_scores_above_threshold(tmp_path: Path) -> None:
    """QA scores must all be >= 7.0 and requires_revision must be False."""
    agent = TrustRiskAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = TrustRiskAgentInput(
        user_request="Generate risk artifacts",
        product_name="VaultGuard",
        risk_domain="financial services",
        stakeholder_context="Compliance and audit team",
    )
    agent.run(request=inp, run_id="integration-tr2")

    run_dir = tmp_path / "runs" / "integration-tr2"
    qa_path = run_dir / "qa_scores.json"
    assert qa_path.exists(), "missing qa_scores.json"

    data = json.loads(qa_path.read_text())
    scores: dict = data.get("scores", data)

    expected_dims = [dim.name for dim in TRUST_RISK_RUBRIC.dimensions]
    for dim in expected_dims:
        assert dim in scores, f"rubric dimension '{dim}' missing from qa_scores.json"
        assert scores[dim] >= 7.0, (
            f"rubric dimension '{dim}' score {scores[dim]} below threshold 7.0"
        )

    # requires_revision must be false (key may be top-level or nested)
    requires_revision = data.get("requires_revision", False)
    assert requires_revision is False, (
        f"requires_revision expected False but got {requires_revision}"
    )


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_trust_risk_agent_via_registry(tmp_path: Path) -> None:
    """Trust/Risk agent instantiated via registry produces threat-model artifact."""
    import os as _os
    orig = _os.environ.get("AGENTSUITE_ENABLED_AGENTS")
    _os.environ["AGENTSUITE_ENABLED_AGENTS"] = "trust_risk"
    try:
        agent_class = default_registry().get_class("trust_risk")
        agent = agent_class(output_root=tmp_path, llm=_default_mock_for_cli())
    finally:
        if orig is None:
            _os.environ.pop("AGENTSUITE_ENABLED_AGENTS", None)
        else:
            _os.environ["AGENTSUITE_ENABLED_AGENTS"] = orig

    inp = TrustRiskAgentInput(
        user_request="Assess AI governance risk",
        product_name="PolicyBot",
        risk_domain="AI governance",
        stakeholder_context="Board and legal",
    )
    state = agent.run(request=inp, run_id="integration-tr3")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-tr3"
    threat_model = run_dir / "threat-model.md"
    assert threat_model.exists(), "missing threat-model.md"
    assert threat_model.stat().st_size > 0, "threat-model.md is empty"
    # Content assertion: primary artifact must contain threat/risk keywords
    threat_model_text = threat_model.read_text()
    assert "threat" in threat_model_text.lower() or "risk" in threat_model_text.lower(), (
        "threat-model.md does not contain expected security/risk content"
    )


def test_trust_risk_consistency_check_failure_raises(tmp_path: Path) -> None:
    """When consistency check returns a critical finding, ConsistencyCheckFailed is raised."""
    base = _default_mock_for_cli()
    # Remove the existing key that would match trust-risk consistency check.
    # TrustRisk spec.py system: "You are checking 9 trust-risk-agent artifacts for consistency."
    # Default mock key (full string): "You are checking 9 trust-risk-agent artifacts for consistency. Return ONLY JSON."
    existing_key = "You are checking 9 trust-risk-agent artifacts for consistency. Return ONLY JSON."
    patched_responses = {k: v for k, v in base.responses.items() if k != existing_key}
    critical_response = json.dumps({
        "mismatches": [
            {
                "dimension": "control_coverage",
                "severity": "critical",
                "detail": "Threat model identifies risk not covered by control framework",
            }
        ]
    })
    patched_responses["checking 9 trust-risk-agent artifacts for consistency"] = critical_response
    llm = MockLLMProvider(responses=patched_responses)

    agent = TrustRiskAgent(output_root=tmp_path, llm=llm)
    inp = TrustRiskAgentInput(
        user_request="test consistency failure",
        product_name="SecureApp",
        risk_domain="cloud infrastructure",
        stakeholder_context="CISO and risk team",
    )
    with pytest.raises(ConsistencyCheckFailed):
        agent.run(request=inp, run_id="trust-risk-consistency-fail")
