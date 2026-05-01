"""Unit tests for TrustRiskAgent — structure, registration, and _wrap behavior."""
from __future__ import annotations

from agentsuite.agents.trust_risk.agent import TrustRiskAgent
from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC
from agentsuite.llm.mock import MockLLMProvider


def _minimal_input() -> TrustRiskAgentInput:
    return TrustRiskAgentInput(
        user_request="Assess cloud infrastructure risk for AcmeCorp",
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        product_name="AcmeCorp Platform",
        risk_domain="cloud infra",
        stakeholder_context="Engineering leads, risk tolerance is moderate",
    )


def test_trust_risk_agent_name():
    assert TrustRiskAgent.name == "trust_risk"


def test_trust_risk_agent_rubric(tmp_path):
    agent = TrustRiskAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert agent.qa_rubric is TRUST_RISK_RUBRIC


def test_stage_handlers_keys(tmp_path):
    agent = TrustRiskAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert set(agent.stage_handlers().keys()) == {"intake", "extract", "spec", "execute", "qa"}


def test_stage_handlers_callables(tmp_path):
    agent = TrustRiskAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    for name, handler in agent.stage_handlers().items():
        assert callable(handler), f"Handler '{name}' is not callable"


def test_wrap_with_dict_input(tmp_path):
    """_wrap() with dict input constructs TrustRiskAgentInput correctly."""
    agent = TrustRiskAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))

    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.base_agent import StageContext
    from agentsuite.kernel.artifacts import ArtifactWriter
    from agentsuite.kernel.cost import CostTracker
    inp = _minimal_input()
    writer = ArtifactWriter(output_root=tmp_path, run_id="wrap-dict")
    tracker = CostTracker()

    # Simulate edits["inputs"] as a dict (resume path)
    dict_inputs = inp.model_dump()
    ctx = StageContext(writer=writer, cost_tracker=tracker, edits={"inputs": dict_inputs})

    state = RunState(
        run_id="wrap-dict",
        agent="trust_risk",
        stage="intake",
        inputs=inp,
        cost_so_far=Cost(),
    )

    # Patch the state inputs to base AgentRequest to trigger dict branch
    from agentsuite.kernel.schema import AgentRequest
    base_inp = AgentRequest(
        user_request=inp.user_request,
        agent_name=inp.agent_name,
        role_domain=inp.role_domain,
    )
    state = state.model_copy(update={"inputs": base_inp})

    handlers = agent.stage_handlers()
    # The _wrap function should reconstruct TrustRiskAgentInput from the dict
    next_state = handlers["intake"](state, ctx)
    assert isinstance(next_state.inputs, TrustRiskAgentInput)
    assert next_state.inputs.product_name == "AcmeCorp Platform"


def test_wrap_with_schema_input(tmp_path):
    """_wrap() with TrustRiskAgentInput instance passes through unchanged."""
    agent = TrustRiskAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))

    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.base_agent import StageContext
    from agentsuite.kernel.artifacts import ArtifactWriter
    from agentsuite.kernel.cost import CostTracker

    inp = _minimal_input()
    writer = ArtifactWriter(output_root=tmp_path, run_id="wrap-schema")
    tracker = CostTracker()
    ctx = StageContext(writer=writer, cost_tracker=tracker, edits={})

    state = RunState(
        run_id="wrap-schema",
        agent="trust_risk",
        stage="intake",
        inputs=inp,
        cost_so_far=Cost(),
    )

    handlers = agent.stage_handlers()
    next_state = handlers["intake"](state, ctx)
    assert isinstance(next_state.inputs, TrustRiskAgentInput)
    assert next_state.inputs.product_name == "AcmeCorp Platform"


# ---------------------------------------------------------------------------
# UX-004 — _stage_to_status maps "approval" → "awaiting_approval"
# ---------------------------------------------------------------------------

def test_stage_to_status_approval_maps_to_awaiting_approval():
    """CLI JSON status: 'approval' stage must emit 'awaiting_approval'."""
    from agentsuite.agents.trust_risk.agent import _stage_to_status
    assert _stage_to_status("approval") == "awaiting_approval"


def test_stage_to_status_done_passes_through():
    """CLI JSON status: 'done' stage must emit 'done' unchanged."""
    from agentsuite.agents.trust_risk.agent import _stage_to_status
    assert _stage_to_status("done") == "done"


def test_stage_to_status_other_stages_pass_through():
    """CLI JSON status: intermediate stages pass through unchanged."""
    from agentsuite.agents.trust_risk.agent import _stage_to_status
    for stage in ("intake", "extract", "spec", "execute", "qa"):
        assert _stage_to_status(stage) == stage


def test_agent_registered():
    """TrustRiskAgent appears in the default registry."""
    import os
    import agentsuite.agents.registry as reg_module

    # Reset singleton so bootstrap runs fresh
    reg_module._DEFAULT_REGISTRY = None
    os.environ["AGENTSUITE_ENABLED_AGENTS"] = (
        "founder,design,product,engineering,marketing,trust_risk"
    )

    from agentsuite.agents.registry import default_registry
    registry = default_registry()
    assert "trust_risk" in registry.enabled_names()
    assert registry.get_class("trust_risk") is TrustRiskAgent
