"""Golden test: full CIO run against the acme-cio fixture (mocked LLM)."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.cio.agent import CIOAgent
from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.llm.mock import _default_mock_for_cli
from tests.golden._helpers import (
    assert_artifact_exact,
    assert_qa_within_tolerance,
    load_qa_scores,
)


SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "cio" / "acme-cio"


def _load_snapshot(name: str) -> dict:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _run_cio(tmp_path: Path):
    agent = CIOAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = CIOAgentInput(
        agent_name="cio",
        role_domain="cio-ops",
        user_request="Run CIO assessment",
        organization_name="Acme Corporation",
        strategic_priorities="digital transformation, cloud migration, cost optimization",
        it_maturity_level="Level 2 - Developing",
    )
    state = agent.run(request=inp, run_id="golden-acme-cio")
    return state, tmp_path / "runs" / "golden-acme-cio"


def test_golden_cio_required_artifacts_present(tmp_path: Path) -> None:
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_cio(tmp_path)
    for name in structure["required_artifacts"]:
        assert (run_dir / name).exists(), f"missing {name}"
    for tmpl in structure["required_brief_templates"]:
        assert (run_dir / "brief-template-library" / tmpl).exists(), f"missing brief {tmpl}"


def test_golden_cio_reaches_approval(tmp_path: Path) -> None:
    state, _ = _run_cio(tmp_path)
    assert state.stage == "approval"


def test_golden_cio_primary_artifact_non_empty(tmp_path: Path) -> None:
    """Under mock LLM, body is a scaffold string — assert non-emptiness only."""
    _, run_dir = _run_cio(tmp_path)
    body = (run_dir / "it-strategy.md").read_text(encoding="utf-8")
    assert len(body) > 0


def test_golden_cio_brief_template_library_complete(tmp_path: Path) -> None:
    """Verify brief-template-library exists and all 8 templates are non-empty."""
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_cio(tmp_path)
    library = run_dir / "brief-template-library"
    assert library.exists(), "brief-template-library directory missing"
    for tmpl_name in structure["required_brief_templates"]:
        tmpl_path = library / tmpl_name
        assert tmpl_path.exists(), f"missing brief template: {tmpl_name}"
        body = tmpl_path.read_text(encoding="utf-8")
        assert len(body) > 0, f"{tmpl_name} is empty"


def test_golden_cio_qa_scores_no_revision_required(tmp_path: Path) -> None:
    """QA scores JSON must exist and requires_revision must be false."""
    _, run_dir = _run_cio(tmp_path)
    scores_path = run_dir / "qa_scores.json"
    assert scores_path.exists()
    data = json.loads(scores_path.read_text(encoding="utf-8"))
    assert "requires_revision" in data, "'requires_revision' key missing from qa_scores.json"
    assert data["requires_revision"] is False, "qa_scores.json reports requires_revision=true"


def test_golden_cio_json_artifact_structure(tmp_path: Path) -> None:
    """JSON artifacts contain expected top-level keys."""
    _, run_dir = _run_cio(tmp_path)

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



# --- v0.9.2 content-aware golden assertions -----------------------------


def test_golden_cio_primary_artifact_content_matches_snapshot(tmp_path: Path) -> None:
    """Cio's it-strategy.md output must match the committed snapshot byte-for-byte.

    Under deterministic mock LLM the rendered scaffold is stable. A prompt
    refactor that changes output regenerates the snapshot via
    `make update-goldens`; an accidental drift fails the test with a unified
    diff so the change is reviewable.
    """
    _, run_dir = _run_cio(tmp_path)
    assert_artifact_exact(
        actual_path=run_dir / "it-strategy.md",
        fixture_path=SNAPSHOT_DIR / "it-strategy.md",
    )


def test_golden_cio_qa_scores_within_tolerance(tmp_path: Path) -> None:
    """QA scores must match the committed snapshot within 5% relative tolerance.

    Numeric tolerance applies only to ``scores`` and ``average``; ``passed``
    and ``requires_revision`` are exact-checked.
    """
    _, run_dir = _run_cio(tmp_path)
    actual = load_qa_scores(run_dir)
    fixture = json.loads((SNAPSHOT_DIR / "qa_scores.json").read_text(encoding="utf-8"))
    assert_qa_within_tolerance(actual, fixture, rtol=0.05)
