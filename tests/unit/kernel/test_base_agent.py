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
