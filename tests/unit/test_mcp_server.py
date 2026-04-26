"""Unit tests for the MCP server tool registration."""
from agentsuite.mcp_server import build_server


def test_build_server_registers_default_tools(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    server = build_server()
    tool_names = sorted(server.tool_names())
    assert "founder_run" in tool_names
    assert "founder_resume" in tool_names
    assert "founder_approve" in tool_names
    assert "founder_get_status" in tool_names
    assert "founder_list_runs" in tool_names
    assert "agentsuite_list_agents" in tool_names
    assert "agentsuite_kernel_artifacts" in tool_names
    assert "agentsuite_cost_report" in tool_names


def test_advanced_stage_tools_hidden_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("AGENTSUITE_EXPOSE_STAGES", raising=False)
    server = build_server()
    tool_names = server.tool_names()
    assert "founder_intake" not in tool_names
    assert "founder_extract" not in tool_names


def test_advanced_stage_tools_visible_when_env_set(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_EXPOSE_STAGES", "true")
    server = build_server()
    tool_names = server.tool_names()
    assert "founder_intake" in tool_names
    assert "founder_extract" in tool_names
    assert "founder_spec" in tool_names
    assert "founder_execute" in tool_names
    assert "founder_qa" in tool_names


def test_only_enabled_agents_get_tools(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    server = build_server()
    tool_names = server.tool_names()
    assert not any(t.startswith("design_") for t in tool_names)
    assert not any(t.startswith("product_") for t in tool_names)
