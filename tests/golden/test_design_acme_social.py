"""Golden test: full Design run against the acme-social fixture (mocked LLM)."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.design.agent import DesignAgent
from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.llm.mock import _default_mock_for_cli


SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "design" / "acme-social"


def _load_snapshot(name: str) -> dict:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _run_design(tmp_path: Path):
    agent = DesignAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="design-ops",
        user_request="create social media campaign assets",
        target_audience="developers and tech-savvy early adopters",
        campaign_goal="drive signups for Acme SaaS product launch",
        channel="social",
        project_slug="acme-social",
    )
    state = agent.run(request=inp, run_id="golden-d1")
    return state, tmp_path / "runs" / "golden-d1"


def test_golden_design_required_artifacts_present(tmp_path: Path) -> None:
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_design(tmp_path)
    for name in structure["required_artifacts"]:
        assert (run_dir / name).exists(), f"missing {name}"
    for tmpl in structure["required_brief_templates"]:
        assert (run_dir / "brief-template-library" / tmpl).exists(), f"missing brief {tmpl}"


def test_golden_design_reaches_approval(tmp_path: Path) -> None:
    state, _ = _run_design(tmp_path)
    assert state.stage == "approval"


def test_golden_design_visual_direction_non_empty(tmp_path: Path) -> None:
    """Under mock LLM, bodies are scaffold strings — assert non-emptiness only."""
    _, run_dir = _run_design(tmp_path)
    body = (run_dir / "visual-direction.md").read_text(encoding="utf-8")
    assert len(body) > 0


def test_golden_design_brief_template_library_complete(tmp_path: Path) -> None:
    """Verify brief-template-library exists and all 8 templates are non-empty."""
    _, run_dir = _run_design(tmp_path)
    library = run_dir / "brief-template-library"
    assert library.exists(), "brief-template-library directory missing"
    templates = list(library.glob("*.md"))
    assert len(templates) == 8, f"expected 8 templates, got {len(templates)}"
    for tmpl_path in templates:
        body = tmpl_path.read_text(encoding="utf-8")
        assert len(body) > 0, f"{tmpl_path.name} is empty"


def test_golden_design_qa_scores_json_valid(tmp_path: Path) -> None:
    """QA scores JSON must be parseable and contain a scores key."""
    _, run_dir = _run_design(tmp_path)
    scores_path = run_dir / "qa_scores.json"
    assert scores_path.exists()
    data = json.loads(scores_path.read_text(encoding="utf-8"))
    assert "scores" in data


def test_golden_design_json_artifact_structure(tmp_path: Path) -> None:
    """JSON artifacts contain expected top-level keys."""
    _, run_dir = _run_design(tmp_path)

    # qa_scores.json structure
    qa = json.loads((run_dir / "qa_scores.json").read_text(encoding="utf-8"))
    assert "scores" in qa, "qa_scores.json missing 'scores' key"
    assert "average" in qa, "qa_scores.json missing 'average' key"
    assert "passed" in qa, "qa_scores.json missing 'passed' key"
    assert "requires_revision" in qa, "qa_scores.json missing 'requires_revision' key"

    # consistency_report.json structure
    cr = json.loads((run_dir / "consistency_report.json").read_text(encoding="utf-8"))
    assert "mismatches" in cr, "consistency_report.json missing 'mismatches' key"

    # extracted_context.json is valid JSON with at least one key
    ec = json.loads((run_dir / "extracted_context.json").read_text(encoding="utf-8"))
    assert isinstance(ec, dict) and len(ec) > 0, "extracted_context.json is empty or not a dict"
