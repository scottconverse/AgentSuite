"""Unit tests for engineering.mcp_tools — registration, schema defaults, get_status, RevisionRequired."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentsuite.agents.engineering.agent import EngineeringAgent
from agentsuite.agents.engineering.mcp_tools import EngineeringRunRequest, register_tools
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


def _make_server(tmp_path: Path) -> _StubServer:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: EngineeringAgent(output_root=tmp_path, llm=MockLLMProvider(responses={})),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    return server


# ---------------------------------------------------------------------------
# TEST-003: Tool registration — expected tools are present by name
# ---------------------------------------------------------------------------

def test_engineering_register_tools_adds_five_default_tools(tmp_path: Path) -> None:
    """register_tools must register exactly the 5 canonical engineering tool names."""
    server = _make_server(tmp_path)
    expected = {
        "agentsuite_engineering_run",
        "agentsuite_engineering_resume",
        "agentsuite_engineering_approve",
        "agentsuite_engineering_get_status",
        "agentsuite_engineering_list_runs",
    }
    assert expected == set(server.tool_names())


def test_engineering_register_tools_expose_stages_adds_ten_tools(tmp_path: Path) -> None:
    """expose_stages=True must add 5 stage tools on top of the 5 defaults."""
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: EngineeringAgent(output_root=tmp_path, llm=MockLLMProvider(responses={})),
        output_root_fn=lambda: tmp_path,
        expose_stages=True,
    )
    assert len(server.tools) == 10
    for stage_tool in (
        "agentsuite_engineering_stage_intake",
        "agentsuite_engineering_stage_extract",
        "agentsuite_engineering_stage_spec",
        "agentsuite_engineering_stage_execute",
        "agentsuite_engineering_stage_qa",
    ):
        assert stage_tool in server.tool_names()


# ---------------------------------------------------------------------------
# TEST-003: EngineeringRunRequest schema defaults
# ---------------------------------------------------------------------------

def test_engineering_run_request_minimal_required_fields() -> None:
    """EngineeringRunRequest must accept minimal required fields and populate defaults."""
    req = EngineeringRunRequest(
        system_name="acme-api",
        problem_domain="event processing",
        tech_stack="Python + FastAPI",
        scale_requirements="1k RPM",
        user_request="build",
    )
    assert req.agent_name == "engineering"
    assert req.role_domain == "engineering"
    assert req.run_id is None                # default: auto-generated at runtime
    assert req.security_requirements == ""   # optional field defaults to empty


def test_engineering_run_request_run_id_default_is_none() -> None:
    """run_id must default to None so the tool can generate a timestamp-based id."""
    req = EngineeringRunRequest(
        system_name="x",
        problem_domain="y",
        tech_stack="z",
        scale_requirements="n",
        user_request="go",
    )
    assert req.run_id is None


def test_engineering_run_request_explicit_run_id_accepted() -> None:
    """Callers may supply their own run_id."""
    req = EngineeringRunRequest(
        system_name="x",
        problem_domain="y",
        tech_stack="z",
        scale_requirements="n",
        user_request="go",
        run_id="my-custom-id",
    )
    assert req.run_id == "my-custom-id"


# ---------------------------------------------------------------------------
# TEST-003: get_status round-trip
# ---------------------------------------------------------------------------

def test_engineering_get_status_returns_expected_fields(tmp_path: Path) -> None:
    """get_status must return a RunState with the correct run_id, agent, and stage."""
    run_id = "r-eng-status"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id=run_id,
        agent="engineering",
        stage="approval",
        inputs=AgentRequest(
            agent_name="engineering",
            role_domain="engineering",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)

    server = _make_server(tmp_path)
    result = server.tools["agentsuite_engineering_get_status"](run_id)

    assert result.run_id == run_id
    assert result.agent == "engineering"
    assert result.stage == "approval"


def test_engineering_get_status_raises_on_missing_run(tmp_path: Path) -> None:
    """get_status must raise FileNotFoundError when no state file exists for run_id."""
    server = _make_server(tmp_path)
    with pytest.raises(FileNotFoundError):
        server.tools["agentsuite_engineering_get_status"]("nonexistent-run")


def test_engineering_list_runs_empty_when_no_runs(tmp_path: Path) -> None:
    """list_runs must return an empty list when no runs directory exists."""
    server = _make_server(tmp_path)
    assert server.tools["agentsuite_engineering_list_runs"]() == []


# ---------------------------------------------------------------------------
# TEST-004 — engineering_approve returns structured dict on RevisionRequired
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# UX-006 — engineering_list_runs filters by project_slug
# ---------------------------------------------------------------------------

def test_engineering_list_runs_filters_by_project_slug(tmp_path: Path) -> None:
    """engineering_list_runs(project_slug='x') must return only runs with project_slug == 'x'."""
    from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
    from agentsuite.kernel.schema import Cost

    def _make_run(run_id: str, project_slug: str | None) -> None:
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        inp = EngineeringAgentInput(
            agent_name="engineering",
            role_domain="engineering",
            user_request="test",
            system_name="Sys",
            problem_domain="payments",
            tech_stack="Python + FastAPI",
            scale_requirements="10k RPM",
            project_slug=project_slug,
        )
        state = RunState(
            run_id=run_id,
            agent="engineering",
            stage="approval",
            inputs=inp,
            cost_so_far=Cost(),
        )
        StateStore(run_dir=run_dir).save(state)

    _make_run("e-slug-a", "slug-a")
    _make_run("e-slug-b", "slug-b")
    _make_run("e-no-slug", None)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: None,
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    runs = server.tools["agentsuite_engineering_list_runs"](project_slug="slug-a")
    assert len(runs) == 1, f"Expected 1, got {len(runs)}: {[r.run_id for r in runs]}"
    assert runs[0].run_id == "e-slug-a"

    runs = server.tools["agentsuite_engineering_list_runs"](project_slug="slug-b")
    assert len(runs) == 1
    assert runs[0].run_id == "e-slug-b"

    runs = server.tools["agentsuite_engineering_list_runs"](project_slug=None)
    assert len(runs) == 3


# ---------------------------------------------------------------------------
# TEST-004 — engineering_approve returns structured dict on RevisionRequired
# ---------------------------------------------------------------------------

def test_engineering_approve_revision_required_returns_structured_error(tmp_path: Path) -> None:
    """engineering_approve must return a structured error dict (not raise) on RevisionRequired."""
    run_dir = tmp_path / "runs" / "r-eng-rev"
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id="r-eng-rev",
        agent="engineering",
        stage="approval",
        requires_revision=True,
        inputs=AgentRequest(
            agent_name="engineering",
            role_domain="engineering",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: EngineeringAgent(output_root=tmp_path, llm=MockLLMProvider(responses={})),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    result = server.tools["agentsuite_engineering_approve"](
        run_id="r-eng-rev", approver="scott", project_slug="proj"
    )
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert result["error"] == "revision_required"
    assert "qa_report_path" in result
    assert isinstance(result["qa_report_path"], str)
    assert "action" in result
