"""MCP tool wrappers for the Founder agent."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import Field

from agentsuite.agents._common import require_kernel_dir, require_run_dir
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.kernel.approval import RevisionRequired
from agentsuite.kernel.schema import Constraints, RunState, Stage
from agentsuite.kernel.state_store import RunStateSchemaVersionError, StateStore
from agentsuite.mcp_models import ApprovalResult, RunResult, RunSummary

_log = logging.getLogger(__name__)


class FounderRunRequest(FounderAgentInput):
    """MCP-facing input for founder_run. Adds optional run_id and supplies sane defaults
    for AgentRequest fields that the harness shouldn't have to think about."""

    run_id: str | None = None
    agent_name: str = "founder"
    role_domain: str = "creative-ops"
    user_request: str = ""
    constraints: Constraints = Field(default_factory=Constraints)


def _now_id() -> str:
    """Generate a UTC-timestamp run id like ``run-20260426-123456-789012``."""
    return "run-" + datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _summary_from_state(state: RunState) -> str:
    parts = [f"agent={state.agent}", f"stage={state.stage}"]
    if state.requires_revision:
        parts.append("revision_required")
    if state.open_questions:
        parts.append(f"{len(state.open_questions)} open questions")
    parts.append(f"cost=${state.cost_so_far.usd:.4f}")
    return "; ".join(parts)


def _result_from_state(state: RunState, run_dir: Path) -> RunResult:
    primary = run_dir / "brand-system.md"
    status = "awaiting_approval"
    if state.stage == "done":
        status = "done"
    elif state.requires_revision:
        status = "needs_revision"
    return RunResult(
        run_id=state.run_id,
        status=status,  # type: ignore[arg-type]
        primary_path=str(primary),
        summary=_summary_from_state(state),
        open_questions=state.open_questions,
        requires_revision=state.requires_revision,
        cost_usd=state.cost_so_far.usd,
    )


def register_tools(
    server: Any,
    agent_class: Callable[[], Any],
    output_root_fn: Callable[[], Path],
    expose_stages: bool,
) -> None:
    """Register the 5 default Founder MCP tools (and 5 advanced stage tools if enabled)."""

    def founder_run(request: FounderRunRequest) -> RunResult:
        run_id = request.run_id or _now_id()
        agent = agent_class()
        # Coerce MCP request into FounderAgentInput
        founder_input = FounderAgentInput(**request.model_dump(exclude={"run_id"}))
        state = agent.run(request=founder_input, run_id=run_id)
        run_dir = output_root_fn() / "runs" / run_id
        return _result_from_state(state, run_dir)

    def founder_resume(run_id: str, stage: Stage, edits: dict[str, Any] | None = None) -> RunResult:
        agent = agent_class()
        state = agent.resume(run_id=run_id, stage=stage, edits=edits or {})
        run_dir = require_run_dir(output_root_fn, run_id)
        return _result_from_state(state, run_dir)

    def founder_approve(run_id: str, approver: str, project_slug: str) -> ApprovalResult | dict:
        agent = agent_class()
        try:
            state = agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
        except RevisionRequired as e:
            run_dir = output_root_fn() / "runs" / run_id
            return {
                "error": "revision_required",
                "message": str(e),
                "qa_report_path": str(run_dir / "qa_report.md"),
                "action": "Review qa_report.md and re-run the agent to address QA feedback before approving.",
            }
        kernel_dir = require_kernel_dir(output_root_fn, project_slug)
        promoted = [
            str(p.relative_to(output_root_fn()))
            for p in kernel_dir.rglob("*")
            if p.is_file()
        ]
        return ApprovalResult(
            run_id=run_id,
            status="done",
            promoted_paths=promoted,
            approved_at=state.approved_at or datetime.now(tz=timezone.utc),
            approved_by=approver,
        )

    def founder_get_status(run_id: str) -> RunState:
        run_dir = require_run_dir(output_root_fn, run_id)
        try:
            state = StateStore(run_dir=run_dir).load()
        except RunStateSchemaVersionError as exc:
            raise ValueError(
                f"run_id {run_id!r} uses a pre-v0.9 schema — "
                f"delete the run directory and re-run."
            ) from exc
        if state is None:
            raise FileNotFoundError(f"No state file for run_id={run_id}")
        return state

    def founder_list_runs(project_slug: str | None = None) -> list[RunSummary]:
        runs_root = output_root_fn() / "runs"
        if not runs_root.exists():
            return []
        out: list[RunSummary] = []
        for d in sorted(runs_root.iterdir()):
            if not d.is_dir():
                continue
            try:
                state = StateStore(run_dir=d).load()
            except RunStateSchemaVersionError:
                _log.warning("Skipping pre-v0.9 run dir %s", d.name)
                continue
            if state is None or state.agent != "founder":
                continue
            if project_slug is not None:
                run_slug = getattr(state.inputs, "project_slug", None)
                if run_slug != project_slug:
                    continue
            out.append(RunSummary(
                run_id=state.run_id,
                agent=state.agent,
                stage=state.stage,
                started_at=state.started_at,
                cost_usd=state.cost_so_far.usd,
            ))
        return out

    server.add_tool("agentsuite_founder_run", founder_run)
    server.add_tool("agentsuite_founder_resume", founder_resume)
    server.add_tool("agentsuite_founder_approve", founder_approve)
    server.add_tool("agentsuite_founder_get_status", founder_get_status)
    server.add_tool("agentsuite_founder_list_runs", founder_list_runs)

    if expose_stages:
        def _stage_tool(stage: Stage):  # type: ignore[no-untyped-def]
            def runner(run_id: str) -> RunResult:
                agent = agent_class()
                state = agent.resume(run_id=run_id, stage=stage, edits={})
                run_dir = require_run_dir(output_root_fn, run_id)
                return _result_from_state(state, run_dir)

            return runner

        server.add_tool("agentsuite_founder_stage_intake", _stage_tool("intake"))
        server.add_tool("agentsuite_founder_stage_extract", _stage_tool("extract"))
        server.add_tool("agentsuite_founder_stage_spec", _stage_tool("spec"))
        server.add_tool("agentsuite_founder_stage_execute", _stage_tool("execute"))
        server.add_tool("agentsuite_founder_stage_qa", _stage_tool("qa"))
