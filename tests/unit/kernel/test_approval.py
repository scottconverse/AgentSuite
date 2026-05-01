"""Unit tests for kernel.approval."""
import pytest

from agentsuite.kernel.approval import ApprovalGate, NotAtApprovalStage, RevisionRequired, RunNotFound
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
from agentsuite.kernel.state_store import StateStore


def _request() -> AgentRequest:
    return AgentRequest(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        constraints=Constraints(),
    )


def test_approve_at_approval_stage_marks_approved_and_promotes(tmp_path):
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write("brand-system.md", "content", kind="spec", stage="spec")
    state = RunState(run_id="r1", agent="founder", stage="approval", inputs=_request())
    store = StateStore(run_dir=writer.run_dir)
    store.save(state)
    gate = ApprovalGate(state_store=store, writer=writer)
    new_state = gate.approve(approver="scott", project_slug="testproj")
    assert new_state.stage == "done"
    assert new_state.approved_by == "scott"
    assert new_state.approved_at is not None
    assert (tmp_path / "_kernel" / "testproj" / "brand-system.md").exists()


def test_approve_outside_approval_stage_raises(tmp_path):
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    state = RunState(run_id="r1", agent="founder", stage="extract", inputs=_request())
    store = StateStore(run_dir=writer.run_dir)
    store.save(state)
    gate = ApprovalGate(state_store=store, writer=writer)
    with pytest.raises(NotAtApprovalStage):
        gate.approve(approver="scott", project_slug="testproj")


def test_approve_with_no_state_file_raises_run_not_found(tmp_path):
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    store = StateStore(run_dir=writer.run_dir)
    gate = ApprovalGate(state_store=store, writer=writer)
    with pytest.raises(RunNotFound):
        gate.approve(approver="scott", project_slug="testproj")


def test_approve_with_requires_revision_raises(tmp_path):
    """approve() must refuse when QA flagged requires_revision=True."""
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write("brand-system.md", "content", kind="spec", stage="spec")
    state = RunState(
        run_id="r1", agent="founder", stage="approval",
        inputs=_request(), requires_revision=True,
    )
    store = StateStore(run_dir=writer.run_dir)
    store.save(state)
    gate = ApprovalGate(state_store=store, writer=writer)
    with pytest.raises(RevisionRequired):
        gate.approve(approver="scott", project_slug="testproj")
    # Artifacts must NOT have been promoted
    assert not (tmp_path / "_kernel" / "testproj").exists()


def test_revision_required_message_includes_qa_scores_path(tmp_path):
    """RevisionRequired error message must include the path to qa_scores.json."""
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write("brand-system.md", "content", kind="spec", stage="spec")
    state = RunState(
        run_id="r1", agent="founder", stage="approval",
        inputs=_request(), requires_revision=True,
    )
    store = StateStore(run_dir=writer.run_dir)
    store.save(state)
    gate = ApprovalGate(state_store=store, writer=writer)
    with pytest.raises(RevisionRequired) as exc_info:
        gate.approve(approver="scott", project_slug="testproj")
    message = str(exc_info.value)
    assert "qa_scores.json" in message, f"Expected 'qa_scores.json' in error message, got: {message!r}"
