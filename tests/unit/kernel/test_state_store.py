"""Unit tests for kernel.state_store."""
import json

import pytest

from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
from agentsuite.kernel.state_store import (
    SCHEMA_VERSION,
    RunStateSchemaVersionError,
    StateStore,
)


def _request() -> AgentRequest:
    return AgentRequest(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        constraints=Constraints(),
    )


def test_state_store_writes_and_reads_state(tmp_path):
    store = StateStore(run_dir=tmp_path)
    state = RunState(run_id="r1", agent="founder", inputs=_request())
    store.save(state)
    loaded = store.load()
    assert loaded is not None
    assert loaded.run_id == "r1"
    assert loaded.stage == "intake"


def test_state_store_overwrites_on_save(tmp_path):
    store = StateStore(run_dir=tmp_path)
    state = RunState(run_id="r1", agent="founder", inputs=_request())
    store.save(state)
    state.stage = "extract"
    store.save(state)
    loaded = store.load()
    assert loaded is not None
    assert loaded.stage == "extract"


def test_state_store_load_missing_returns_none(tmp_path):
    store = StateStore(run_dir=tmp_path)
    assert store.load() is None


def test_state_store_save_leaves_no_tmp_files(tmp_path):
    """Atomic save must not leave .tmp files behind on success."""
    store = StateStore(run_dir=tmp_path)
    state = RunState(run_id="r1", agent="founder", inputs=_request())
    store.save(state)
    leftover = list(tmp_path.glob("*.tmp"))
    assert leftover == [], f"Stale .tmp files after save: {leftover}"
    assert store.path.exists()


def test_state_store_preserves_agent_subclass_fields(tmp_path):
    """Agent-specific subclass fields survive StateStore save/load round-trip.

    v0.9.0: ``StateStore.save()`` now dumps ``inputs`` using the runtime
    instance's schema rather than the declared
    ``RunState.inputs: AgentRequest`` field type, and ``load()`` re-validates
    against the agent's input subclass via the lazy-import registry. CIO's
    ``organization_name`` / ``strategic_priorities`` and TrustRisk's
    ``product_name`` / ``risk_domain`` survive the round-trip and the loaded
    instance is the actual subclass type, not the base.
    """
    from agentsuite.agents.cio.input_schema import CIOAgentInput
    from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput

    # --- CIO agent ---
    cio_input = CIOAgentInput(
        user_request="Produce a CIO strategy report.",
        organization_name="Acme Corp",
        strategic_priorities="Cloud migration, AI adoption",
        it_maturity_level="Level 3 - Defined",
    )
    store_cio = StateStore(run_dir=tmp_path / "cio")
    store_cio.run_dir.mkdir(parents=True, exist_ok=True)
    state_cio = RunState(run_id="cio-r1", agent="cio", inputs=cio_input)
    store_cio.save(state_cio)
    loaded_cio = store_cio.load()
    assert loaded_cio is not None
    assert loaded_cio.run_id == "cio-r1"
    assert loaded_cio.agent == "cio"
    assert loaded_cio.stage == "intake"
    # Loaded instance is the subclass, not the base — direct attribute access works.
    assert isinstance(loaded_cio.inputs, CIOAgentInput)
    assert loaded_cio.inputs.organization_name == "Acme Corp"
    assert loaded_cio.inputs.strategic_priorities == "Cloud migration, AI adoption"
    assert loaded_cio.inputs.it_maturity_level == "Level 3 - Defined"
    assert loaded_cio.inputs.user_request == "Produce a CIO strategy report."
    assert loaded_cio.inputs.agent_name == "cio"

    # --- TrustRisk agent ---
    trust_input = TrustRiskAgentInput(
        user_request="Produce a trust and risk assessment.",
        product_name="SecureVault",
        risk_domain="cloud-infra",
        stakeholder_context="Engineering team, 50 engineers",
    )
    store_tr = StateStore(run_dir=tmp_path / "trust_risk")
    store_tr.run_dir.mkdir(parents=True, exist_ok=True)
    state_tr = RunState(run_id="tr-r1", agent="trust_risk", inputs=trust_input)
    store_tr.save(state_tr)
    loaded_tr = store_tr.load()
    assert loaded_tr is not None
    assert loaded_tr.run_id == "tr-r1"
    assert loaded_tr.agent == "trust_risk"
    assert isinstance(loaded_tr.inputs, TrustRiskAgentInput)
    assert loaded_tr.inputs.product_name == "SecureVault"
    assert loaded_tr.inputs.risk_domain == "cloud-infra"
    assert loaded_tr.inputs.stakeholder_context == "Engineering team, 50 engineers"


# --- v0.9.0: schema_version + parametrised round-trip --------------------


