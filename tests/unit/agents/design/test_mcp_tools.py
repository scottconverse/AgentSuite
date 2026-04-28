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
