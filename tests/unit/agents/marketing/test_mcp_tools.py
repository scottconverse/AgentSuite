"""Unit tests for marketing.mcp_tools — registration, schema defaults, get_status, RevisionRequired."""
from __future__ import annotations

from pathlib import Path

import pytest

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


def _make_server(tmp_path: Path) -> _StubServer:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: MarketingAgent(output_root=tmp_path, llm=MockLLMProvider(responses={})),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    return server


# ---------------------------------------------------------------------------
# TEST-003: Tool registration — expected tools are present by name
# ---------------------------------------------------------------------------

def test_marketing_register_tools_adds_five_default_tools(tmp_path: Path) -> None:
    """register_tools must register exactly the 5 canonical marketing tool names."""
    server = _make_server(tmp_path)
    expected = {
        "agentsuite_marketing_run",
        "agentsuite_marketing_resume",
        "agentsuite_marketing_approve",
        "agentsuite_marketing_get_status",
        "agentsuite_marketing_list_runs",
    }
    assert expected == set(server.tool_names())


def test_marketing_register_tools_expose_stages_adds_ten_tools(tmp_path: Path) -> None:
    """expose_stages=True must add 5 stage tools on top of the 5 defaults."""
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: MarketingAgent(output_root=tmp_path, llm=MockLLMProvider(responses={})),
        output_root_fn=lambda: tmp_path,
        expose_stages=True,
    )
    assert len(server.tools) == 10
    for stage_tool in (
        "agentsuite_marketing_stage_intake",
        "agentsuite_marketing_stage_extract",
        "agentsuite_marketing_stage_spec",
        "agentsuite_marketing_stage_execute",
        "agentsuite_marketing_stage_qa",
    ):
        assert stage_tool in server.tool_names()


# ---------------------------------------------------------------------------
# TEST-003: MarketingRunRequest schema defaults
# ---------------------------------------------------------------------------

def test_marketing_run_request_minimal_required_fields() -> None:
    """MarketingRunRequest must accept minimal required fields and populate defaults."""
    req = MarketingRunRequest(
        brand_name="Acme Corp",
        campaign_goal="drive signups",
        target_market="SMBs",
        user_request="run marketing agent",
    )
    assert req.agent_name == "marketing"
    assert req.role_domain == "marketing-ops"
    assert req.run_id is None       # default: auto-generated at runtime
    assert req.budget_range == ""   # optional field defaults to empty


def test_marketing_run_request_run_id_default_is_none() -> None:
    """run_id must default to None."""
    req = MarketingRunRequest(
        brand_name="X",
        campaign_goal="Y",
        target_market="Z",
        user_request="go",
    )
    assert req.run_id is None


def test_marketing_run_request_explicit_run_id_accepted() -> None:
    """Callers may supply their own run_id."""
    req = MarketingRunRequest(
        brand_name="X",
        campaign_goal="Y",
        target_market="Z",
        user_request="go",
        run_id="mkt-run-42",
    )
    assert req.run_id == "mkt-run-42"


# ---------------------------------------------------------------------------
# TEST-003: get_status round-trip
# ---------------------------------------------------------------------------

def test_marketing_get_status_returns_expected_fields(tmp_path: Path) -> None:
    """get_status must return a RunState with the correct run_id, agent, and stage."""
    run_id = "r-mkt-status"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id=run_id,
        agent="marketing",
        stage="approval",
        inputs=AgentRequest(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)

    server = _make_server(tmp_path)
    result = server.tools["agentsuite_marketing_get_status"](run_id)

    assert result.run_id == run_id
    assert result.agent == "marketing"
    assert result.stage == "approval"


def test_marketing_get_status_raises_on_missing_run(tmp_path: Path) -> None:
    """get_status must raise FileNotFoundError when no state file exists for run_id."""
    server = _make_server(tmp_path)
    with pytest.raises(FileNotFoundError):
        server.tools["agentsuite_marketing_get_status"]("nonexistent-run")


def test_marketing_list_runs_empty_when_no_runs(tmp_path: Path) -> None:
    """list_runs must return an empty list when no runs directory exists."""
    server = _make_server(tmp_path)
    assert server.tools["agentsuite_marketing_list_runs"]() == []


# ---------------------------------------------------------------------------
# UX-006 — marketing_list_runs filters by project_slug
# ---------------------------------------------------------------------------

def test_marketing_list_runs_filters_by_project_slug(tmp_path: Path) -> None:
    """marketing_list_runs(project_slug='x') must return only runs with project_slug == 'x'."""
    from agentsuite.agents.marketing.input_schema import MarketingAgentInput
    from agentsuite.kernel.schema import Cost

    def _make_run(run_id: str, project_slug: str | None) -> None:
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        inp = MarketingAgentInput(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request="test",
            brand_name="Brand",
            campaign_goal="goal",
            target_market="SMBs",
            project_slug=project_slug,
        )
        state = RunState(
            run_id=run_id,
            agent="marketing",
            stage="approval",
            inputs=inp,
            cost_so_far=Cost(),
        )
        StateStore(run_dir=run_dir).save(state)

    _make_run("m-slug-a", "slug-a")
    _make_run("m-slug-b", "slug-b")
    _make_run("m-no-slug", None)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: None,
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    runs = server.tools["agentsuite_marketing_list_runs"](project_slug="slug-a")
    assert len(runs) == 1, f"Expected 1, got {len(runs)}: {[r.run_id for r in runs]}"
    assert runs[0].run_id == "m-slug-a"

    runs = server.tools["agentsuite_marketing_list_runs"](project_slug="slug-b")
    assert len(runs) == 1
    assert runs[0].run_id == "m-slug-b"

    runs = server.tools["agentsuite_marketing_list_runs"](project_slug=None)
    assert len(runs) == 3


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
