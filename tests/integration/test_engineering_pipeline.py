"""End-to-end Engineering pipeline integration test (mock LLM)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentsuite.agents.engineering.agent import EngineeringAgent
from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.stages.spec import SPEC_ARTIFACTS
from agentsuite.agents.engineering.template_loader import TEMPLATE_NAMES
from agentsuite.llm.mock import _default_mock_for_cli


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_engineering_pipeline_full_run(tmp_path: Path) -> None:
    """Full Engineering pipeline integration test against MockLLMProvider."""
    agent = EngineeringAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = EngineeringAgentInput(
        user_request="integration test engineering spec",
        agent_name="engineering",
        role_domain="engineering-ops",
        system_name="TestSystem",
        problem_domain="Web API",
        tech_stack="Python FastAPI",
        scale_requirements="1k RPS",
    )
    state = agent.run(request=inp, run_id="integration-e1")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-e1"
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


def test_engineering_pipeline_approval_promotion(tmp_path: Path) -> None:
    """Full pipeline + approval: verifies kernel promotion works for EngineeringAgent."""
    agent = EngineeringAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = EngineeringAgentInput(
        user_request="integration test engineering spec",
        agent_name="engineering",
        role_domain="engineering-ops",
        system_name="TestSystem",
        problem_domain="Web API",
        tech_stack="Python FastAPI",
        scale_requirements="1k RPS",
    )
    agent.run(request=inp, run_id="integration-e2")
    agent.approve(run_id="integration-e2", approver="test", project_slug="testsystem")
    kernel = tmp_path / "_kernel" / "testsystem"
    assert (kernel / "architecture-decision-record.md").exists(), (
        "missing promoted artifact _kernel/testsystem/architecture-decision-record.md"
    )


def test_engineering_pipeline_resume_from_spec(tmp_path: Path) -> None:
    """Verify pipeline can be resumed from spec stage (simulating mid-run restart).

    The resume edits dict carries the original typed input so the kernel's
    _wrap handler can re-validate without losing EngineeringAgentInput-specific
    fields (system_name, problem_domain, tech_stack, scale_requirements) that
    are dropped when RunState serialises inputs as the base AgentRequest type.
    """
    agent = EngineeringAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = EngineeringAgentInput(
        user_request="integration test engineering spec",
        agent_name="engineering",
        role_domain="engineering-ops",
        system_name="TestSystem",
        problem_domain="Web API",
        tech_stack="Python FastAPI",
        scale_requirements="1k RPS",
    )
    # Run to completion first
    state = agent.run(request=inp, run_id="integration-e3")
    assert state.stage == "approval"
    # Resume from spec — pass typed input via edits so _wrap can re-validate
    state2 = agent.resume(run_id="integration-e3", stage="spec", edits={"inputs": inp})
    assert state2.stage == "approval"
