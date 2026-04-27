"""Unit tests for DesignAgent end-to-end (mocked LLM)."""
from __future__ import annotations

import json

from agentsuite.agents.design.agent import DesignAgent
from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.rubric import DESIGN_RUBRIC
from agentsuite.agents.design.stages.spec import SPEC_ARTIFACTS
from agentsuite.agents.design.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "audience_profile": {"primary_persona": "senior designer"},
    "brand_voice": {"tone_words": ["confident", "clean"], "writing_style": "terse", "forbidden_tones": []},
    "visual_signals": ["bold typography"],
    "typography_signals": {"heading_style": "sans-serif"},
    "color_palette_observed": [],
    "craft_anti_patterns": ["stock photography"],
    "gaps": [],
}


def _all_responses() -> dict[str, str]:
    responses: dict[str, str] = {
        "extracting": json.dumps(_EXTRACTED),
        "checking 9 artifacts": json.dumps({"mismatches": []}),
        "scoring 9 design-agent": json.dumps({
            "scores": {d.name: 8.0 for d in DESIGN_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\n\nContent."
    return responses


def _request() -> DesignAgentInput:
    return DesignAgentInput(
        agent_name="design",
        role_domain="marketing",
        user_request="create a social media campaign",
        target_audience="developers",
        campaign_goal="drive signups for new product launch",
        channel="social",
        project_slug="acme-launch",
    )


def test_design_agent_run_to_approval(tmp_path):
    agent = DesignAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    state = agent.run(request=_request(), run_id="r1")
    assert state.stage == "approval"


def test_design_agent_produces_nine_spec_artifacts(tmp_path):
    agent = DesignAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    agent.run(request=_request(), run_id="r1")
    run_dir = tmp_path / "runs" / "r1"
    for stem in SPEC_ARTIFACTS:
        assert (run_dir / f"{stem}.md").exists(), f"Missing {stem}.md"


def test_design_agent_produces_eight_brief_templates(tmp_path):
    agent = DesignAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    agent.run(request=_request(), run_id="r1")
    run_dir = tmp_path / "runs" / "r1"
    for name in TEMPLATE_NAMES:
        assert (run_dir / "brief-template-library" / f"{name}.md").exists(), f"Missing {name}.md"


def test_design_agent_produces_qa_report(tmp_path):
    agent = DesignAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    agent.run(request=_request(), run_id="r1")
    run_dir = tmp_path / "runs" / "r1"
    assert (run_dir / "qa_report.md").exists()
    assert (run_dir / "qa_scores.json").exists()


def test_design_agent_cost_tracked(tmp_path):
    agent = DesignAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    state = agent.run(request=_request(), run_id="r1")
    assert state.cost_so_far.input_tokens > 0
