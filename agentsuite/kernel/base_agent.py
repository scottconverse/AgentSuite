"""Abstract base agent with persisted five-stage pipeline (intake, extract, spec, execute, qa) with a separate approval gate."""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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

# K1: Human-readable labels for each stage in the pipeline.
_STAGE_LABELS: dict[str, str] = {
    "intake":   "Intake",
    "extract":  "Extraction",
    "spec":     "Specification",
    "execute":  "Execution",
    "qa":       "Quality review",
}

# K2: Protocol for progress callbacks — callable accepting a dict event.
ProgressCallback = Callable[[dict[str, Any]], None]


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


def _summarize_stage_output(stage_name: str, artifacts: list[Any]) -> str:
    """K1: Extract a short summary from stage artifacts for cross-stage context.

    Reads the first 500 words of the first text artifact for the given stage.
    Returns an empty string if no artifact is readable.
    """
    for ref in artifacts:
        path = getattr(ref, "path", None) or getattr(ref, "file_path", None)
        if path is None:
            continue
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            words = text.split()
            return " ".join(words[:500])
        except OSError:
            continue
    return ""


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
    """Per-call context passed to every stage handler.

    K1: ``cross_stage_context`` accumulates summaries from completed stages so
    each handler can optionally incorporate prior decisions into its prompt.
    The dict grows after each stage completes; keys are stage names, values
    are 500-word plain-text summaries of the primary artifact.
    """
    writer: ArtifactWriter
    cost_tracker: CostTracker
    edits: dict[str, Any]
    # K1: grows after each stage; keys are stage names, values are 500-word summaries
    cross_stage_context: dict[str, str] = field(default_factory=dict)


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

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        self.output_root = Path(output_root)

    @abstractmethod
    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return a mapping {stage_name: handler} for all stages in PIPELINE_ORDER."""

    def run(
        self,
        *,
        request: AgentRequest,
        run_id: str,
        progress_callback: ProgressCallback | None = None,
    ) -> RunState:
        """Start a new run. Drives all stages until approval gate or completion.

        K2: ``progress_callback`` is called with structured event dicts at key
        checkpoints within each stage.  Signature: ``callback(event: dict) -> None``.

        Event types emitted:
          - ``{type: "stage_progress", stage, step, total, message}`` — at stage
            start and stage complete.
          - ``{type: "context_update", stage, summary}`` — after each stage,
            with the first 300 chars of the stage's primary artifact (K1).

        The caller should never block inside the callback; it is called
        synchronously on the agent thread and exceptions are silently swallowed.
        """
        writer = ArtifactWriter(output_root=self.output_root, run_id=run_id)
        store = StateStore(run_dir=writer.run_dir)
        state = RunState(run_id=run_id, agent=self.name, inputs=request)
        store.save(state)
        return self._drive(state, writer, store, edits={}, progress_callback=progress_callback)

    def resume(
        self,
        *,
        run_id: str,
        stage: Stage,
        edits: dict[str, Any],
        progress_callback: ProgressCallback | None = None,
    ) -> RunState:
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
        return self._drive(state, writer, store, edits=edits, progress_callback=progress_callback)

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
        progress_callback: ProgressCallback | None = None,
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

        # K1: cross-stage context accumulator — grows as stages complete
        cross_stage_context: dict[str, str] = {}

        ctx = StageContext(
            writer=writer,
            cost_tracker=cost_tracker,
            edits=edits,
            cross_stage_context=cross_stage_context,
        )
        start_idx = PIPELINE_ORDER.index(state.stage) if state.stage in PIPELINE_ORDER else 0
        total_stages = len(PIPELINE_ORDER)
        for step_idx, stage in enumerate(PIPELINE_ORDER[start_idx:], start=start_idx):
            if stage not in handlers:
                raise NotImplementedError(f"Agent {self.name} missing handler for stage '{stage}'")
            cost_tracker.current_stage = stage
            stage_start = time.monotonic()
            warned_before = cost_tracker.warned

            # K2: emit stage_start event
            if progress_callback is not None:
                try:
                    progress_callback({
                        "type": "stage_progress",
                        "stage": stage,
                        "step": step_idx + 1,
                        "total": total_stages,
                        "message": f"Starting {_STAGE_LABELS.get(stage, stage)}",
                    })
                except Exception:  # noqa: BLE001
                    pass

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
                    except Exception:  # noqa: BLE001
                        pass
                # UX-006/QA-005: emit one stderr line per completed stage so
                # the CLI does not appear hung during long LLM phases.
                _emit_stage_progress(stage, time.monotonic() - stage_start, state.cost_so_far.usd)
                _log.debug("[OK] %s complete", stage)

                # K1: summarize this stage's artifacts into cross-stage context
                summary = _summarize_stage_output(stage, list(state.artifacts))
                if summary:
                    cross_stage_context[stage] = summary
                    # K2: emit context_update so callers can surface it in UI
                    if progress_callback is not None:
                        try:
                            progress_callback({
                                "type": "context_update",
                                "stage": stage,
                                "summary": summary[:300],
                            })
                        except Exception:  # noqa: BLE001
                            pass

                # K2: emit stage_complete event
                if progress_callback is not None:
                    try:
                        progress_callback({
                            "type": "stage_progress",
                            "stage": stage,
                            "step": step_idx + 1,
                            "total": total_stages,
                            "message": f"{_STAGE_LABELS.get(stage, stage)} complete",
                        })
                    except Exception:  # noqa: BLE001
                        pass

            except Exception:
                state.cost_so_far = cost_tracker.total
                store.save(state)
                # Best-effort partial summary on failure; never mask the
                # original exception.
                try:
                    cost_tracker.save_summary(cost_summary_path)
                except Exception:  # noqa: BLE001
                    pass
                raise
            if state.stage == "approval":
                break
        return state
