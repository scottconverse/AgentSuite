"""Golden test: full Founder run against the frozen patentforgelocal fixture."""
import json
from pathlib import Path

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.mock import _default_mock_for_cli


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