def test_state_store_writes_schema_version(tmp_path):
    """Every saved _state.json carries the current SCHEMA_VERSION."""
    store = StateStore(run_dir=tmp_path)
    state = RunState(run_id="r1", agent="founder", inputs=_request())
    store.save(state)
    raw = json.loads(store.path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == SCHEMA_VERSION


def test_state_store_load_rejects_pre_v0_9_state(tmp_path):
    """Loading a state file without schema_version raises a typed error.

    The error message names the offending run dir so the operator can act
    on it directly without reading source.
    """
    store = StateStore(run_dir=tmp_path)
    legacy = {
        "run_id": "r1",
        "agent": "founder",
        "stage": "intake",
        "inputs": {
            "agent_name": "founder",
            "role_domain": "creative-ops",
            "user_request": "x",
        },
        "artifacts": [],
        "open_questions": [],
        "cost_so_far": {"input_tokens": 0, "output_tokens": 0, "usd": 0.0, "model": None},
        "started_at": "2026-04-28T00:00:00+00:00",
        "updated_at": "2026-04-28T00:00:00+00:00",
        "requires_revision": False,
        "approved_at": None,
        "approved_by": None,
        # No schema_version — simulates pre-v0.9 state.
    }
    store.run_dir.mkdir(parents=True, exist_ok=True)
    store.path.write_text(json.dumps(legacy), encoding="utf-8")
    with pytest.raises(RunStateSchemaVersionError, match="Pre-v0.9 state files are not supported"):
        store.load()


def test_state_store_load_rejects_older_schema_version(tmp_path):
    """An on-disk schema_version < SCHEMA_VERSION is also rejected."""
    store = StateStore(run_dir=tmp_path)
    legacy = {"schema_version": SCHEMA_VERSION - 1, "run_id": "r1", "agent": "founder"}
    store.run_dir.mkdir(parents=True, exist_ok=True)
    store.path.write_text(json.dumps(legacy), encoding="utf-8")
    with pytest.raises(RunStateSchemaVersionError):
        store.load()


@pytest.mark.parametrize(
    "agent, build_input, attr_to_check, expected_value",
    [
        (
            "founder",
            lambda: __import__("agentsuite.agents.founder.input_schema", fromlist=["FounderAgentInput"]).FounderAgentInput(
                agent_name="founder", role_domain="creative-ops",
                user_request="Build brand system.", business_goal="Launch new product.",
            ),
            "business_goal",
            "Launch new product.",
        ),
        (
            "design",
            lambda: __import__("agentsuite.agents.design.input_schema", fromlist=["DesignAgentInput"]).DesignAgentInput(
                agent_name="design", role_domain="creative-ops",
                user_request="Make a landing page hero.",
                target_audience="Indie devs",
                campaign_goal="Drive sign-ups",
            ),
            "campaign_goal",
            "Drive sign-ups",
        ),
        (
            "product",
            lambda: __import__("agentsuite.agents.product.input_schema", fromlist=["ProductAgentInput"]).ProductAgentInput(
                agent_name="product", role_domain="product-ops",
                user_request="Spec the new feature.",
                product_name="Widget Pro",
                target_users="Power users",
                core_problem="Widgets are slow",
            ),
            "product_name",
            "Widget Pro",
        ),
        (
            "engineering",
            lambda: __import__("agentsuite.agents.engineering.input_schema", fromlist=["EngineeringAgentInput"]).EngineeringAgentInput(
                agent_name="engineering", role_domain="engineering-ops",
                user_request="Design the system.",
                system_name="OrderService",
                problem_domain="Order processing at scale",
                tech_stack="Python + FastAPI + Postgres",
                scale_requirements="5k RPM, 99.9% uptime",
            ),
            "system_name",
            "OrderService",
        ),
        (
            "marketing",
            lambda: __import__("agentsuite.agents.marketing.input_schema", fromlist=["MarketingAgentInput"]).MarketingAgentInput(
                user_request="Plan the launch campaign.",
                brand_name="Acme",
                campaign_goal="Awareness in target market",
                target_market="SMB engineering teams",
            ),
            "brand_name",
            "Acme",
        ),
        (
            "trust_risk",
            lambda: __import__("agentsuite.agents.trust_risk.input_schema", fromlist=["TrustRiskAgentInput"]).TrustRiskAgentInput(
                user_request="Assess the risk surface.",
                product_name="SecureVault",
                risk_domain="cloud-infra",
                stakeholder_context="Engineering team, 50 engineers",
            ),
            "product_name",
            "SecureVault",
        ),
        (
            "cio",
            lambda: __import__("agentsuite.agents.cio.input_schema", fromlist=["CIOAgentInput"]).CIOAgentInput(
                user_request="Produce strategy.",
                organization_name="Acme Corp",
                strategic_priorities="Cloud migration",
                it_maturity_level="Level 3",
            ),
            "organization_name",
            "Acme Corp",
        ),
    ],
)
def test_state_store_round_trip_preserves_subclass_field_for_each_agent(
    tmp_path, agent, build_input, attr_to_check, expected_value
):
    """All 7 agents: subclass-specific input field survives save/load round-trip."""
    inputs = build_input()
    store = StateStore(run_dir=tmp_path / agent)
    store.run_dir.mkdir(parents=True, exist_ok=True)
    state = RunState(run_id=f"{agent}-r1", agent=agent, inputs=inputs)
    store.save(state)
    loaded = store.load()
    assert loaded is not None
    assert isinstance(loaded.inputs, type(inputs))
    assert getattr(loaded.inputs, attr_to_check) == expected_value
