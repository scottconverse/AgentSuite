"""End-to-end Design pipeline integration test (mock LLM)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agentsuite.agents.design.agent import DesignAgent
from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.stages.spec import SPEC_ARTIFACTS, ConsistencyCheckFailed
from agentsuite.agents.design.template_loader import TEMPLATE_NAMES
from agentsuite.llm.mock import MockLLMProvider, _default_mock_for_cli


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_design_full_pipeline_with_mock_provider(tmp_path: Path) -> None:
    """Full Design pipeline integration test against MockLLMProvider."""
    agent = DesignAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="design-ops",
        user_request="create social campaign design artifacts",
        target_audience="developers and tech-savvy early adopters",
        campaign_goal="drive signups for Acme product launch",
        channel="social",
        project_slug="acme-social",
    )
    state = agent.run(request=inp, run_id="integration-d1")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-d1"
    expected = (
        ["_state.json", "inputs_manifest.json", "extracted_context.json",
         "consistency_report.json", "export-manifest-template.json",
         "qa_report.md", "qa_scores.json"]
        + [f"{s}.md" for s in SPEC_ARTIFACTS]
        + [f"brief-template-library/{t}.md" for t in TEMPLATE_NAMES]
    )
    for name in expected:
        assert (run_dir / name).exists(), f"missing artifact {name}"


def test_design_pipeline_emits_promoted_kernel_after_approval(tmp_path: Path) -> None:
    """Full pipeline + approval: verifies kernel promotion works for DesignAgent."""
    agent = DesignAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="design-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="launch",
        channel="web",
        project_slug="acme",
    )
    agent.run(request=inp, run_id="int-d2")
    agent.approve(run_id="int-d2", approver="scott", project_slug="acme")
    kernel = tmp_path / "_kernel" / "acme"
    assert (kernel / "visual-direction.md").exists()


def test_design_consistency_check_failure_raises(tmp_path: Path) -> None:
    """When consistency check returns a critical finding, ConsistencyCheckFailed is raised."""
    base = _default_mock_for_cli()
    # Remove the existing "checking 9 artifacts" key so our critical override takes effect.
    # Design spec.py system prompt contains "checking 9 artifacts for design consistency".
    patched_responses = {k: v for k, v in base.responses.items() if k != "checking 9 artifacts"}
    critical_response = json.dumps({
        "mismatches": [
            {
                "dimension": "brand_voice_consistency",
                "severity": "critical",
                "detail": "Visual direction contradicts design-brief color palette",
            }
        ]
    })
    patched_responses["checking 9 artifacts for design consistency"] = critical_response
    llm = MockLLMProvider(responses=patched_responses)

    agent = DesignAgent(output_root=tmp_path, llm=llm)
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="design-ops",
        user_request="test consistency failure",
        target_audience="developers",
        campaign_goal="launch",
        channel="web",
    )
    with pytest.raises(ConsistencyCheckFailed):
        agent.run(request=inp, run_id="design-consistency-fail")


def test_design_pipeline_resume_from_spec(tmp_path: Path) -> None:
    """Verify pipeline can be resumed from spec stage (simulating mid-run restart).

    The resume edits dict carries the original typed input so the kernel's
    _wrap handler can re-validate without losing DesignAgentInput-specific
    fields (campaign_goal, target_audience) that are dropped when RunState
    serialises inputs as the base AgentRequest type.
    """
    agent = DesignAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="design-ops",
        user_request="x",
        target_audience="devs",
        campaign_goal="launch",
        channel="web",
    )
    # Run to completion first
    state = agent.run(request=inp, run_id="int-d3")
    assert state.stage == "approval"
    # Resume from spec — pass typed input via edits so _wrap can re-validate
    state2 = agent.resume(run_id="int-d3", stage="spec", edits={"inputs": inp})
    assert state2.stage == "approval"
