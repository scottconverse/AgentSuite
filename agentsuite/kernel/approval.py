"""Human approval gate."""
from __future__ import annotations

from datetime import datetime, timezone

from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.state_store import StateStore


class RunNotFound(RuntimeError):
    """Raised when approve() is called but no state file exists for the run."""


class NotAtApprovalStage(RuntimeError):
    """Raised when approve() is called but run is not at the approval stage."""


class RevisionRequired(RuntimeError):
    """Raised when approve() is called but QA flagged the run as needing revision."""


class ApprovalGate:
    """Gate that promotes run artifacts and marks the run done on human approval."""

    def __init__(self, state_store: StateStore, writer: ArtifactWriter) -> None:
        self.state_store = state_store
        self.writer = writer

    def approve(self, *, approver: str, project_slug: str) -> RunState:
        """Promote artifacts to ``_kernel/<slug>/`` and mark the run done.

        Raises ``RunNotFound`` if no state file exists yet.
        Raises ``NotAtApprovalStage`` if the run is not currently at the
        ``approval`` stage.
        """
        state = self.state_store.load()
        if state is None:
            raise RunNotFound(f"No state file at {self.state_store.path}")
        if state.stage != "approval":
            raise NotAtApprovalStage(
                f"Run is at stage '{state.stage}', not 'approval'"
            )
        if state.requires_revision:
            raise RevisionRequired(
                "QA flagged this run as requiring revision. "
                "Address the QA feedback and re-run before approving."
            )
        self.writer.promote(project_slug=project_slug)
        state.stage = "done"
        state.approved_at = datetime.now(tz=timezone.utc)
        state.approved_by = approver
        self.state_store.save(state)
        return state
