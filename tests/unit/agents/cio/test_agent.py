"""Unit tests for CIOAgent — structure, registration, and _wrap behavior."""
from __future__ import annotations

from agentsuite.agents.cio.agent import CIOAgent
from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.rubric import CIO_RUBRIC
from agentsuite.llm.mock import MockLLMProvider


def _minimal_input() -> CIOAgentInput:
    return CIOAgentInput(
        user_request="Develop an IT strategy for AcmeCorp",
        agent_name="cio",
        role_domain="cio-ops",
        organization_name="AcmeCorp",
        strategic_priorities="Cloud migration, AI adoption, cybersecurity hardening",
        it_maturity_level="Level 2 – Managed",
    )


def test_cio_agent_name():
    assert CIOAgent.name == "cio"


def test_cio_agent_rubric(tmp_path):
    agent = CIOAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert agent.qa_rubric is CIO_RUBRIC


def test_stage_handlers_keys(tmp_path):
    agent = CIOAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert set(agent.stage_handlers().keys()) == {"intake", "extract", "spec", "execute", "qa"}


def test_stage_handlers_callables(tmp_path):
    agent = CIOAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    for name, handler in agent.stage_handlers().items():
        assert callable(handler), f"Handler '{name}' is not callable"


_INTAKE_MOCK_RESPONSES = {
    "indexing IT source materials": "Intake acknowledged.",
}


def test_wrap_with_dict_input(tmp_path):
    """_wrap() with dict input constructs CIOAgentInput correctly."""
    agent = CIOAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_INTAKE_MOCK_RESPONSES))

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
        agent="cio",
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
    # The _wrap function should reconstruct CIOAgentInput from the dict
    next_state = handlers["intake"](state, ctx)
    assert isinstance(next_state.inputs, CIOAgentInput)
    assert next_state.inputs.organization_name == "AcmeCorp"


def test_wrap_with_schema_input(tmp_path):
    """_wrap() with CIOAgentInput instance passes through unchanged."""
    agent = CIOAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_INTAKE_MOCK_RESPONSES))

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
        agent="cio",
        stage="intake",
        inputs=inp,
        cost_so_far=Cost(),
    )

    handlers = agent.stage_handlers()
    next_state = handlers["intake"](state, ctx)
    assert isinstance(next_state.inputs, CIOAgentInput)
    assert next_state.inputs.organization_name == "AcmeCorp"


def test_agent_registered():
    """CIOAgent appears in the default registry."""
    import os
    import agentsuite.agents.registry as reg_module

    # Reset singleton so bootstrap runs fresh
    reg_module._DEFAULT_REGISTRY = None
    os.environ["AGENTSUITE_ENABLED_AGENTS"] = "cio"

    from agentsuite.agents.registry import default_registry
    registry = default_registry()
    assert "cio" in registry.enabled_names()
    assert registry.get_class("cio") is CIOAgent
