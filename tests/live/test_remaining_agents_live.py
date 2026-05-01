"""Live tier stubs — gated by RUN_LIVE_TESTS=1. Uses real LLM, capped at $3 per test.

Covers the six agents that have no live test yet: design, product, engineering,
marketing, trust_risk, cio. Each test mirrors the pattern in test_founder_live.py:
resolve the live provider, run the full pipeline, and assert the pipeline reaches
the approval stage and produces its primary artifact.

Tests are skipped by default (see conftest.py) unless RUN_LIVE_TESTS=1.
They are intended for v0.X.0 release boundaries only.
"""
import pytest

from agentsuite.agents.design.agent import DesignAgent
from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.engineering.agent import EngineeringAgent
from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.marketing.agent import MarketingAgent
from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.product.agent import ProductAgent
from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.trust_risk.agent import TrustRiskAgent
from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.cio.agent import CIOAgent
from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.llm.resolver import resolve_provider


pytestmark = pytest.mark.live

PER_TEST_CAP_USD = 3.0


def test_design_full_pipeline_live(tmp_path, monkeypatch):
    """Full Design pipeline against real LLM.

    Cost-capped at ``PER_TEST_CAP_USD`` via the ``AGENTSUITE_COST_CAP_USD`` env.
    Asserts: pipeline reaches approval stage and primary artifact exists.
    """
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", str(PER_TEST_CAP_USD))
    agent = DesignAgent(output_root=tmp_path, llm=resolve_provider())
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="design-ops",
        user_request="build visual identity for a developer productivity tool",
        target_audience="software developers and engineering teams",
        campaign_goal="drive adoption at developer-tools product launch",
        channel="web",
        project_slug="devtool-live",
    )
    state = agent.run(request=inp, run_id="live-design-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "live-design-r1"
    assert (run_dir / "visual-direction.md").exists()
    assert state.cost_so_far.usd <= PER_TEST_CAP_USD


def test_product_full_pipeline_live(tmp_path, monkeypatch):
    """Full Product pipeline against real LLM.

    Cost-capped at ``PER_TEST_CAP_USD`` via the ``AGENTSUITE_COST_CAP_USD`` env.
    Asserts: pipeline reaches approval stage and primary artifact exists.
    """
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", str(PER_TEST_CAP_USD))
    agent = ProductAgent(output_root=tmp_path, llm=resolve_provider())
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product-ops",
        user_request="define the product spec for a code review assistant",
        product_name="ReviewBot",
        target_users="software engineers on mid-size teams",
        core_problem="code reviews are slow and inconsistent",
    )
    state = agent.run(request=inp, run_id="live-product-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "live-product-r1"
    assert (run_dir / "product-requirements-doc.md").exists()
    assert state.cost_so_far.usd <= PER_TEST_CAP_USD


def test_engineering_full_pipeline_live(tmp_path, monkeypatch):
    """Full Engineering pipeline against real LLM.

    Cost-capped at ``PER_TEST_CAP_USD`` via the ``AGENTSUITE_COST_CAP_USD`` env.
    Asserts: pipeline reaches approval stage and primary artifact exists.
    """
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", str(PER_TEST_CAP_USD))
    agent = EngineeringAgent(output_root=tmp_path, llm=resolve_provider())
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering-ops",
        user_request="design the architecture for a real-time notification service",
        system_name="NotifStream",
        problem_domain="real-time event delivery at scale",
        tech_stack="Python FastAPI + Redis + WebSockets",
        scale_requirements="100k concurrent connections, <100ms delivery p99",
    )
    state = agent.run(request=inp, run_id="live-engineering-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "live-engineering-r1"
    assert (run_dir / "architecture-decision-record.md").exists()
    assert state.cost_so_far.usd <= PER_TEST_CAP_USD


def test_marketing_full_pipeline_live(tmp_path, monkeypatch):
    """Full Marketing pipeline against real LLM.

    Cost-capped at ``PER_TEST_CAP_USD`` via the ``AGENTSUITE_COST_CAP_USD`` env.
    Asserts: pipeline reaches approval stage and primary artifact exists.
    """
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", str(PER_TEST_CAP_USD))
    agent = MarketingAgent(output_root=tmp_path, llm=resolve_provider())
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="create a product launch campaign for a developer tool",
        brand_name="AgentSuite",
        campaign_goal="drive 500 signups in the first 30 days post-launch",
        target_market="engineering leads and CTOs at seed-stage startups",
    )
    state = agent.run(request=inp, run_id="live-marketing-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "live-marketing-r1"
    assert (run_dir / "campaign-brief.md").exists()
    assert state.cost_so_far.usd <= PER_TEST_CAP_USD


def test_trust_risk_full_pipeline_live(tmp_path, monkeypatch):
    """Full Trust/Risk pipeline against real LLM.

    Cost-capped at ``PER_TEST_CAP_USD`` via the ``AGENTSUITE_COST_CAP_USD`` env.
    Asserts: pipeline reaches approval stage and primary artifact exists.
    """
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", str(PER_TEST_CAP_USD))
    agent = TrustRiskAgent(output_root=tmp_path, llm=resolve_provider())
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="assess the trust and risk posture for a multi-tenant SaaS platform",
        product_name="AgentSuite Cloud",
        risk_domain="multi-tenant SaaS",
        stakeholder_context="CISO, CTO, and enterprise customer security review teams",
    )
    state = agent.run(request=inp, run_id="live-trust-risk-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "live-trust-risk-r1"
    assert (run_dir / "threat-model.md").exists()
    assert state.cost_so_far.usd <= PER_TEST_CAP_USD


def test_cio_full_pipeline_live(tmp_path, monkeypatch):
    """Full CIO pipeline against real LLM.

    Cost-capped at ``PER_TEST_CAP_USD`` via the ``AGENTSUITE_COST_CAP_USD`` env.
    Asserts: pipeline reaches approval stage and primary artifact exists.
    """
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", str(PER_TEST_CAP_USD))
    agent = CIOAgent(output_root=tmp_path, llm=resolve_provider())
    inp = CIOAgentInput(
        agent_name="cio",
        role_domain="cio-ops",
        user_request="produce a 3-year IT strategy for a high-growth SaaS company",
        organization_name="GrowthCo",
        strategic_priorities="cloud-native migration, AI adoption, developer platform",
        it_maturity_level="Level 3 - Defined",
    )
    state = agent.run(request=inp, run_id="live-cio-r1")
    assert state.stage == "approval"
    run_dir = tmp_path / "runs" / "live-cio-r1"
    assert (run_dir / "it-strategy.md").exists()
    assert state.cost_so_far.usd <= PER_TEST_CAP_USD
