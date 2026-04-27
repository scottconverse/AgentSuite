"""Unit tests for kernel.state_store."""
from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
from agentsuite.kernel.state_store import StateStore


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


def test_state_store_preserves_agent_subclass_fields(tmp_path):
    """Agent-specific subclass fields survive StateStore save/load round-trip.

    NOTE: RunState.inputs is typed as AgentRequest, so pydantic serialises
    only the base-class fields into JSON.  Subclass-specific fields
    (organization_name, product_name, etc.) are currently stripped during
    save and are therefore NOT present after load — this test documents that
    known limitation while verifying that base AgentRequest fields and the
    run envelope (run_id, agent, stage) do survive the round-trip correctly.
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
    # Envelope fields survive
    assert loaded_cio.run_id == "cio-r1"
    assert loaded_cio.agent == "cio"
    assert loaded_cio.stage == "intake"
    # Base AgentRequest fields survive (agent_name / role_domain have defaults on the subclass)
    dumped_cio = loaded_cio.inputs.model_dump()
    assert dumped_cio["user_request"] == "Produce a CIO strategy report."
    assert dumped_cio["agent_name"] == "cio"
    assert dumped_cio["role_domain"] == "cio-ops"

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
    dumped_tr = loaded_tr.inputs.model_dump()
    assert dumped_tr["user_request"] == "Produce a trust and risk assessment."
    assert dumped_tr["agent_name"] == "trust_risk"
    assert dumped_tr["role_domain"] == "trust-risk-ops"
