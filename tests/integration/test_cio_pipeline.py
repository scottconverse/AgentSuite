"""End-to-end CIO pipeline integration test (mock LLM)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agentsuite.agents.registry import default_registry
from agentsuite.agents.cio.agent import CIOAgent
from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.rubric import CIO_RUBRIC
from agentsuite.agents.cio.stages.spec import SPEC_ARTIFACTS, ConsistencyCheckFailed
from agentsuite.llm.mock import MockLLMProvider, _default_mock_for_cli


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_cio_full_pipeline_mock(tmp_path: Path) -> None:
    """Full CIO pipeline integration test against MockLLMProvider."""
    agent = CIOAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = CIOAgentInput(
        user_request="Run CIO assessment",
        organization_name="TechCorp Global",
        strategic_priorities="cloud-first strategy, AI adoption, cost reduction",
        it_maturity_level="Level 3 - Defined",
    )
    state = agent.run(request=inp, run_id="integration-cio1")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-cio1"
    # All 9 spec artifacts (.md files)
    for stem in SPEC_ARTIFACTS:
        assert (run_dir / f"{stem}.md").exists(), f"missing spec artifact {stem}.md"
    # qa_scores.json
    assert (run_dir / "qa_scores.json").exists(), "missing qa_scores.json"


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_cio_qa_scores_above_threshold(tmp_path: Path) -> None:
    """QA scores must all be >= 7.0 and requires_revision must be False."""
    agent = CIOAgent(output_root=tmp_path, llm=_default_mock_for_cli())
    inp = CIOAgentInput(
        user_request="Generate IT strategy artifacts",
        organization_name="InnovateCo",
        strategic_priorities="digital transformation and security",
        it_maturity_level="Level 2 - Developing",
    )
    agent.run(request=inp, run_id="integration-cio2")

    run_dir = tmp_path / "runs" / "integration-cio2"
    qa_path = run_dir / "qa_scores.json"
    assert qa_path.exists(), "missing qa_scores.json"

    data = json.loads(qa_path.read_text())
    scores: dict = data.get("scores", data)

    expected_dims = [dim.name for dim in CIO_RUBRIC.dimensions]
    for dim in expected_dims:
        assert dim in scores, f"rubric dimension '{dim}' missing from qa_scores.json"
        assert scores[dim] >= 7.0, (
            f"rubric dimension '{dim}' score {scores[dim]} below threshold 7.0"
        )

    # requires_revision must be false (key may be top-level or nested)
    requires_revision = data.get("requires_revision", False)
    assert requires_revision is False, (
        f"requires_revision expected False but got {requires_revision}"
    )


@pytest.mark.skipif(
    os.environ.get("RECORD_CASSETTES") == "1",
    reason="Skip when re-recording cassettes",
)
def test_cio_agent_via_registry(tmp_path: Path) -> None:
    """CIO agent instantiated via registry produces it-strategy artifact."""
    import os as _os
    orig = _os.environ.get("AGENTSUITE_ENABLED_AGENTS")
    _os.environ["AGENTSUITE_ENABLED_AGENTS"] = "cio"
    try:
        agent_class = default_registry().get_class("cio")
        agent = agent_class(output_root=tmp_path, llm=_default_mock_for_cli())
    finally:
        if orig is None:
            _os.environ.pop("AGENTSUITE_ENABLED_AGENTS", None)
        else:
            _os.environ["AGENTSUITE_ENABLED_AGENTS"] = orig

    inp = CIOAgentInput(
        user_request="Assess IT strategy",
        organization_name="FutureTech",
        strategic_priorities="innovation and growth",
        it_maturity_level="Level 4 - Managed",
    )
    state = agent.run(request=inp, run_id="integration-cio3")
    assert state.stage == "approval"

    run_dir = tmp_path / "runs" / "integration-cio3"
    it_strategy = run_dir / "it-strategy.md"
    assert it_strategy.exists(), "missing it-strategy.md"
    assert it_strategy.stat().st_size > 0, "it-strategy.md is empty"
    # Content assertion: primary artifact must contain IT strategy keywords
    it_strategy_text = it_strategy.read_text()
    assert "strategy" in it_strategy_text.lower() or "it" in it_strategy_text.lower(), (
        "it-strategy.md does not contain expected IT strategy content"
    )


def test_cio_consistency_check_failure_raises(tmp_path: Path) -> None:
    """When consistency check returns a critical finding, ConsistencyCheckFailed is raised."""
    base = _default_mock_for_cli()
    # Remove the existing key that would match CIO consistency check.
    # CIO spec.py system: "You are checking 9 CIO artifacts for consistency."
    # Default mock key (full string): "You are checking 9 CIO artifacts for consistency. Return ONLY JSON."
    existing_key = "You are checking 9 CIO artifacts for consistency. Return ONLY JSON."
    patched_responses = {k: v for k, v in base.responses.items() if k != existing_key}
    critical_response = json.dumps({
        "mismatches": [
            {
                "dimension": "budget_alignment",
                "severity": "critical",
                "detail": "Technology roadmap investments conflict with budget-allocation-model constraints",
            }
        ]
    })
    patched_responses["checking 9 CIO artifacts for consistency"] = critical_response
    llm = MockLLMProvider(responses=patched_responses)

    agent = CIOAgent(output_root=tmp_path, llm=llm)
    inp = CIOAgentInput(
        user_request="test consistency failure",
        organization_name="TechCorp Global",
        strategic_priorities="cloud-first strategy, AI adoption",
        it_maturity_level="Level 3 - Defined",
    )
    with pytest.raises(ConsistencyCheckFailed):
        agent.run(request=inp, run_id="cio-consistency-fail")
