"""Unit tests for ProductAgent — structure, registration, and intake smoke test."""
from __future__ import annotations

from agentsuite.agents.product.agent import ProductAgent
from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.rubric import PRODUCT_RUBRIC
from agentsuite.llm.mock import MockLLMProvider


def _minimal_input() -> ProductAgentInput:
    return ProductAgentInput(
        agent_name="product",
        role_domain="product",
        user_request="build a product spec",
        product_name="MyApp",
        target_users="developers",
        core_problem="too much manual work",
    )


def test_product_agent_name():
    assert ProductAgent.name == "product"


def test_product_agent_has_five_stage_handlers(tmp_path):
    agent = ProductAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert len(agent.stage_handlers()) == 5


def test_product_agent_stage_names(tmp_path):
    agent = ProductAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert set(agent.stage_handlers().keys()) == {"intake", "extract", "spec", "execute", "qa"}


def test_product_agent_uses_product_rubric(tmp_path):
    agent = ProductAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert agent.qa_rubric is PRODUCT_RUBRIC


def test_product_agent_registered_in_default_registry():
    import os
    import agentsuite.agents.registry as reg_module
    # Reset singleton so bootstrap runs fresh
    reg_module._DEFAULT_REGISTRY = None
    os.environ["AGENTSUITE_ENABLED_AGENTS"] = "founder,design,product"

    from agentsuite.agents.registry import default_registry
    registry = default_registry()
    assert "product" in registry.enabled_names()
    assert registry.get_class("product") is ProductAgent


# ---------------------------------------------------------------------------
# UX-004 — _stage_to_status maps "approval" → "awaiting_approval"
# ---------------------------------------------------------------------------

def test_stage_to_status_approval_maps_to_awaiting_approval():
    """CLI JSON status: 'approval' stage must emit 'awaiting_approval'."""
    from agentsuite.kernel.base_agent import stage_to_status as _stage_to_status
    assert _stage_to_status("approval") == "awaiting_approval"


def test_stage_to_status_done_passes_through():
    """CLI JSON status: 'done' stage must emit 'done' unchanged."""
    from agentsuite.kernel.base_agent import stage_to_status as _stage_to_status
    assert _stage_to_status("done") == "done"


def test_stage_to_status_other_stages_pass_through():
    """CLI JSON status: intermediate stages pass through unchanged."""
    from agentsuite.kernel.base_agent import stage_to_status as _stage_to_status
    for stage in ("intake", "extract", "spec", "execute", "qa"):
        assert _stage_to_status(stage) == stage


def test_product_agent_accepts_valid_input(tmp_path):
    """Smoke test: intake stage runs without error and advances to 'extract'."""
    agent = ProductAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
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
        agent="product",
        stage="intake",
        inputs=inp,
        cost_so_far=Cost(),
    )

    handlers = agent.stage_handlers()
    next_state = handlers["intake"](state, ctx)
    assert next_state.stage == "extract"
