"""Golden test: full Trust/Risk run against the acme-security fixture (mocked LLM)."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.trust_risk.agent import TrustRiskAgent
from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.llm.mock import _default_mock_for_cli


SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "trust_risk" / "acme-security"


def _load_snapshot(name: str) -> dict:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _run_trust_risk(tmp_path: Path):
    agent = TrustRiskAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="Run trust risk assessment",
        product_name="Acme Security Platform",
        risk_domain="cloud infrastructure",
        stakeholder_context="Enterprise CISO and compliance team",
    )
    state = agent.run(request=inp, run_id="golden-acme-security")
    return state, tmp_path / "runs" / "golden-acme-security"


def test_golden_trust_risk_required_artifacts_present(tmp_path: Path) -> None:
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_trust_risk(tmp_path)
    for name in structure["required_artifacts"]:
        assert (run_dir / name).exists(), f"missing {name}"
    for tmpl in structure["required_brief_templates"]:
        assert (run_dir / "brief-template-library" / tmpl).exists(), f"missing brief {tmpl}"


def test_golden_trust_risk_reaches_approval(tmp_path: Path) -> None:
    state, _ = _run_trust_risk(tmp_path)
    assert state.stage == "approval"


def test_golden_trust_risk_primary_artifact_non_empty(tmp_path: Path) -> None:
    """Under mock LLM, body is a scaffold string — assert non-emptiness only."""
    _, run_dir = _run_trust_risk(tmp_path)
    body = (run_dir / "threat-model.md").read_text(encoding="utf-8")
    assert len(body) > 0


def test_golden_trust_risk_brief_template_library_complete(tmp_path: Path) -> None:
    """Verify brief-template-library exists and all 8 templates are non-empty."""
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_trust_risk(tmp_path)
    library = run_dir / "brief-template-library"
    assert library.exists(), "brief-template-library directory missing"
    for tmpl_name in structure["required_brief_templates"]:
        tmpl_path = library / tmpl_name
        assert tmpl_path.exists(), f"missing brief template: {tmpl_name}"
        body = tmpl_path.read_text(encoding="utf-8")
        assert len(body) > 0, f"{tmpl_name} is empty"


def test_golden_trust_risk_qa_scores_no_revision_required(tmp_path: Path) -> None:
    """QA scores JSON must exist and requires_revision must be false."""
    _, run_dir = _run_trust_risk(tmp_path)
    scores_path = run_dir / "qa_scores.json"
    assert scores_path.exists()
    data = json.loads(scores_path.read_text(encoding="utf-8"))
    assert "requires_revision" in data, "'requires_revision' key missing from qa_scores.json"
    assert data["requires_revision"] is False, "qa_scores.json reports requires_revision=true"
