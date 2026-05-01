"""End-to-end Marketing pipeline integration test (mock LLM)."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.marketing.agent import MarketingAgent
from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.stages.spec import SPEC_ARTIFACTS
from agentsuite.agents.marketing.template_loader import TEMPLATE_NAMES
from agentsuite.llm.mock import MockLLMProvider, _default_mock_for_cli


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
    # Content assertion: primary artifact must contain marketing-domain keywords
    brief = run_dir / "campaign-brief.md"
    brief_text = brief.read_text()
    assert "campaign" in brief_text.lower() or "brief" in brief_text.lower(), (
        "campaign-brief.md does not contain expected marketing content"
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


def test_marketing_extract_parse_error_fallback(tmp_path: Path) -> None:
    """When extract returns invalid JSON, pipeline uses fallback dict with parse_error key."""
    base = _default_mock_for_cli()
    # Override the extract response to return invalid JSON.
    # Remove the generic "extracting" key so it doesn't shadow the specific marketing extract key.
    patched_responses = {k: v for k, v in base.responses.items() if k != "extracting"}
    extract_key = "You are extracting structured marketing context from brand and competitor documents. Return ONLY valid JSON."
    patched_responses[extract_key] = "NOT VALID JSON %%% {"
    llm = MockLLMProvider(responses=patched_responses)

    agent = MarketingAgent(output_root=tmp_path, llm=llm)
    inp = MarketingAgentInput(
        user_request="integration test marketing campaign",
        brand_name="TestBrand",
        campaign_goal="Drive signups",
        target_market="SMBs",
        agent_name="marketing",
        role_domain="marketing-ops",
    )
    state = agent.run(request=inp, run_id="integration-m-parse-err")
    # Fallback allows pipeline to continue to approval
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-m-parse-err"
    extracted_path = run_dir / "extracted_context.json"
    assert extracted_path.exists(), "missing extracted_context.json"
    extracted = json.loads(extracted_path.read_text())
    assert "parse_error" in extracted, (
        "extracted_context.json should contain 'parse_error' key when JSON parsing fails"
    )


def test_marketing_consistency_check_failure_raises(tmp_path: Path) -> None:
    """Critical consistency finding is non-fatal; pipeline continues and report records it."""
    base = _default_mock_for_cli()
    patched_responses = dict(base.responses)
    consistency_key = "You are checking 9 marketing-agent artifacts for consistency. Return ONLY JSON."
    patched_responses[consistency_key] = json.dumps({
        "mismatches": [
            {
                "dimension": "audience_consistency",
                "severity": "critical",
                "detail": "Target audience conflicts between campaign brief and messaging framework",
            }
        ]
    })
    llm = MockLLMProvider(responses=patched_responses)

    agent = MarketingAgent(output_root=tmp_path, llm=llm)
    inp = MarketingAgentInput(
        user_request="integration test marketing campaign",
        brand_name="TestBrand",
        campaign_goal="Drive signups",
        target_market="SMBs",
        agent_name="marketing",
        role_domain="marketing-ops",
    )
    state = agent.run(request=inp, run_id="integration-m-consistency-fail")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-m-consistency-fail"
    report = json.loads((run_dir / "consistency_report.json").read_text())
    assert any(m.get("severity") == "critical" for m in report.get("mismatches", []))
