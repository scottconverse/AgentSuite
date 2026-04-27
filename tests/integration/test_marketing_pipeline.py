"""End-to-end Marketing pipeline integration test (mock LLM)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentsuite.agents.marketing.agent import MarketingAgent
from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.stages.spec import SPEC_ARTIFACTS
from agentsuite.agents.marketing.template_loader import TEMPLATE_NAMES
from agentsuite.llm.mock import _default_mock_for_cli


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_marketing_pipeline_full_run(tmp_path: Path) -> None:
    """Full Marketing pipeline integration test against MockLLMProvider."""
    agent = MarketingAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = MarketingAgentInput(
        user_request="integration test marketing campaign",
        brand_name="TestBrand",
        campaign_goal="Drive signups",
        target_market="SMBs",
        agent_name="marketing",
        role_domain="marketing-ops",
    )
    state = agent.run(request=inp, run_id="integration-m1")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-m1"
    # All 9 spec artifacts (.md files)
    for stem in SPEC_ARTIFACTS:
        assert (run_dir / f"{stem}.md").exists(), f"missing spec artifact {stem}.md"
    # qa_scores.json
    assert (run_dir / "qa_scores.json").exists(), "missing qa_scores.json"
    # inputs_manifest.json
    assert (run_dir / "inputs_manifest.json").exists(), "missing inputs_manifest.json"
    # brief-template-library/ with 8 templates
    for name in TEMPLATE_NAMES:
        assert (run_dir / "brief-template-library" / f"{name}.md").exists(), (
            f"missing template brief-template-library/{name}.md"
        )


def test_marketing_pipeline_approval_promotion(tmp_path: Path) -> None:
    """Full pipeline + approval: verifies kernel promotion works for MarketingAgent."""
    agent = MarketingAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = MarketingAgentInput(
        user_request="integration test marketing campaign",
        brand_name="TestBrand",
        campaign_goal="Drive signups",
        target_market="SMBs",
        agent_name="marketing",
        role_domain="marketing-ops",
    )
    agent.run(request=inp, run_id="integration-m2")
    agent.approve(run_id="integration-m2", approver="test", project_slug="testbrand")
    kernel = tmp_path / "_kernel" / "testbrand"
    assert (kernel / "campaign-brief.md").exists(), (
        "missing promoted artifact _kernel/testbrand/campaign-brief.md"
    )


def test_marketing_pipeline_resume_from_spec(tmp_path: Path) -> None:
    """Verify pipeline can be resumed from spec stage (simulating mid-run restart).

    The resume edits dict carries the original typed input so the kernel's
    _wrap handler can re-validate without losing MarketingAgentInput-specific
    fields (brand_name, campaign_goal, target_market) that are dropped when
    RunState serialises inputs as the base AgentRequest type.
    """
    agent = MarketingAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = MarketingAgentInput(
        user_request="integration test marketing campaign",
        brand_name="TestBrand",
        campaign_goal="Drive signups",
        target_market="SMBs",
        agent_name="marketing",
        role_domain="marketing-ops",
    )
    # Run to completion first
    state = agent.run(request=inp, run_id="integration-m3")
    assert state.stage == "approval"
    # Resume from spec — pass typed input via edits so _wrap can re-validate
    state2 = agent.resume(run_id="integration-m3", stage="spec", edits={"inputs": inp})
    assert state2.stage == "approval"
