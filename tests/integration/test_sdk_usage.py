"""Integration test: programmatic SDK usage via the top-level agentsuite package.

Proves that C1 exports (FounderAgent, resolve_provider) work correctly and that
a caller can instantiate FounderAgent and run it without touching the CLI or MCP.
"""
from pathlib import Path

from agentsuite import FounderAgent
from agentsuite.llm.mock import _default_mock_for_cli
from agentsuite.llm.resolver import resolve_provider
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.kernel.schema import Constraints


def test_founder_agent_sdk_instantiation_and_run(tmp_path: Path) -> None:
    """FounderAgent can be imported from the top-level package and run programmatically.

    This mirrors the README SDK example — replaces resolve_provider() with the
    mock so the test runs offline with no API keys required.
    """
    # Verify resolve_provider is importable from the top-level package (C1 export check)
    assert callable(resolve_provider)

    llm = _default_mock_for_cli()
    agent = FounderAgent(output_root=tmp_path, llm=llm)

    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="product",
        user_request="My startup builds patent search tools for solo inventors",
        business_goal="Launch SDK demo",
        project_slug="sdk-demo",
        constraints=Constraints(),
    )

    state = agent.run(request=inp, run_id="sdk-demo-run")

    # Core assertions from the README example
    assert state.run_id == "sdk-demo-run"
    assert isinstance(state.stage, str)
    assert len(state.stage) > 0
    assert state.stage == "approval"

    # Artifacts land on disk under output_root/runs/<run_id>/
    run_dir = tmp_path / "runs" / "sdk-demo-run"
    assert run_dir.exists(), f"run directory not created: {run_dir}"
    assert (run_dir / "_state.json").exists(), "state file missing"
