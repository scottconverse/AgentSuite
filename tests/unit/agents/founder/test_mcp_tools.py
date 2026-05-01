"""Unit tests for founder.mcp_tools."""
import json
from pathlib import Path


from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.mcp_tools import (
    FounderRunRequest,
    register_tools,
)
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.llm.mock import MockLLMProvider


def _all_responses() -> dict[str, str]:
    extracted = {
        "mission": "x",
        "audience": {"primary_persona": "y", "secondary_personas": []},
        "positioning": "z",
        "tone_signals": ["practical"],
        "visual_signals": [],
        "recurring_claims": [],
        "recurring_vocabulary": [],
        "prohibited_language": [],
        "gaps": [],
    }
    responses = {
        "extracting": json.dumps(extracted),
        "checking 9 artifacts": json.dumps({"mismatches": []}),
        "scoring 9 founder": json.dumps({
            "scores": {d.name: 8.0 for d in FOUNDER_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\nContent."
    return responses


class _StubServer:
    def __init__(self) -> None:
        self.tools: dict[str, callable] = {}

    def add_tool(self, name: str, fn) -> None:
        self.tools[name] = fn

    def tool_names(self) -> list[str]:
        return list(self.tools.keys())


def _agent_factory(tmp_path: Path) -> FounderAgent:
    return FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))


def test_register_tools_adds_five_default_tools(tmp_path):
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    assert "agentsuite_founder_run" in server.tool_names()
    assert "agentsuite_founder_resume" in server.tool_names()
    assert "agentsuite_founder_approve" in server.tool_names()
    assert "agentsuite_founder_get_status" in server.tool_names()
    assert "agentsuite_founder_list_runs" in server.tool_names()


def test_founder_run_returns_awaiting_approval(tmp_path):
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    request = FounderRunRequest(
        business_goal="Launch PFL",
        project_slug="pfl",
        run_id="r1",
    )
    result = server.tools["agentsuite_founder_run"](request)
    assert result.run_id == "r1"
    assert result.status == "awaiting_approval"
    assert result.primary_path.endswith("brand-system.md")


def test_founder_approve_returns_promoted_paths(tmp_path):
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    request = FounderRunRequest(business_goal="Launch PFL", project_slug="pfl", run_id="r1")
    server.tools["agentsuite_founder_run"](request)
    approval = server.tools["agentsuite_founder_approve"](run_id="r1", approver="scott", project_slug="pfl")
    assert approval.status == "done"
    assert any("brand-system.md" in p for p in approval.promoted_paths)


def test_founder_list_runs_returns_active_runs(tmp_path):
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    request = FounderRunRequest(business_goal="Launch PFL", project_slug="pfl", run_id="r1")
    server.tools["agentsuite_founder_run"](request)
    runs = server.tools["agentsuite_founder_list_runs"](project_slug=None)
    assert len(runs) == 1
    assert runs[0].run_id == "r1"


def test_founder_get_status_returns_state(tmp_path):
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    request = FounderRunRequest(business_goal="Launch PFL", project_slug="pfl", run_id="r1")
    server.tools["agentsuite_founder_run"](request)
    status = server.tools["agentsuite_founder_get_status"](run_id="r1")
    assert status.run_id == "r1"
    assert status.stage == "approval"


def test_advanced_stage_tools_added_when_expose_set(tmp_path):
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=True,
    )
    for stage_tool in ("agentsuite_founder_stage_intake", "agentsuite_founder_stage_extract", "agentsuite_founder_stage_spec", "agentsuite_founder_stage_execute", "agentsuite_founder_stage_qa"):
        assert stage_tool in server.tool_names()


# ---------------------------------------------------------------------------
# UX-002 — founder_approve returns structured dict on RevisionRequired
# ---------------------------------------------------------------------------

def test_founder_approve_revision_required_returns_structured_error(tmp_path):
    """founder_approve must return a structured error dict (not raise) on RevisionRequired."""
    from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
    from agentsuite.kernel.state_store import StateStore

    # Set up a run that is at approval stage but requires revision
    run_dir = tmp_path / "runs" / "r-rev"
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id="r-rev",
        agent="founder",
        stage="approval",
        requires_revision=True,
        inputs=AgentRequest(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses())),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    result = server.tools["agentsuite_founder_approve"](
        run_id="r-rev", approver="scott", project_slug="pfl"
    )
    assert isinstance(result, dict)
    assert result["error"] == "revision_required"
    assert "qa_report_path" in result
    assert "qa_report.md" in result["qa_report_path"]
    assert "action" in result
    # Artifacts must NOT have been promoted
    assert not (tmp_path / "_kernel" / "pfl").exists()


# ---------------------------------------------------------------------------
# TEST-002 — RevisionRequired edge cases on founder approve
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# UX-006 — founder_list_runs filters by project_slug
# ---------------------------------------------------------------------------

def test_founder_list_runs_filters_by_project_slug(tmp_path):
    """founder_list_runs(project_slug='x') must return only runs with project_slug == 'x'."""
    from agentsuite.agents.founder.input_schema import FounderAgentInput
    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.state_store import StateStore

    def _make_run(run_id: str, project_slug: str | None) -> None:
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        inp = FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="test",
            business_goal="test",
            project_slug=project_slug,
        )
        state = RunState(
            run_id=run_id,
            agent="founder",
            stage="approval",
            inputs=inp,
            cost_so_far=Cost(),
        )
        StateStore(run_dir=run_dir).save(state)

    _make_run("r-slug-a", "slug-a")
    _make_run("r-slug-b", "slug-b")
    _make_run("r-no-slug", None)

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: _agent_factory(tmp_path),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    # Filter by slug-a — must return only r-slug-a
    runs = server.tools["agentsuite_founder_list_runs"](project_slug="slug-a")
    assert len(runs) == 1, f"Expected 1 run for slug-a, got {len(runs)}: {[r.run_id for r in runs]}"
    assert runs[0].run_id == "r-slug-a"

    # Filter by slug-b — must return only r-slug-b
    runs = server.tools["agentsuite_founder_list_runs"](project_slug="slug-b")
    assert len(runs) == 1
    assert runs[0].run_id == "r-slug-b"

    # No filter — must return all 3 runs
    runs = server.tools["agentsuite_founder_list_runs"](project_slug=None)
    assert len(runs) == 3


def test_founder_approve_revision_required_missing_qa_report_path(tmp_path):
    """founder_approve must still return a structured error dict even when qa_report.md is absent.

    The RevisionRequired handler should not raise; the qa_report_path value should be
    a string path (even if the file doesn't exist on disk yet).
    """
    from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
    from agentsuite.kernel.state_store import StateStore

    # Create a revision-required state without writing qa_report.md to disk
    run_dir = tmp_path / "runs" / "r-no-qa"
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id="r-no-qa",
        agent="founder",
        stage="approval",
        requires_revision=True,
        inputs=AgentRequest(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)
    # Explicitly confirm qa_report.md is NOT on disk
    assert not (run_dir / "qa_report.md").exists()

    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses())),
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    # Must return a dict, not raise
    result = server.tools["agentsuite_founder_approve"](
        run_id="r-no-qa", approver="scott", project_slug="pfl"
    )
    assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result!r}"
    assert result.get("error") == "revision_required"
    # qa_report_path must be a string (even though the file doesn't exist yet)
    assert isinstance(result.get("qa_report_path"), str)
    assert "action" in result
