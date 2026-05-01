"""Integration tests for PipelineOrchestrator (mock LLM)."""
import pytest

from agentsuite.llm.mock import _default_mock_for_cli
from agentsuite.pipeline.orchestrator import PipelineOrchestrator
from agentsuite.pipeline.state_store import PipelineNotFound


@pytest.fixture(autouse=True)
def enable_agents(monkeypatch):
    """Ensure founder and design are in the enabled agent list for all tests."""
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder,design,product,marketing")


class TestPipelineAutoApprove:
    def test_two_agent_pipeline_runs_to_done(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        assert state.status == "done"
        assert state.current_step_index == 2

    def test_all_steps_marked_done_after_auto_approve(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        for step in state.steps:
            assert step.status == "done"

    def test_run_artifacts_written_for_each_agent(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        for step in state.steps:
            run_dir = tmp_path / "runs" / step.run_id
            assert run_dir.exists(), f"run dir missing for {step.agent}"
            assert (run_dir / "_state.json").exists()

    def test_kernel_promoted_after_auto_approve(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        orch.run(
            agents=["founder"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        assert (tmp_path / "_kernel" / "pfl").exists()

    def test_pipeline_state_persisted_to_disk(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        pipeline_json = tmp_path / "pipelines" / state.pipeline_id / "_pipeline.json"
        assert pipeline_json.exists()

    def test_total_cost_accumulated_across_agents(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        assert state.total_cost_usd >= 0.0

    def test_single_agent_pipeline(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        assert state.status == "done"
        assert len(state.steps) == 1


class TestPipelineManualApproval:
    def test_pipeline_pauses_at_first_agent(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=False,
            llm=_default_mock_for_cli(),
        )
        assert state.status == "awaiting_approval"
        assert state.current_step_index == 0
        assert state.steps[0].status == "awaiting_approval"

    def test_approve_advances_to_next_agent(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=False,
            llm=_default_mock_for_cli(),
        )
        state = orch.approve(
            pipeline_id=state.pipeline_id,
            approver="scott",
            llm=_default_mock_for_cli(),
        )
        # After approving founder, design runs and pauses at its approval gate
        assert state.current_step_index == 1
        assert state.steps[0].status == "done"

    def test_approve_last_agent_marks_pipeline_done(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=False,
            llm=_default_mock_for_cli(),
        )
        assert state.status == "awaiting_approval"
        state = orch.approve(
            pipeline_id=state.pipeline_id,
            approver="scott",
            llm=_default_mock_for_cli(),
        )
        assert state.status == "done"

    def test_status_returns_current_state(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        running = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=False,
            llm=_default_mock_for_cli(),
        )
        queried = orch.status(pipeline_id=running.pipeline_id)
        assert queried.pipeline_id == running.pipeline_id
        assert queried.status == "awaiting_approval"

    def test_approve_non_existent_pipeline_raises(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        with pytest.raises(PipelineNotFound):
            orch.approve(pipeline_id="no-such-pipeline", approver="scott")

    def test_approve_wrong_status_raises(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder"],
            project_slug="pfl",
            business_goal="Launch PatentForgeLocal v1",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        with pytest.raises(ValueError, match="not 'awaiting_approval'"):
            orch.approve(pipeline_id=state.pipeline_id, approver="scott")


class TestProgressCallback:
    def test_callback_fires_start_and_done_for_each_agent(self, tmp_path):
        events: list[tuple[str, str]] = []

        def on_progress(event, step, state):
            events.append((event, step.agent))

        orch = PipelineOrchestrator(output_root=tmp_path)
        orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="test",
            auto_approve=True,
            llm=_default_mock_for_cli(),
            on_progress=on_progress,
        )

        assert events == [
            ("agent_start", "founder"),
            ("agent_done", "founder"),
            ("agent_start", "design"),
            ("agent_done", "design"),
        ]

    def test_callback_fires_waiting_on_manual_pause(self, tmp_path):
        events: list[str] = []

        def on_progress(event, step, state):
            events.append(event)

        orch = PipelineOrchestrator(output_root=tmp_path)
        orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="test",
            auto_approve=False,
            llm=_default_mock_for_cli(),
            on_progress=on_progress,
        )

        assert events == ["agent_start", "agent_waiting"]

    def test_callback_not_required(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder"],
            project_slug="pfl",
            business_goal="test",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        assert state.status == "done"

    def test_callback_fires_on_approve_for_subsequent_agents(self, tmp_path):
        events: list[tuple[str, str]] = []

        def on_progress(event, step, state):
            events.append((event, step.agent))

        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder", "design"],
            project_slug="pfl",
            business_goal="test",
            auto_approve=False,
            llm=_default_mock_for_cli(),
        )
        orch.approve(
            pipeline_id=state.pipeline_id,
            approver="scott",
            llm=_default_mock_for_cli(),
            on_progress=on_progress,
        )

        # After approve, design runs and pauses — callback fires for design
        assert ("agent_start", "design") in events


class TestPipelineList:
    def test_list_returns_all_pipelines(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        for slug in ("alpha", "beta"):
            orch.run(
                agents=["founder"],
                project_slug=slug,
                business_goal="test",
                auto_approve=True,
                llm=_default_mock_for_cli(),
            )
        pipelines_root = tmp_path / "pipelines"
        ids = [d.name for d in pipelines_root.iterdir() if d.is_dir()]
        assert len(ids) == 2

    def test_list_empty_when_no_pipelines(self, tmp_path):
        pipelines_root = tmp_path / "pipelines"
        assert not pipelines_root.exists()


class TestPipelineValidation:
    def test_empty_agents_list_raises(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        with pytest.raises(ValueError, match="must not be empty"):
            orch.run(
                agents=[],
                project_slug="pfl",
                business_goal="test",
                llm=_default_mock_for_cli(),
            )

    def test_custom_pipeline_id_used(self, tmp_path):
        orch = PipelineOrchestrator(output_root=tmp_path)
        state = orch.run(
            agents=["founder"],
            project_slug="pfl",
            business_goal="test",
            pipeline_id="my-custom-id",
            auto_approve=True,
            llm=_default_mock_for_cli(),
        )
        assert state.pipeline_id == "my-custom-id"
