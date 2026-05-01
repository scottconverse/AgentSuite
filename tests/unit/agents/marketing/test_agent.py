"""Unit tests for MarketingAgent — structure, registration, and intake smoke test."""
from __future__ import annotations

from agentsuite.agents.marketing.agent import MarketingAgent
from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.rubric import MARKETING_RUBRIC
from agentsuite.llm.mock import MockLLMProvider


def _minimal_input() -> MarketingAgentInput:
    return MarketingAgentInput(
        user_request="Drive signups for TestBrand targeting SMBs",
        agent_name="marketing",
        role_domain="marketing-ops",
        brand_name="TestBrand",
        campaign_goal="Drive signups",
        target_market="SMBs",
    )


def test_agent_name():
    assert MarketingAgent.name == "marketing"


def test_stage_handler_count(tmp_path):
    agent = MarketingAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert len(agent.stage_handlers()) == 5


def test_stage_keys(tmp_path):
    agent = MarketingAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert set(agent.stage_handlers().keys()) == {"intake", "extract", "spec", "execute", "qa"}


def test_rubric_identity(tmp_path):
    agent = MarketingAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    assert agent.qa_rubric is MARKETING_RUBRIC


def test_registry_registration():
    import os
    import agentsuite.agents.registry as reg_module
    # Reset singleton so bootstrap runs fresh
    reg_module._DEFAULT_REGISTRY = None
    os.environ["AGENTSUITE_ENABLED_AGENTS"] = "founder,design,product,engineering,marketing"

    from agentsuite.agents.registry import default_registry
    registry = default_registry()
    assert "marketing" in registry.enabled_names()
    assert registry.get_class("marketing") is MarketingAgent


# ---------------------------------------------------------------------------
# UX-004 — _stage_to_status maps "approval" → "awaiting_approval"
# ---------------------------------------------------------------------------

def test_stage_to_status_approval_maps_to_awaiting_approval():
    """CLI JSON status: 'approval' stage must emit 'awaiting_approval'."""
    from agentsuite.agents.marketing.agent import _stage_to_status
    assert _stage_to_status("approval") == "awaiting_approval"


def test_stage_to_status_done_passes_through():
    """CLI JSON status: 'done' stage must emit 'done' unchanged."""
    from agentsuite.agents.marketing.agent import _stage_to_status
    assert _stage_to_status("done") == "done"


def test_stage_to_status_other_stages_pass_through():
    """CLI JSON status: intermediate stages pass through unchanged."""
    from agentsuite.agents.marketing.agent import _stage_to_status
    for stage in ("intake", "extract", "spec", "execute", "qa"):
        assert _stage_to_status(stage) == stage


def test_intake_smoke(tmp_path):
    """Smoke test: intake stage runs without error and advances to 'extract'."""
    agent = MarketingAgent(output_root=tmp_path, llm=MockLLMProvider(responses={}))
    inp = MarketingAgentInput(
        user_request="Drive signups for TestBrand targeting SMBs",
        brand_name="TestBrand",
        campaign_goal="Drive signups",
        target_market="SMBs",
        agent_name="marketing",
        role_domain="marketing-ops",
    )

    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.base_agent import StageContext
    from agentsuite.kernel.artifacts import ArtifactWriter
    from agentsuite.kernel.cost import CostTracker

    writer = ArtifactWriter(output_root=tmp_path, run_id="smoke")
    tracker = CostTracker()
    ctx = StageContext(writer=writer, cost_tracker=tracker, edits={})

    state = RunState(
        run_id="smoke",
        agent="marketing",
        stage="intake",
        inputs=inp,
        cost_so_far=Cost(),
    )

    handlers = agent.stage_handlers()
    next_state = handlers["intake"](state, ctx)
    assert next_state.stage == "extract"
    assert (tmp_path / "runs" / "smoke" / "inputs_manifest.json").exists()
