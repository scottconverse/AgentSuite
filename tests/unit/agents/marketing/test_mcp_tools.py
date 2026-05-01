"""Unit tests for marketing.mcp_tools — RevisionRequired (TEST-004)."""
from __future__ import annotations

from pathlib import Path

from agentsuite.agents.marketing.agent import MarketingAgent
from agentsuite.agents.marketing.mcp_tools import MarketingRunRequest, register_tools
from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
from agentsuite.kernel.state_store import StateStore
from agentsuite.llm.mock import MockLLMProvider


class _StubServer:
    def __init__(self) -> None:
        self.tools: dict = {}

    def add_tool(self, name: str, fn) -> None:
        self.tools[name] = fn

    def tool_names(self) -> list[str]:
        return list(self.tools.keys())


# ---------------------------------------------------------------------------
# TEST-004 — marketing_approve returns structured dict on RevisionRequired
# ---------------------------------------------------------------------------

def test_marketing_approve_revision_required_returns_structured_error(tmp_path: Path) -> None:
    """marketing_approve must return a structured error dict (not raise) on RevisionRequired."""
    run_dir = tmp_path / "runs" / "r-mkt-rev"
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id="r-mkt-rev",
        agent="marketing",
        stage="approval",
        requires_revision=True,
        inputs=AgentRequest(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: MarketingAgent(output_root=tmp_path, llm=MockLLMProvider(responses={})),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    result = server.tools["agentsuite_marketing_approve"](
        run_id="r-mkt-rev", approver="scott", project_slug="proj"
    )
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert result["error"] == "revision_required"
    assert "qa_report_path" in result
    assert isinstance(result["qa_report_path"], str)
    assert "action" in result
