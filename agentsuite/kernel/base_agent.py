"""Abstract base agent with persisted five-stage pipeline (intake, extract, spec, execute, qa) with a separate approval gate."""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, cast

from agentsuite.kernel.approval import ApprovalGate
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.qa import QARubric
from agentsuite.kernel.schema import AgentRequest, Cost, RunState, Stage
from agentsuite.kernel.state_store import StateStore

_log = logging.getLogger(__name__)

PIPELINE_ORDER: list[Stage] = ["intake", "extract", "spec", "execute", "qa"]


def stage_to_status(stage: str) -> str:
    """Map internal stage names to user-facing status values."""
    if stage == "approval":
        return "awaiting_approval"
    return stage


def _emit_stage_progress(stage: Stage, elapsed_s: float, total_usd: float) -> None:
    """Emit one line of stage-completion progress to stderr.

    Silenced when ``AGENTSUITE_QUIET`` is set (the CLI's ``--quiet`` flag
    exports this). Always writes to ``sys.stderr`` so the CLI's JSON stdout
    stays clean for shell-piping. Never raises.

    The cost portion is omitted when *total_usd* is zero (e.g. Ollama runs)
    so the line stays clean: ``[OK] intake complete  (0.2s)`` rather than
    ``[OK] intake complete  (0.2s, $0.0000)``.
    """
    if os.environ.get("AGENTSUITE_QUIET", "").lower() in {"1", "true", "yes"}:
        return
    cost_str = f", ${total_usd:.4f}" if total_usd > 0 else ""
    line = f"[OK] {stage} complete  ({elapsed_s:.1f}s{cost_str})"
    try:
        sys.stderr.write(line + chr(10))
        sys.stderr.flush()
    except Exception:
        pass


@dataclass
class AgentCLISpec:
    """Describes how an agent is exposed via the CLI."""
    cli_name: str            # typer subcommand name (e.g. "trust-risk")
    help: str                # typer help text
    run_fn: Callable[..., None]  # the run command function (built by the agent module)
    agent_class: type        # the concrete BaseAgent subclass
    primary_artifact: str    # filename for the run output summary line
    agent_name: str = ""     # the agent's state.agent value (defaults to cli_name)
    has_list_runs: bool = False  # whether to add a list-runs subcommand
    next_step_hint: str = ""  # UX-202: hint emitted to stderr after run completes


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
        from agentsuite.kernel.identifiers import validate_run_id
        run_dir = self.output_root / "runs" / validate_run_id(run_id)
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
        # Runs already at "approval" or "done" are terminal — return as-is.
        # Without this guard, a non-pipeline stage falls through to start_idx=0
        # and silently restarts from intake.
        if state.stage in ("approval", "done"):
            return state
        handlers = self.stage_handlers()
        cost_tracker = CostTracker(
            run_id=state.run_id,
            agent=state.agent,
            provider=getattr(getattr(self, "llm", None), "name", None),
        )
        cost_summary_path = writer.run_dir / "cost_summary.json"
        # Resume idempotency (ADR-0007): when resuming a previously-crashed
        # run, carry forward state.cost_so_far so cap enforcement reflects
        # multi-attempt total spend, and restore per-stage breakdown from
        # the prior cost_summary.json so the final report shows the full
        # history rather than just the resumed-segment costs. Failures to
        # parse the prior file are non-fatal: the carried total is still
        # correct from state.cost_so_far.
        if state.cost_so_far.usd > 0 or state.cost_so_far.input_tokens > 0:
            cost_tracker.total = state.cost_so_far
            if cost_summary_path.exists():
                try:
                    prior = json.loads(cost_summary_path.read_text(encoding="utf-8"))
                    for entry in prior.get("stages", []):
                        stage_name = cast(Stage, entry["stage"])
                        cost_tracker.per_stage[stage_name] = Cost(
                            input_tokens=entry["input_tokens"],
                            output_tokens=entry["output_tokens"],
                            usd=entry["cost_usd"],
                            model=entry.get("model"),
                        )
                except (OSError, json.JSONDecodeError, KeyError, TypeError):
                    pass
        ctx = StageContext(writer=writer, cost_tracker=cost_tracker, edits=edits)
        start_idx = PIPELINE_ORDER.index(state.stage) if state.stage in PIPELINE_ORDER else 0
        for stage in PIPELINE_ORDER[start_idx:]:
            if stage not in handlers:
                raise NotImplementedError(f"Agent {self.name} missing handler for stage '{stage}'")
            cost_tracker.current_stage = stage
            stage_start = time.monotonic()
            warned_before = cost_tracker.warned
            try:
                state = handlers[stage](state, ctx)
                state.artifacts = writer.refs()
                state.cost_so_far = cost_tracker.total
                store.save(state)
                # Persist cost_summary.json after every successful stage so a
                # crashed run still leaves an authoritative cost record on disk.
                cost_tracker.save_summary(cost_summary_path)
                # ENG-005/UX-003: surface cost warning to stderr the first time
                # the soft cap is crossed so operators see it immediately.
                if cost_tracker.warned and not warned_before:
                    try:
                        sys.stderr.write(
                            f"Warning: cost cap approaching. "
                            f"Current spend: ${cost_tracker.total.usd:.4f}\n"
                        )
                        sys.stderr.flush()
                    except Exception:  # noqa: BLE001 — defensive
                        pass
                # UX-006/QA-005: emit one stderr line per completed stage so
                # the CLI does not appear hung during long LLM phases.
                _emit_stage_progress(stage, time.monotonic() - stage_start, state.cost_so_far.usd)
                _log.debug("[OK] %s complete", stage)
            except Exception:
                state.cost_so_far = cost_tracker.total
                store.save(state)
                # Best-effort partial summary on failure; never mask the
                # original exception.
                try:
                    cost_tracker.save_summary(cost_summary_path)
                except Exception:  # noqa: BLE001 — defensive
                    pass
                raise
            if state.stage == "approval":
                break
        return state
