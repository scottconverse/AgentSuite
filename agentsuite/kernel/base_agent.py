"""Abstract base agent with persisted five-stage pipeline (intake, extract, spec, execute, qa) with a separate approval gate."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from agentsuite.kernel.approval import ApprovalGate
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.qa import QARubric
from agentsuite.kernel.schema import AgentRequest, RunState, Stage
from agentsuite.kernel.state_store import StateStore


PIPELINE_ORDER: list[Stage] = ["intake", "extract", "spec", "execute", "qa"]


@dataclass
class StageContext:
    """Per-call context passed to every stage handler."""
    writer: ArtifactWriter
    cost_tracker: CostTracker
    edits: dict[str, Any]


StageHandler = Callable[[RunState, StageContext], RunState]


class BaseAgent(ABC):
    """Abstract base for all AgentSuite agents.

    Concrete subclasses supply ``stage_handlers()`` (one handler per stage in
    ``PIPELINE_ORDER``) and a ``qa_rubric``. The base class owns state
    persistence, artifact tracking, cost accumulation, and the run / resume /
    approve cycle.
    """
    name: str = "base"
    qa_rubric: QARubric

    def __init__(self, output_root: Path) -> None:
        self.output_root = Path(output_root)

    @abstractmethod
    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return a mapping {stage_name: handler} for all stages in PIPELINE_ORDER."""

    def run(self, *, request: AgentRequest, run_id: str) -> RunState:
        """Start a new run. Drives all stages until approval gate or completion."""
        writer = ArtifactWriter(output_root=self.output_root, run_id=run_id)
        store = StateStore(run_dir=writer.run_dir)
        state = RunState(run_id=run_id, agent=self.name, inputs=request)
        store.save(state)
        return self._drive(state, writer, store, edits={})

    def resume(self, *, run_id: str, stage: Stage, edits: dict[str, Any]) -> RunState:
        """Resume an existing run from the named stage with optional edits.

        Raises ``FileNotFoundError`` if the run dir or state file is missing.
        """
        run_dir = self.output_root / "runs" / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run not found: {run_dir}")
        writer = ArtifactWriter(output_root=self.output_root, run_id=run_id)
        store = StateStore(run_dir=writer.run_dir)
        state = store.load()
        if state is None:
            raise FileNotFoundError(f"State missing: {store.path}")
        state.stage = stage
        store.save(state)
        return self._drive(state, writer, store, edits=edits)

    def approve(self, *, run_id: str, approver: str, project_slug: str) -> RunState:
        """Approve a run: promote artifacts to ``_kernel/<slug>/`` and mark done."""
        writer = ArtifactWriter(output_root=self.output_root, run_id=run_id)
        store = StateStore(run_dir=writer.run_dir)
        gate = ApprovalGate(state_store=store, writer=writer)
        return gate.approve(approver=approver, project_slug=project_slug)

    def _drive(
        self,
        state: RunState,
        writer: ArtifactWriter,
        store: StateStore,
        edits: dict[str, Any],
    ) -> RunState:
        handlers = self.stage_handlers()
        cost_tracker = CostTracker()
        ctx = StageContext(writer=writer, cost_tracker=cost_tracker, edits=edits)
        start_idx = PIPELINE_ORDER.index(state.stage) if state.stage in PIPELINE_ORDER else 0
        for stage in PIPELINE_ORDER[start_idx:]:
            if stage not in handlers:
                raise NotImplementedError(f"Agent {self.name} missing handler for stage '{stage}'")
            state = handlers[stage](state, ctx)
            state.artifacts = writer.refs()
            state.cost_so_far = cost_tracker.total
            store.save(state)
            if state.stage == "approval":
                break
        return state
