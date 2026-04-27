"""Golden test: full Marketing run against the acme-campaign fixture (mocked LLM)."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.marketing.agent import MarketingAgent
from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.llm.mock import _default_mock_for_cli


SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "marketing" / "acme-campaign"


def _load_snapshot(name: str) -> dict:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _run_marketing(tmp_path: Path):
    agent = MarketingAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="acme campaign marketing strategy",
        brand_name="Acme Corp",
        campaign_goal="Drive product signups",
        target_market="SMB software teams",
    )
    state = agent.run(request=inp, run_id="golden-acme-campaign")
    return state, tmp_path / "runs" / "golden-acme-campaign"


def test_golden_marketing_required_artifacts_present(tmp_path: Path) -> None:
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_marketing(tmp_path)
    for name in structure["required_artifacts"]:
        assert (run_dir / name).exists(), f"missing {name}"
    for tmpl in structure["required_brief_templates"]:
        assert (run_dir / "brief-template-library" / tmpl).exists(), f"missing brief {tmpl}"


def test_golden_marketing_reaches_approval(tmp_path: Path) -> None:
    state, _ = _run_marketing(tmp_path)
    assert state.stage == "approval"


def test_golden_marketing_spec_artifact_non_empty(tmp_path: Path) -> None:
    """Under mock LLM, body is a scaffold string — assert non-emptiness only."""
    _, run_dir = _run_marketing(tmp_path)
    body = (run_dir / "campaign-brief.md").read_text(encoding="utf-8")
    assert len(body) > 0


def test_golden_marketing_brief_template_library_complete(tmp_path: Path) -> None:
    """Verify brief-template-library exists and all 8 templates are non-empty."""
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_marketing(tmp_path)
    library = run_dir / "brief-template-library"
    assert library.exists(), "brief-template-library directory missing"
    for tmpl_name in structure["required_brief_templates"]:
        tmpl_path = library / tmpl_name
        assert tmpl_path.exists(), f"missing brief template: {tmpl_name}"
        body = tmpl_path.read_text(encoding="utf-8")
        assert len(body) > 0, f"{tmpl_name} is empty"


def test_golden_marketing_qa_scores_json_valid(tmp_path: Path) -> None:
    """QA scores JSON must be parseable and contain 'passed' and 'scores' keys."""
    _, run_dir = _run_marketing(tmp_path)
    scores_path = run_dir / "qa_scores.json"
    assert scores_path.exists()
    data = json.loads(scores_path.read_text(encoding="utf-8"))
    assert "passed" in data, "'passed' key missing from qa_scores.json"
    assert "scores" in data, "'scores' key missing from qa_scores.json"
