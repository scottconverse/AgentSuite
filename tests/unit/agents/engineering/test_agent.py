"""Unit tests for EngineeringAgent — structure, registration, and intake smoke test."""
from __future__ import annotations

from agentsuite.agents.engineering.agent import EngineeringAgent
from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC
from agentsuite.llm.mock import MockLLMProvider


def _minimal_input() -> EngineeringAgentInput:
    return EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering",
        user_request="design a system architecture",
        system_name="PaymentService",
        problem_domain="payment processing",
        tech_stack="Python + FastAPI + PostgreSQL + Redis",
        scale_requirements="10k RPM, 99.9% uptime, <200ms p99",
    )


def test_agent_name():
    assert EngineeringAgent.name == "engineering"


def test_stage_handler_count(tmp_path):
    agent = EngineeringAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert len(agent.stage_handlers()) == 5


def test_stage_keys(tmp_path):
    agent = EngineeringAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert set(agent.stage_handlers().keys()) == {"intake", "extract", "spec", "execute", "qa"}


def test_rubric_identity(tmp_path):
    agent = EngineeringAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert agent.qa_rubric is ENGINEERING_RUBRIC


def test_registry_registration():
    import os
    import agentsuite.agents.registry as reg_module
    # Reset singleton so bootstrap runs fresh
    reg_module._DEFAULT_REGISTRY = None
    os.environ["AGENTSUITE_ENABLED_AGENTS"] = "founder,design,product,engineering"

    from agentsuite.agents.registry import default_registry
    registry = default_registry()
    assert "engineering" in registry.enabled_names()
    assert registry.get_class("engineering") is EngineeringAgent


# ---------------------------------------------------------------------------
# UX-004 — _stage_to_status maps "approval" → "awaiting_approval"
# ---------------------------------------------------------------------------

def test_stage_to_status_approval_maps_to_awaiting_approval():
    """CLI JSON status: 'approval' stage must emit 'awaiting_approval'."""
    from agentsuite.agents.engineering.agent import _stage_to_status
    assert _stage_to_status("approval") == "awaiting_approval"


def test_stage_to_status_done_passes_through():
    """CLI JSON status: 'done' stage must emit 'done' unchanged."""
    from agentsuite.agents.engineering.agent import _stage_to_status
    assert _stage_to_status("done") == "done"


def test_stage_to_status_other_stages_pass_through():
    """CLI JSON status: intermediate stages pass through unchanged."""
    from agentsuite.agents.engineering.agent import _stage_to_status
    for stage in ("intake", "extract", "spec", "execute", "qa"):
        assert _stage_to_status(stage) == stage


def test_intake_smoke(tmp_path):
    """Smoke test: intake stage runs without error and advances to 'extract'."""
    agent = EngineeringAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    inp = _minimal_input()

    # Run only the intake stage by calling its handler directly
    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.base_agent import StageContext
    from agentsuite.kernel.artifacts import ArtifactWriter
    from agentsuite.kernel.cost import CostTracker

    writer = ArtifactWriter(output_root=tmp_path, run_id="smoke")
    tracker = CostTracker()
    ctx = StageContext(writer=writer, cost_tracker=tracker, edits={})

    state = RunState(
        run_id="smoke",
        agent="engineering",
        stage="intake",
        inputs=inp,
        cost_so_far=Cost(),
    )

    handlers = agent.stage_handlers()
    next_state = handlers["intake"](state, ctx)
    assert next_state.stage == "extract"
