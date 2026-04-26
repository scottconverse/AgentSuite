"""Unit tests for founder.mcp_tools."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.mcp_tools import (
    FounderRunRequest,
    register_tools,
)
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.schema import Constraints
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
    assert "founder_run" in server.tool_names()
    assert "founder_resume" in server.tool_names()
    assert "founder_approve" in server.tool_names()
    assert "founder_get_status" in server.tool_names()
    assert "founder_list_runs" in server.tool_names()


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
    result = server.tools["founder_run"](request)
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
    server.tools["founder_run"](request)
    approval = server.tools["founder_approve"](run_id="r1", approver="scott", project_slug="pfl")
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
    server.tools["founder_run"](request)
    runs = server.tools["founder_list_runs"](project_slug=None)
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
    server.tools["founder_run"](request)
    status = server.tools["founder_get_status"](run_id="r1")
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
    for stage_tool in ("founder_intake", "founder_extract", "founder_spec", "founder_execute", "founder_qa"):
        assert stage_tool in server.tool_names()
