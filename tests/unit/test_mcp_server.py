"""Unit tests for the MCP server tool registration."""
from agentsuite.mcp_server import build_server


def test_build_server_registers_default_tools(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    server = build_server()
    tool_names = sorted(server.tool_names())
    assert "agentsuite_founder_run" in tool_names
    assert "agentsuite_founder_resume" in tool_names
    assert "agentsuite_founder_approve" in tool_names
    assert "agentsuite_founder_get_status" in tool_names
    assert "agentsuite_founder_list_runs" in tool_names
    assert "agentsuite_list_agents" in tool_names
    assert "agentsuite_kernel_artifacts" in tool_names
    assert "agentsuite_cost_report" in tool_names


def test_advanced_stage_tools_hidden_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("AGENTSUITE_EXPOSE_STAGES", raising=False)
    server = build_server()
    tool_names = server.tool_names()
    assert "agentsuite_founder_stage_intake" not in tool_names
    assert "agentsuite_founder_stage_extract" not in tool_names


def test_advanced_stage_tools_visible_when_env_set(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_EXPOSE_STAGES", "true")
    server = build_server()
    tool_names = server.tool_names()
    assert "agentsuite_founder_stage_intake" in tool_names
    assert "agentsuite_founder_stage_extract" in tool_names
    assert "agentsuite_founder_stage_spec" in tool_names
    assert "agentsuite_founder_stage_execute" in tool_names
    assert "agentsuite_founder_stage_qa" in tool_names


def test_only_enabled_agents_get_tools(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    server = build_server()
    tool_names = server.tool_names()
    assert not any(t.startswith("agentsuite_design_") for t in tool_names)
    assert not any(t.startswith("agentsuite_product_") for t in tool_names)


def test_founder_get_status_tool_handles_missing_run(monkeypatch, tmp_path):
    """founder_get_status raises FileNotFoundError for a run_id that doesn't exist."""
    import pytest
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    build_server()

    # Retrieve the registered handler by building a temp server and calling the underlying fn
    # The _ServerWrapper stores tool functions; we can find it by re-registering with a spy
    # Simpler: use the agent mcp_tools directly to call the handler via the same code path
    from agentsuite.agents.founder import mcp_tools as founder_mcp

    captured_tools: dict = {}

    class _SpyServer:
        def add_tool(self, name, fn):
            captured_tools[name] = fn

    founder_mcp.register_tools(
        _SpyServer(),
        agent_class=lambda: __import__(
            "agentsuite.agents.founder.agent", fromlist=["FounderAgent"]
        ).FounderAgent(output_root=tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    get_status = captured_tools["agentsuite_founder_get_status"]
    with pytest.raises(FileNotFoundError):
        get_status(run_id="nonexistent-run-xyz")


def test_founder_get_status_tool_returns_state_after_run(monkeypatch, tmp_path):
    """founder_get_status returns a RunState after a successful run."""
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))

    from agentsuite.agents.founder.agent import FounderAgent
    from agentsuite.agents.founder.input_schema import FounderAgentInput
    from agentsuite.agents.founder import mcp_tools as founder_mcp
    from agentsuite.kernel.schema import Constraints
    from agentsuite.llm.mock import _default_mock_for_cli

    # Run the agent so a state file exists
    agent = FounderAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="test mcp status",
        business_goal="MCP status test",
        project_slug="mcp-test",
        constraints=Constraints(),
    )
    agent.run(request=inp, run_id="mcp-status-run")

    # Now build the get_status tool and call it
    captured_tools: dict = {}

    class _SpyServer:
        def add_tool(self, name, fn):
            captured_tools[name] = fn

    founder_mcp.register_tools(
        _SpyServer(),
        agent_class=lambda: FounderAgent(output_root=tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    get_status = captured_tools["agentsuite_founder_get_status"]
    state = get_status(run_id="mcp-status-run")
    assert state.run_id == "mcp-status-run"
    assert state.stage == "approval"
    assert state.agent == "founder"
