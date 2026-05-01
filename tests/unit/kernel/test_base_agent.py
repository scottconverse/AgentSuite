"""Unit tests for kernel.base_agent."""

import pytest

from agentsuite.kernel.base_agent import BaseAgent, StageHandler
from agentsuite.kernel.qa import QARubric, RubricDimension
from agentsuite.kernel.schema import AgentRequest, Constraints


class _FakeAgent(BaseAgent):
    name = "fake"
    qa_rubric = QARubric(
        dimensions=[RubricDimension(name="ok", question="?")],
        pass_threshold=5.0,
    )

    def stage_handlers(self) -> dict[str, StageHandler]:
        def intake(state, ctx):
            ctx.writer.write_json("inputs_manifest.json", {"k": "v"}, kind="data", stage="intake")
            return state.model_copy(update={"stage": "extract"})

        def extract(state, ctx):
            return state.model_copy(update={"stage": "spec"})

        def spec(state, ctx):
            ctx.writer.write("primary.md", "x", kind="spec", stage="spec")
            return state.model_copy(update={"stage": "execute"})

        def execute(state, ctx):
            return state.model_copy(update={"stage": "qa"})

        def qa(state, ctx):
            return state.model_copy(update={"stage": "approval"})

        return {"intake": intake, "extract": extract, "spec": spec, "execute": execute, "qa": qa}


def _req() -> AgentRequest:
    return AgentRequest(
        agent_name="fake",
        role_domain="test",
        user_request="x",
        constraints=Constraints(),
    )


def test_run_advances_to_approval_stage(tmp_path):
    agent = _FakeAgent(output_root=tmp_path)
    state = agent.run(request=_req(), run_id="r1")
    assert state.stage == "approval"


def test_run_writes_state_file(tmp_path):
    agent = _FakeAgent(output_root=tmp_path)
    agent.run(request=_req(), run_id="r1")
    assert (tmp_path / "runs" / "r1" / "_state.json").exists()


def test_run_writes_artifacts(tmp_path):
    agent = _FakeAgent(output_root=tmp_path)
    agent.run(request=_req(), run_id="r1")
    assert (tmp_path / "runs" / "r1" / "primary.md").exists()
    assert (tmp_path / "runs" / "r1" / "inputs_manifest.json").exists()


def test_resume_re_runs_from_named_stage(tmp_path):
    agent = _FakeAgent(output_root=tmp_path)
    agent.run(request=_req(), run_id="r1")
    state = agent.resume(run_id="r1", stage="qa", edits={})
    assert state.stage == "approval"


def test_resume_unknown_run_raises(tmp_path):
    agent = _FakeAgent(output_root=tmp_path)
    with pytest.raises(FileNotFoundError):
        agent.resume(run_id="nope", stage="qa", edits={})


def test_approve_promotes_artifacts(tmp_path):
    agent = _FakeAgent(output_root=tmp_path)
    agent.run(request=_req(), run_id="r1")
    state = agent.approve(run_id="r1", approver="scott", project_slug="proj")
    assert state.stage == "done"
    assert (tmp_path / "_kernel" / "proj" / "primary.md").exists()


def test_drive_returns_immediately_when_stage_is_approval(tmp_path):
    """_drive must be a no-op when state is already at 'approval'."""
    from agentsuite.kernel.artifacts import ArtifactWriter
    from agentsuite.kernel.schema import RunState
    from agentsuite.kernel.state_store import StateStore

    agent = _FakeAgent(output_root=tmp_path)
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    store = StateStore(run_dir=writer.run_dir)
    state = RunState(run_id="r1", agent="fake", stage="approval", inputs=_req())
    store.save(state)
    result = agent._drive(state, writer, store, edits={})
    assert result.stage == "approval"


def test_drive_returns_immediately_when_stage_is_done(tmp_path):
    """_drive must be a no-op when state is already at 'done'."""
    from agentsuite.kernel.artifacts import ArtifactWriter
    from agentsuite.kernel.schema import RunState
    from agentsuite.kernel.state_store import StateStore

    agent = _FakeAgent(output_root=tmp_path)
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    store = StateStore(run_dir=writer.run_dir)
    state = RunState(run_id="r1", agent="fake", stage="done", inputs=_req())
    store.save(state)
    result = agent._drive(state, writer, store, edits={})
    assert result.stage == "done"


