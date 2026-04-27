"""End-to-end Founder pipeline integration test (mock LLM)."""
import json
import os
from pathlib import Path

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS, ConsistencyCheckFailed
from agentsuite.agents.founder.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.mock import MockLLMProvider, _default_mock_for_cli


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording — see Task 28 docs for the dedicated record path",
)
def test_founder_full_pipeline_with_mock_provider(tmp_path):
    """The integration test runs against MockLLMProvider — vcr cassettes are reserved
    for the future real-provider integration path. v0.1.0 ships mock-only integration
    plus the explicit live tier (Task 30) for real-LLM coverage."""
    agent = FounderAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="build full creative ops for PatentForgeLocal",
        business_goal="Launch PatentForgeLocal v1",
        project_slug="pfl",
        constraints=Constraints(),
    )
    state = agent.run(request=inp, run_id="integration-r1")
    assert state.stage == "approval"

    run_dir: Path = tmp_path / "runs" / "integration-r1"
    expected = (
        ["_state.json", "inputs_manifest.json", "extracted_context.json",
         "consistency_report.json", "export-manifest-template.json",
         "qa_report.md", "qa_scores.json"]
        + [f"{s}.md" for s in SPEC_ARTIFACTS]
        + [f"brief-template-library/{t}.md" for t in TEMPLATE_NAMES]
    )
    for name in expected:
        assert (run_dir / name).exists(), f"missing artifact {name}"


def test_founder_full_pipeline_emits_promoted_kernel_after_approval(tmp_path):
    agent = FounderAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="Launch PFL",
        project_slug="pfl",
        constraints=Constraints(),
    )
    agent.run(request=inp, run_id="r2")
    agent.approve(run_id="r2", approver="scott", project_slug="pfl")
    kernel = tmp_path / "_kernel" / "pfl"
    assert (kernel / "brand-system.md").exists()
    assert (kernel / "brief-template-library" / "landing-hero.md").exists()


def test_founder_consistency_check_failure_raises(tmp_path: Path) -> None:
    """When consistency check returns a critical finding, ConsistencyCheckFailed is raised."""
    base = _default_mock_for_cli()
    # Remove the existing key that would match the consistency check so our critical one takes effect.
    # Founder spec.py system prompt contains "checking 9 artifacts for cross-document consistency".
    # The default mock has "checking 9 artifacts" which would match — remove it and replace.
    patched_responses = {k: v for k, v in base.responses.items() if k != "checking 9 artifacts"}
    critical_response = json.dumps({
        "mismatches": [
            {
                "dimension": "tone_consistency",
                "severity": "critical",
                "detail": "Brand voice in brand-system conflicts with founder-voice-guide",
            }
        ]
    })
    # Key must be a substring of the system prompt used by founder spec_stage
    patched_responses["checking 9 artifacts for cross-document consistency"] = critical_response
    llm = MockLLMProvider(responses=patched_responses)

    agent = FounderAgent(output_root=tmp_path, llm=llm)
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="test consistency failure",
        business_goal="Launch PFL",
        project_slug="pfl",
        constraints=Constraints(),
    )
    with pytest.raises(ConsistencyCheckFailed):
        agent.run(request=inp, run_id="founder-consistency-fail")


def test_pipeline_hard_cap_exceeded_propagates(tmp_path):
    """HardCapExceeded propagates cleanly through BaseAgent._drive() and is not swallowed."""
    from unittest.mock import patch
    from agentsuite.kernel.cost import CostTracker, HardCapExceeded, Cost

    original_add = CostTracker.add
    call_count = {"n": 0}

    def _raise_on_second(self, cost: Cost) -> Cost:
        call_count["n"] += 1
        if call_count["n"] >= 2:
            raise HardCapExceeded("test cap exceeded")
        return original_add(self, cost)

    with patch.object(CostTracker, "add", _raise_on_second):
        agent = FounderAgent(output_root=tmp_path, llm=_default_mock_for_cli())
        inp = FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="cap test",
            business_goal="Test cap",
            project_slug="cap-test",
            constraints=Constraints(),
        )
        with pytest.raises(HardCapExceeded):
            agent.run(request=inp, run_id="cap-test-run")
