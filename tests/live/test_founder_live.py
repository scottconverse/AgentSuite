"""Live tier — gated by RUN_LIVE_TESTS=1. Uses real LLM, capped at $3 per test."""
from pathlib import Path

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.resolver import resolve_provider


pytestmark = pytest.mark.live


FIXTURE_DIR = Path(__file__).parent.parent.parent / "examples" / "patentforgelocal"
PER_TEST_CAP_USD = 3.0


def test_founder_full_pipeline_live(tmp_path, monkeypatch):
    """Full pipeline against real LLM. Runs only at v0.X.0 release boundaries.

    Cost-capped at ``PER_TEST_CAP_USD`` via the ``AGENTSUITE_COST_CAP_USD`` env.
    Asserts: pipeline reaches approval stage, all 9 spec artifacts exist,
    brand-system.md has real markdown headings, total cost under cap.
    """
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", str(PER_TEST_CAP_USD))
    agent = FounderAgent(output_root=tmp_path, llm=resolve_provider())
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="build creative ops for PFL",
        business_goal="Launch PatentForgeLocal v1",
        project_slug="pfl-live",
        inputs_dir=FIXTURE_DIR,
        founder_voice_samples=[FIXTURE_DIR / "voice-sample.txt"],
        constraints=Constraints(),
    )
    state = agent.run(request=inp, run_id="live-full-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "live-full-r1"
    for name in ["brand-system.md"] + [f"{s}.md" for s in SPEC_ARTIFACTS]:
        assert (run_dir / name).exists()
    body = (run_dir / "brand-system.md").read_text(encoding="utf-8")
    # Real model output: should have markdown headings
    assert body.count("\n#") >= 3 or body.startswith("# ")
    # Cost stayed under per-test cap
    assert state.cost_so_far.usd <= PER_TEST_CAP_USD
