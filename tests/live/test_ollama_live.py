"""Live-Ollama tier — gated by RUN_LIVE_OLLAMA_TESTS=1 + a running daemon.

Zero cost (Ollama runs locally). Useful for offline validation without API keys.
Distinct from the cloud `live` tier so users without Anthropic/OpenAI/Gemini keys
can still validate the kernel + Founder pipeline against a real LLM.
"""
from pathlib import Path

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.ollama import OllamaProvider


pytestmark = pytest.mark.live_ollama


FIXTURE_DIR = Path(__file__).parent.parent.parent / "examples" / "patentforgelocal"


def test_founder_full_pipeline_against_local_ollama(tmp_path: Path) -> None:
    """Full Founder pipeline against the locally-running Ollama daemon.

    Asserts pipeline reaches approval stage, all 9 spec artifacts exist,
    brand-system.md has at least one markdown heading, and total cost is $0.
    """
    agent = FounderAgent(output_root=tmp_path, llm=OllamaProvider())
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="build creative ops for PFL",
        business_goal="Launch PatentForgeLocal v1",
        project_slug="pfl-ollama",
        inputs_dir=FIXTURE_DIR,
        founder_voice_samples=[FIXTURE_DIR / "voice-sample.txt"],
        constraints=Constraints(),
    )
    state = agent.run(request=inp, run_id="ollama-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "ollama-r1"
    for name in ["brand-system.md"] + [f"{s}.md" for s in SPEC_ARTIFACTS]:
        assert (run_dir / name).exists()
    body = (run_dir / "brand-system.md").read_text(encoding="utf-8")
    assert body.count("\n#") >= 1 or body.startswith("# ")
    assert state.cost_so_far.usd == 0.0
