"""Unit tests for PipelineStateStore save/load round-trip."""
import pytest

from agentsuite.pipeline.schema import PipelineState, PipelineStepState
from agentsuite.pipeline.state_store import PipelineNotFound, PipelineStateStore


def _make_state(pipeline_id: str = "test-pipe") -> PipelineState:
    return PipelineState(
        pipeline_id=pipeline_id,
        project_slug="myapp",
        business_goal="Launch MyApp",
        agents=["founder", "design"],
        steps=[
            PipelineStepState(agent="founder", run_id=f"{pipeline_id}-founder"),
            PipelineStepState(agent="design",  run_id=f"{pipeline_id}-design"),
        ],
    )


class TestPipelineStateStore:
    def test_save_creates_pipeline_json(self, tmp_path):
        store = PipelineStateStore(tmp_path, "p1")
        state = _make_state("p1")
        store.save(state)
        assert store.path.exists()

    def test_load_round_trips_state(self, tmp_path):
        store = PipelineStateStore(tmp_path, "p1")
        original = _make_state("p1")
        store.save(original)
        loaded = store.load()
        assert loaded.pipeline_id == "p1"
        assert loaded.agents == ["founder", "design"]
        assert loaded.project_slug == "myapp"
        assert len(loaded.steps) == 2

    def test_load_raises_pipeline_not_found(self, tmp_path):
        store = PipelineStateStore(tmp_path, "nonexistent")
        with pytest.raises(PipelineNotFound):
            store.load()

    def test_save_overwrites_existing(self, tmp_path):
        store = PipelineStateStore(tmp_path, "p1")
        state = _make_state("p1")
        store.save(state)
        state.status = "done"
        store.save(state)
        assert store.load().status == "done"

    def test_save_is_atomic_via_tmp_file(self, tmp_path):
        store = PipelineStateStore(tmp_path, "p1")
        store.save(_make_state("p1"))
        tmp = store.path.with_suffix(".json.tmp")
        assert not tmp.exists()

    def test_agent_extras_round_trip(self, tmp_path):
        store = PipelineStateStore(tmp_path, "p1")
        state = _make_state("p1")
        state.agent_extras = {"engineering": {"tech_stack": "Python", "scale_requirements": "1k"}}
        store.save(state)
        loaded = store.load()
        assert loaded.agent_extras["engineering"]["tech_stack"] == "Python"

    def test_inputs_dir_round_trip(self, tmp_path):
        store = PipelineStateStore(tmp_path, "p1")
        state = _make_state("p1")
        state.inputs_dir = "/some/path"
        store.save(state)
        assert store.load().inputs_dir == "/some/path"
