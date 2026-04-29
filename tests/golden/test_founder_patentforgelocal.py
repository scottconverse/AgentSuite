"""Golden test: full Founder run against the frozen patentforgelocal fixture."""
import json
from pathlib import Path


from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.mock import _default_mock_for_cli
from tests.golden._helpers import (
    assert_artifact_exact,
    assert_qa_within_tolerance,
    load_qa_scores,
)


SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "founder" / "patentforgelocal"
FIXTURE_DIR = Path(__file__).parent.parent.parent / "examples" / "patentforgelocal"


def _load_snapshot(name: str) -> dict:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _run_founder(tmp_path: Path):
    agent = FounderAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="build creative ops for PatentForgeLocal",
        business_goal="Launch PatentForgeLocal v1",
        project_slug="pfl",
        inputs_dir=FIXTURE_DIR,
        founder_voice_samples=[FIXTURE_DIR / "voice-sample.txt"],
        constraints=Constraints(),
    )
    state = agent.run(request=inp, run_id="golden-r1")
    return state, tmp_path / "runs" / "golden-r1"


def test_golden_required_artifacts_present(tmp_path):
    structure = _load_snapshot("structure.json")
    _, run_dir = _run_founder(tmp_path)
    for name in structure["required_artifacts"]:
        assert (run_dir / name).exists(), f"missing {name}"
    for tmpl in structure["required_brief_templates"]:
        assert (run_dir / "brief-template-library" / tmpl).exists()


def test_golden_brand_system_non_empty(tmp_path):
    """Under mock LLM, bodies are scaffold strings — assert non-emptiness only.
    Real heading checks live in the live tier (Task 30)."""
    _, run_dir = _run_founder(tmp_path)
    body = (run_dir / "brand-system.md").read_text(encoding="utf-8")
    assert len(body) > 0


def test_golden_critical_phrase_blocklist_in_brief_templates(tmp_path):
    """Under mock LLM, phrase blocklist is not enforced — the mock generates scaffold text.
    Real cliché phrase validation lives in the live tier (Task 30) where the actual
    LLM-rendered output is subject to quality assertions.
    This test verifies only that the brief template library exists and is non-empty."""
    _, run_dir = _run_founder(tmp_path)
    library = run_dir / "brief-template-library"
    assert library.exists(), "brief-template-library directory missing"
    templates = list(library.glob("*.md"))
    assert len(templates) > 0, "no templates found in brief-template-library"
    for tmpl_path in templates:
        body = tmpl_path.read_text(encoding="utf-8")
        assert len(body) > 0, f"{tmpl_path.name} is empty"


def test_golden_founder_json_artifact_structure(tmp_path):
    """JSON artifacts contain expected top-level keys."""
    _, run_dir = _run_founder(tmp_path)

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


# --- v0.9.0 content-aware golden assertions -----------------------------


def test_golden_brand_system_content_matches_snapshot(tmp_path):
    """Founder's brand-system.md output must match the committed snapshot byte-for-byte.

    Under deterministic mock LLM the rendered scaffold is stable. A prompt
    refactor that changes output regenerates the snapshot via
    `make update-goldens`; an accidental drift fails the test with a unified
    diff so the change is reviewable.
    """
    _, run_dir = _run_founder(tmp_path)
    assert_artifact_exact(
        actual_path=run_dir / "brand-system.md",
        fixture_path=SNAPSHOT_DIR / "brand-system.md",
    )


def test_golden_qa_scores_within_tolerance(tmp_path):
    """QA scores must match the committed snapshot within 5% relative tolerance.

    Numeric tolerance applies only to ``scores`` and ``average``; ``passed``
    and ``requires_revision`` are exact-checked. The split is enforced by
    the helper so future contributors can't relax text-content drift by
    sprinkling tolerance over the wrong field.
    """
    _, run_dir = _run_founder(tmp_path)
    actual = load_qa_scores(run_dir)
    fixture = json.loads((SNAPSHOT_DIR / "qa_scores.json").read_text(encoding="utf-8"))
    assert_qa_within_tolerance(actual, fixture, rtol=0.05)
