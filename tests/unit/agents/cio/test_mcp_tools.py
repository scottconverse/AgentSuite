"""Unit tests for cio.mcp_tools — security (ENG-001) and happy-path coverage."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentsuite.agents.cio.mcp_tools import SPEC_ARTIFACTS, register_tools


class _StubServer:
    def __init__(self) -> None:
        self.tools: dict = {}

    def add_tool(self, name: str, fn) -> None:
        self.tools[name] = fn

    def tool_names(self) -> list[str]:
        return list(self.tools.keys())


def _make_server(tmp_path: Path) -> _StubServer:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: None,  # agent not needed for artifact/template tools
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    return server


# ---------------------------------------------------------------------------
# ENG-001: path traversal guard — artifact_name
# ---------------------------------------------------------------------------

def test_get_artifact_rejects_path_traversal(tmp_path: Path) -> None:
    """get_artifact must return an error dict (not file contents) for ../../.env."""
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_cio_get_artifact"](
        run_id="run-safe-001", artifact_name="../../.env"
    )
    assert "error" in result
    assert ".env" not in result.get("content", "")


def test_get_artifact_rejects_unknown_artifact(tmp_path: Path) -> None:
    """get_artifact must return an error dict for an artifact name not in the allowlist."""
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_cio_get_artifact"](
        run_id="run-safe-001", artifact_name="secret-data"
    )
    assert "error" in result
    assert "Unknown artifact" in result["error"]


def test_get_artifact_returns_content_for_valid_name(tmp_path: Path) -> None:
    """get_artifact must return file content when artifact_name is valid and file exists."""
    run_id = "run-cio-test"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    artifact_name = SPEC_ARTIFACTS[0]  # "it-strategy"
    (run_dir / f"{artifact_name}.md").write_text("# IT Strategy\nContent.", encoding="utf-8")

    server = _make_server(tmp_path)
    result = server.tools["agentsuite_cio_get_artifact"](
        run_id=run_id, artifact_name=artifact_name
    )
    assert "error" not in result
    assert result["artifact_name"] == artifact_name
    assert "IT Strategy" in result["content"]


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_tools_adds_ten_default_tools(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    expected = {
        "agentsuite_cio_run",
        "agentsuite_cio_approve",
        "agentsuite_cio_list_runs",
        "agentsuite_cio_get_artifact",
        "agentsuite_cio_list_artifacts",
        "agentsuite_cio_get_qa_scores",
        "agentsuite_cio_get_brief_template",
        "agentsuite_cio_list_brief_templates",
        "agentsuite_cio_get_revision_instructions",
        "agentsuite_cio_get_run_status",
    }
    assert expected == set(server.tool_names())


def test_register_tools_expose_stages_adds_fifteen_tools(tmp_path: Path) -> None:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: None,
        output_root_fn=lambda: tmp_path,
        expose_stages=True,
    )
    assert len(server.tools) == 15
    for stage_tool in (
        "agentsuite_cio_stage_intake",
        "agentsuite_cio_stage_extract",
        "agentsuite_cio_stage_spec",
        "agentsuite_cio_stage_execute",
        "agentsuite_cio_stage_qa",
    ):
        assert stage_tool in server.tool_names()


# ---------------------------------------------------------------------------
# list_brief_templates smoke test
# ---------------------------------------------------------------------------

def test_list_brief_templates_returns_all_template_names(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_cio_list_brief_templates"]()
    assert "templates" in result
    assert len(result["templates"]) == 8


def test_get_brief_template_rejects_unknown_name(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_cio_get_brief_template"](template_name="../../hack")
    assert "error" in result


def test_list_runs_empty_when_no_runs(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    runs = server.tools["agentsuite_cio_list_runs"]()
    assert runs == []
