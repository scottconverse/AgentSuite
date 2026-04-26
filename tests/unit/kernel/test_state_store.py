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
    assert loaded.run_id == "r1"
    assert loaded.stage == "intake"


def test_state_store_overwrites_on_save(tmp_path):
    store = StateStore(run_dir=tmp_path)
    state = RunState(run_id="r1", agent="founder", inputs=_request())
    store.save(state)
    state.stage = "extract"
    store.save(state)
    loaded = store.load()
    assert loaded.stage == "extract"


def test_state_store_load_missing_returns_none(tmp_path):
    store = StateStore(run_dir=tmp_path)
    assert store.load() is None