def test_cost_summary_provider_not_null(tmp_path):
    """CR-102: cost_summary.json must have non-null provider after a complete run.

    The fix in base_agent._drive passes ``provider=getattr(self.llm, 'name', None)``
    to CostTracker so that cost_summary.json reflects the concrete provider name
    rather than ``null``.
    """
    import json
    from agentsuite.agents.founder.agent import FounderAgent
    from agentsuite.agents.founder.input_schema import FounderAgentInput
    from agentsuite.kernel.schema import Constraints
    from agentsuite.llm.mock import _default_mock_for_cli

    llm = _default_mock_for_cli(provider_name="anthropic")
    agent = FounderAgent(output_root=tmp_path, llm=llm)
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="build creative ops for test startup",
        business_goal="test startup",
        constraints=Constraints(),
    )
    agent.run(request=inp, run_id="cr102-test")

    cost_summary_path = tmp_path / "runs" / "cr102-test" / "cost_summary.json"
    assert cost_summary_path.exists(), "cost_summary.json was not written"
    summary = json.loads(cost_summary_path.read_text(encoding="utf-8"))

    # CR-102: provider must not be null
    assert summary["provider"] == "anthropic", (
        f"Expected provider='anthropic', got {summary['provider']!r}"
    )
    # CR-102: model at top level reflects the mock's default model
    assert summary["model"] == "mock-1", (
        f"Expected model='mock-1', got {summary['model']!r}"
    )
    # Each stage entry that was executed should have a non-null model field
    for entry in summary.get("stages", []):
        assert entry["model"] is not None, (
            f"Stage '{entry['stage']}' has model=null in cost_summary.json (CR-102)"
        )


# --- ENG-005/UX-003: stage progress format --------------------------------


def test_stage_progress_omits_cost_when_zero(capsys):
    """ENG-005 Part B: zero total_usd produces no '$0.0000' in the progress line."""
    from agentsuite.kernel.base_agent import _emit_stage_progress
    _emit_stage_progress("intake", elapsed_s=0.2, total_usd=0.0)
    captured = capsys.readouterr()
    assert "[OK] intake complete  (0.2s)" in captured.err
    assert "$" not in captured.err


def test_stage_progress_includes_cost_when_nonzero(capsys):
    """ENG-005 Part B: nonzero total_usd appears as '$X.XXXX' in the progress line."""
    from agentsuite.kernel.base_agent import _emit_stage_progress
    _emit_stage_progress("extract", elapsed_s=1.5, total_usd=0.0123)
    captured = capsys.readouterr()
    assert "[OK] extract complete  (1.5s, $0.0123)" in captured.err


def test_stage_progress_cost_warning_emitted_once(tmp_path):
    """ENG-005 Part A: warning is written to stderr the first time the soft cap is crossed."""
    import io
    import sys

    # Build an agent that accumulates enough cost to trigger the soft-warn cap
    # during the intake stage.
    from agentsuite.kernel.base_agent import BaseAgent, StageHandler
    from agentsuite.kernel.cost import CostCap, CostTracker
    from agentsuite.kernel.qa import QARubric, RubricDimension
    from agentsuite.kernel.schema import AgentRequest, Constraints, Cost
    from agentsuite.kernel.artifacts import ArtifactWriter
    from agentsuite.kernel.state_store import StateStore

    class _CostlyAgent(BaseAgent):
        name = "costly"
        qa_rubric = QARubric(
            dimensions=[RubricDimension(name="ok", question="?")],
            pass_threshold=5.0,
        )

        def stage_handlers(self) -> dict[str, StageHandler]:
            def intake(state, ctx):
                # Exceed the soft-warn cap (1.0 USD default)
                ctx.cost_tracker.add(Cost(usd=1.5))
                return state.model_copy(update={"stage": "extract"})

            def extract(state, ctx):
                return state.model_copy(update={"stage": "spec"})

            def spec(state, ctx):
                ctx.writer.write("primary.md", "x", kind="spec", stage="spec")
                return state.model_copy(update={"stage": "execute"})

            def execute(state, ctx):
                return state.model_copy(update={"stage": "qa"})

            def qa(state, ctx):
                return state.model_copy(update={"stage": "approval"})

            return {
                "intake": intake,
                "extract": extract,
                "spec": spec,
                "execute": execute,
                "qa": qa,
            }

    agent = _CostlyAgent(output_root=tmp_path)
    req = AgentRequest(
        agent_name="costly",
        role_domain="test",
        user_request="x",
        constraints=Constraints(),
    )

    buf = io.StringIO()
    old_stderr = sys.stderr
    sys.stderr = buf
    try:
        agent.run(request=req, run_id="warn-test")
    finally:
        sys.stderr = old_stderr

    output = buf.getvalue()
    assert "Warning: cost cap approaching" in output
    assert "$1.5000" in output
    # Warning must appear exactly once (not repeated on every subsequent stage)
    assert output.count("Warning: cost cap approaching") == 1
