"""Golden test: full Product run against the acme-app fixture (mocked LLM)."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.product.agent import ProductAgent
from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.llm.mock import _default_mock_for_cli


SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "product" / "acme-app"


def _load_snapshot(name: str) -> dict:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _run_product(tmp_path: Path):
    agent = ProductAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product-ops",
        user_request="acme product spec",
        product_name="AcmeApp",
        target_users="startup founders",
        core_problem="too much manual product work",
        project_slug="acme-app",
    )
    state = agent.run(request=inp, run_id="golden-acme-app")
    return state, tmp_path / "runs" / "golden-acme-app"


def test_golden_product_required_artifacts_present(tmp_path: Path) -> None:
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_product(tmp_path)
    for name in structure["required_artifacts"]:
        assert (run_dir / name).exists(), f"missing {name}"
    for tmpl in structure["required_brief_templates"]:
        assert (run_dir / "brief-template-library" / tmpl).exists(), f"missing brief {tmpl}"


def test_golden_product_reaches_approval(tmp_path: Path) -> None:
    state, _ = _run_product(tmp_path)
    assert state.stage == "approval"


def test_golden_product_prd_non_empty(tmp_path: Path) -> None:
    """Under mock LLM, body is a scaffold string — assert non-emptiness only."""
    _, run_dir = _run_product(tmp_path)
    body = (run_dir / "product-requirements-doc.md").read_text(encoding="utf-8")
    assert len(body) > 0


def test_golden_product_brief_template_library_complete(tmp_path: Path) -> None:
    """Verify brief-template-library exists and all 8 templates are non-empty."""
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_product(tmp_path)
    library = run_dir / "brief-template-library"
    assert library.exists(), "brief-template-library directory missing"
    for tmpl_name in structure["required_brief_templates"]:
        tmpl_path = library / tmpl_name
        assert tmpl_path.exists(), f"missing brief template: {tmpl_name}"
        body = tmpl_path.read_text(encoding="utf-8")
        assert len(body) > 0, f"{tmpl_name} is empty"


def test_golden_product_qa_scores_json_valid(tmp_path: Path) -> None:
    """QA scores JSON must be parseable and contain 'passed' and 'scores' keys."""
    _, run_dir = _run_product(tmp_path)
    scores_path = run_dir / "qa_scores.json"
    assert scores_path.exists()
    data = json.loads(scores_path.read_text(encoding="utf-8"))
    assert "passed" in data, "'passed' key missing from qa_scores.json"
    assert "scores" in data, "'scores' key missing from qa_scores.json"


def test_golden_product_json_artifact_structure(tmp_path: Path) -> None:
    """JSON artifacts contain expected top-level keys."""
    _, run_dir = _run_product(tmp_path)

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
