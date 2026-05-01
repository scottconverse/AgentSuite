"""Unit tests for design.mcp_tools."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.design.agent import DesignAgent
from agentsuite.agents.design.mcp_tools import DesignRunRequest, register_tools
from agentsuite.agents.design.rubric import DESIGN_RUBRIC
from agentsuite.agents.design.stages.spec import SPEC_ARTIFACTS
from agentsuite.llm.mock import MockLLMProvider


def _all_responses() -> dict[str, str]:
    extracted = {
        "audience_profile": {"primary_persona": "senior designer"},
        "brand_voice": {"tone_words": ["confident"], "writing_style": "terse", "forbidden_tones": []},
        "visual_signals": ["bold typography"],
        "typography_signals": {"heading_style": "sans-serif"},
        "color_palette_observed": [],
        "craft_anti_patterns": [],
        "gaps": [],
    }
    responses = {
        "extracting": json.dumps(extracted),
        "checking 9 artifacts": json.dumps({"mismatches": []}),
        "scoring 9 design-agent": json.dumps({
            "scores": {d.name: 8.0 for d in DESIGN_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\nContent."
    return responses


class _StubServer:
    def __init__(self) -> None:
        self.tools: dict = {}

    def add_tool(self, name: str, fn) -> None:
        self.tools[name] = fn

    def tool_names(self) -> list[str]:
        return list(self.tools.keys())


def _agent_factory(tmp_path: Path) -> DesignAgent:
    return DesignAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))


def test_register_tools_adds_five_default_tools(tmp_path: Path) -> None:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    for name in ["agentsuite_design_run", "agentsuite_design_resume", "agentsuite_design_approve", "agentsuite_design_get_status", "agentsuite_design_list_runs"]:
        assert name in server.tool_names()


def test_register_tools_expose_stages_adds_ten_tools(tmp_path: Path) -> None:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=True,
    )
    assert len(server.tools) == 10
    for name in ["agentsuite_design_stage_intake", "agentsuite_design_stage_extract", "agentsuite_design_stage_spec", "agentsuite_design_stage_execute", "agentsuite_design_stage_qa"]:
        assert name in server.tool_names()


def test_design_run_returns_awaiting_approval(tmp_path: Path) -> None:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    request = DesignRunRequest(
        target_audience="developers",
        campaign_goal="drive signups",
        channel="web",
        run_id="mcp-r1",
    )
    result = server.tools["agentsuite_design_run"](request)
    assert result.status == "awaiting_approval"
    assert result.run_id == "mcp-r1"


def test_design_list_runs_empty_when_no_runs(tmp_path: Path) -> None:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    runs = server.tools["agentsuite_design_list_runs"]()
    assert runs == []


def test_design_get_status_raises_on_missing_run(tmp_path: Path) -> None:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    with pytest.raises(FileNotFoundError):
        server.tools["agentsuite_design_get_status"]("nonexistent-run")


# ---------------------------------------------------------------------------
# TEST-004 — design_approve returns structured dict on RevisionRequired
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# UX-006 — design_list_runs filters by project_slug
# ---------------------------------------------------------------------------

def test_design_list_runs_filters_by_project_slug(tmp_path: Path) -> None:
    """design_list_runs(project_slug='x') must return only runs with project_slug == 'x'."""
    from agentsuite.agents.design.input_schema import DesignAgentInput
    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.state_store import StateStore

    def _make_run(run_id: str, project_slug: str | None) -> None:
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        inp = DesignAgentInput(
            agent_name="design",
            role_domain="design-ops",
            user_request="test",
            target_audience="devs",
            campaign_goal="test goal",
            project_slug=project_slug,
        )
        state = RunState(
            run_id=run_id,
            agent="design",
            stage="approval",
            inputs=inp,
            cost_so_far=Cost(),
        )
        StateStore(run_dir=run_dir).save(state)

    _make_run("d-slug-a", "slug-a")
    _make_run("d-slug-b", "slug-b")
    _make_run("d-no-slug", None)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    # Filter by slug-a
    runs = server.tools["agentsuite_design_list_runs"](project_slug="slug-a")
    assert len(runs) == 1, f"Expected 1, got {len(runs)}: {[r.run_id for r in runs]}"
    assert runs[0].run_id == "d-slug-a"

    # Filter by slug-b
    runs = server.tools["agentsuite_design_list_runs"](project_slug="slug-b")
    assert len(runs) == 1
    assert runs[0].run_id == "d-slug-b"

    # No filter — all 3
    runs = server.tools["agentsuite_design_list_runs"](project_slug=None)
    assert len(runs) == 3


def test_design_approve_revision_required_returns_structured_error(tmp_path: Path) -> None:
    """design_approve must return a structured error dict (not raise) on RevisionRequired."""
    from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
    from agentsuite.kernel.state_store import StateStore

    run_dir = tmp_path / "runs" / "r-des-rev"
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id="r-des-rev",
        agent="design",
        stage="approval",
        requires_revision=True,
        inputs=AgentRequest(
            agent_name="design",
            role_domain="design-ops",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: DesignAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses())),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    result = server.tools["agentsuite_design_approve"](
        run_id="r-des-rev", approver="scott", project_slug="proj"
    )
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert result["error"] == "revision_required"
    assert "qa_report_path" in result
    assert isinstance(result["qa_report_path"], str)
    assert "action" in result
    # Artifacts must NOT have been promoted
    assert not (tmp_path / "_kernel" / "proj").exists()
