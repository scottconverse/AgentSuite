"""End-to-end Product pipeline integration test (mock LLM)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentsuite.agents.product.agent import ProductAgent
from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.stages.spec import SPEC_ARTIFACTS
from agentsuite.agents.product.template_loader import TEMPLATE_NAMES
from agentsuite.llm.mock import _default_mock_for_cli


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_product_pipeline_full_run(tmp_path: Path) -> None:
    """Full Product pipeline integration test against MockLLMProvider."""
    agent = ProductAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = ProductAgentInput(
        user_request="integration test product spec",
        agent_name="product",
        role_domain="product-ops",
        product_name="IntegrationApp",
        target_users="QA engineers",
        core_problem="too much manual testing",
    )
    state = agent.run(request=inp, run_id="integration-p1")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-p1"
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
    # Content assertion: primary artifact must contain product-domain keywords
    prd = run_dir / "product-requirements-doc.md"
    prd_text = prd.read_text()
    assert "product" in prd_text.lower() or "requirements" in prd_text.lower(), (
        "product-requirements-doc.md does not contain expected product content"
    )


def test_product_pipeline_approval_promotion(tmp_path: Path) -> None:
    """Full pipeline + approval: verifies kernel promotion works for ProductAgent."""
    agent = ProductAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = ProductAgentInput(
        user_request="integration test product spec",
        agent_name="product",
        role_domain="product-ops",
        product_name="IntegrationApp",
        target_users="QA engineers",
        core_problem="too much manual testing",
    )
    agent.run(request=inp, run_id="integration-p2")
    agent.approve(run_id="integration-p2", approver="test", project_slug="integrationapp")
    kernel = tmp_path / "_kernel" / "integrationapp"
    assert (kernel / "product-requirements-doc.md").exists(), (
        "missing promoted artifact _kernel/integrationapp/product-requirements-doc.md"
    )


def test_product_pipeline_resume_from_spec(tmp_path: Path) -> None:
    """Verify pipeline can be resumed from spec stage (simulating mid-run restart).

    The resume edits dict carries the original typed input so the kernel's
    _wrap handler can re-validate without losing ProductAgentInput-specific
    fields (product_name, target_users, core_problem) that are dropped when
    RunState serialises inputs as the base AgentRequest type.
    """
    agent = ProductAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = ProductAgentInput(
        user_request="integration test product spec",
        agent_name="product",
        role_domain="product-ops",
        product_name="IntegrationApp",
        target_users="QA engineers",
        core_problem="too much manual testing",
    )
    # Run to completion first
    state = agent.run(request=inp, run_id="integration-p3")
    assert state.stage == "approval"
    # Resume from spec — pass typed input via edits so _wrap can re-validate
    state2 = agent.resume(run_id="integration-p3", stage="spec", edits={"inputs": inp})
    assert state2.stage == "approval"
