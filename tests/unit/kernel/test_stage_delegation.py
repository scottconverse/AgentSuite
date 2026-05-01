"""TEST-S2-001: Verify all 14 agent stage wrappers correctly delegate to kernel counterparts.

Each agent has two stage wrappers:
  - stages/spec.py  → calls kernel_spec_stage(_SPEC_CONFIG, state, ctx)
  - stages/qa.py    → calls kernel_qa_stage(_QA_CONFIG, state, ctx)

These tests patch the kernel function at its import site inside each wrapper module
and assert:
  1. The kernel function was called exactly once.
  2. The first positional argument is the correct config type.
  3. Key config fields are populated (rubric/system_msg for QA, spec_artifacts for spec).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
from agentsuite.kernel.stages.qa import QAStageConfig
from agentsuite.kernel.stages.spec import SpecStageConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_state(agent: str) -> RunState:
    """Return the smallest valid RunState for patched delegation tests.

    Because kernel_spec_stage / kernel_qa_stage are patched to a MagicMock,
    the state is never actually read by the kernel — any RunState is fine.
    """
    req = AgentRequest(
        agent_name=agent,
        role_domain="test",
        user_request="delegation test",
        constraints=Constraints(),
    )
    return RunState(run_id="test-run", agent=agent, stage="spec", inputs=req)


def _minimal_ctx() -> StageContext:
    """Return a StageContext with a mock writer (never used when kernel is patched)."""
    writer = MagicMock()
    writer.run_dir = MagicMock()
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": MagicMock()})


# ---------------------------------------------------------------------------
# Founder — spec
# ---------------------------------------------------------------------------

def test_founder_spec_delegates_to_kernel():
    state = _minimal_state("founder")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.founder.stages.spec.kernel_spec_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.founder.stages.spec import spec_stage
        spec_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, SpecStageConfig)
    assert len(config.spec_artifacts) == 9
    assert "brand-system" in config.spec_artifacts


# ---------------------------------------------------------------------------
# Founder — qa
# ---------------------------------------------------------------------------

def test_founder_qa_delegates_to_kernel():
    state = _minimal_state("founder")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.founder.stages.qa.kernel_qa_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.founder.stages.qa import qa_stage
        qa_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, QAStageConfig)
    assert config.rubric is not None
    assert "founder" in config.system_msg.lower()
    assert config.spec_artifacts is not None and len(config.spec_artifacts) > 0


# ---------------------------------------------------------------------------
# Design — spec
# ---------------------------------------------------------------------------

def test_design_spec_delegates_to_kernel():
    state = _minimal_state("design")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.design.stages.spec.kernel_spec_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.design.stages.spec import spec_stage
        spec_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, SpecStageConfig)
    assert len(config.spec_artifacts) == 9
    assert "visual-direction" in config.spec_artifacts


# ---------------------------------------------------------------------------
# Design — qa
# ---------------------------------------------------------------------------

def test_design_qa_delegates_to_kernel():
    state = _minimal_state("design")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.design.stages.qa.kernel_qa_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.design.stages.qa import qa_stage
        qa_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, QAStageConfig)
    assert config.rubric is not None
    assert "design" in config.system_msg.lower()
    assert config.spec_artifacts is not None and len(config.spec_artifacts) > 0


# ---------------------------------------------------------------------------
# Engineering — spec
# ---------------------------------------------------------------------------

def test_engineering_spec_delegates_to_kernel():
    state = _minimal_state("engineering")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.engineering.stages.spec.kernel_spec_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.engineering.stages.spec import spec_stage
        spec_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, SpecStageConfig)
    assert len(config.spec_artifacts) == 9
    assert "architecture-decision-record" in config.spec_artifacts


# ---------------------------------------------------------------------------
# Engineering — qa
# ---------------------------------------------------------------------------

def test_engineering_qa_delegates_to_kernel():
    state = _minimal_state("engineering")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.engineering.stages.qa.kernel_qa_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.engineering.stages.qa import qa_stage
        qa_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, QAStageConfig)
    assert config.rubric is not None
    assert "engineering" in config.system_msg.lower()
    assert config.spec_artifacts is not None and len(config.spec_artifacts) > 0


# ---------------------------------------------------------------------------
# CIO — spec
# ---------------------------------------------------------------------------

def test_cio_spec_delegates_to_kernel():
    state = _minimal_state("cio")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.cio.stages.spec.kernel_spec_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.cio.stages.spec import spec_stage
        spec_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, SpecStageConfig)
    assert len(config.spec_artifacts) == 9
    assert "it-strategy" in config.spec_artifacts


# ---------------------------------------------------------------------------
# CIO — qa
# ---------------------------------------------------------------------------

def test_cio_qa_delegates_to_kernel():
    state = _minimal_state("cio")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.cio.stages.qa.kernel_qa_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.cio.stages.qa import qa_stage
        qa_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, QAStageConfig)
    assert config.rubric is not None
    assert "cio" in config.system_msg.lower()
    assert config.spec_artifacts is not None and len(config.spec_artifacts) > 0


# ---------------------------------------------------------------------------
# Marketing — spec
# ---------------------------------------------------------------------------

def test_marketing_spec_delegates_to_kernel():
    state = _minimal_state("marketing")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.marketing.stages.spec.kernel_spec_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.marketing.stages.spec import spec_stage
        spec_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, SpecStageConfig)
    assert len(config.spec_artifacts) == 9
    assert "campaign-brief" in config.spec_artifacts


# ---------------------------------------------------------------------------
# Marketing — qa
# ---------------------------------------------------------------------------

def test_marketing_qa_delegates_to_kernel():
    state = _minimal_state("marketing")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.marketing.stages.qa.kernel_qa_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.marketing.stages.qa import qa_stage
        qa_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, QAStageConfig)
    assert config.rubric is not None
    assert "marketing" in config.system_msg.lower()
    assert config.spec_artifacts is not None and len(config.spec_artifacts) > 0


# ---------------------------------------------------------------------------
# Product — spec
# ---------------------------------------------------------------------------

def test_product_spec_delegates_to_kernel():
    state = _minimal_state("product")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.product.stages.spec.kernel_spec_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.product.stages.spec import spec_stage
        spec_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, SpecStageConfig)
    assert len(config.spec_artifacts) == 9
    assert "product-requirements-doc" in config.spec_artifacts


# ---------------------------------------------------------------------------
# Product — qa
# ---------------------------------------------------------------------------

def test_product_qa_delegates_to_kernel():
    state = _minimal_state("product")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.product.stages.qa.kernel_qa_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.product.stages.qa import qa_stage
        qa_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, QAStageConfig)
    assert config.rubric is not None
    assert "product" in config.system_msg.lower()
    assert config.spec_artifacts is not None and len(config.spec_artifacts) > 0


# ---------------------------------------------------------------------------
# Trust & Risk — spec
# ---------------------------------------------------------------------------

def test_trust_risk_spec_delegates_to_kernel():
    state = _minimal_state("trust_risk")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.trust_risk.stages.spec.kernel_spec_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.trust_risk.stages.spec import spec_stage
        spec_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, SpecStageConfig)
    assert len(config.spec_artifacts) == 9
    assert "threat-model" in config.spec_artifacts


# ---------------------------------------------------------------------------
# Trust & Risk — qa
# ---------------------------------------------------------------------------

def test_trust_risk_qa_delegates_to_kernel():
    state = _minimal_state("trust_risk")
    ctx = _minimal_ctx()
    target = "agentsuite.agents.trust_risk.stages.qa.kernel_qa_stage"
    with patch(target) as mock_kernel:
        mock_kernel.return_value = state
        from agentsuite.agents.trust_risk.stages.qa import qa_stage
        qa_stage(state, ctx)

    mock_kernel.assert_called_once()
    config = mock_kernel.call_args[0][0]
    assert isinstance(config, QAStageConfig)
    assert config.rubric is not None
    assert "trust" in config.system_msg.lower()
    assert config.spec_artifacts is not None and len(config.spec_artifacts) > 0
