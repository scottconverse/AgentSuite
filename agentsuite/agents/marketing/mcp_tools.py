"""MCP tool wrappers for the Marketing agent."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from agentsuite.agents._common import require_kernel_dir, require_run_dir
from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.kernel.schema import RunState, Stage
from agentsuite.kernel.state_store import StateStore
from agentsuite.mcp_models import ApprovalResult, RunResult, RunSummary


class MarketingRunRequest(MarketingAgentInput):
    """MCP-facing input for marketing_run. Adds optional run_id, supplies sane defaults."""

    run_id: str | None = None
    agent_name: str = "marketing"
    role_domain: str = "marketing-ops"
    user_request: str = "run marketing agent"


def _now_id() -> str:
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
    primary = run_dir / "campaign-brief.md"
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
    """Register the 5 default Marketing MCP tools (and 5 stage tools if expose_stages)."""

    def marketing_run(request: MarketingRunRequest) -> RunResult:
        run_id = request.run_id or _now_id()
        agent = agent_class()
        marketing_input = MarketingAgentInput(**request.model_dump(exclude={"run_id"}))
        state = agent.run(request=marketing_input, run_id=run_id)
        run_dir = output_root_fn() / "runs" / run_id
        return _result_from_state(state, run_dir)

    def marketing_resume(run_id: str, stage: Stage, edits: dict[str, Any] | None = None) -> RunResult:
        agent = agent_class()
        state = agent.resume(run_id=run_id, stage=stage, edits=edits or {})
        run_dir = require_run_dir(output_root_fn, run_id)
        return _result_from_state(state, run_dir)

    def marketing_approve(run_id: str, approver: str, project_slug: str) -> ApprovalResult:
        agent = agent_class()
        state = agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
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

    def marketing_get_status(run_id: str) -> RunState:
        run_dir = require_run_dir(output_root_fn, run_id)
        state = StateStore(run_dir=run_dir).load()
        if state is None:
            raise FileNotFoundError(f"No state file for run_id={run_id}")
        return state

    def marketing_list_runs(project_slug: str | None = None) -> list[RunSummary]:
        runs_root = output_root_fn() / "runs"
        if not runs_root.exists():
            return []
        out: list[RunSummary] = []
        for d in sorted(runs_root.iterdir()):
            if not d.is_dir():
                continue
            state = StateStore(run_dir=d).load()
            if state is None or state.agent != "marketing":
                continue
            out.append(RunSummary(
                run_id=state.run_id,
                agent=state.agent,
                stage=state.stage,
                started_at=state.started_at,
                cost_usd=state.cost_so_far.usd,
            ))
        return out

    server.add_tool("agentsuite_marketing_run", marketing_run)
    server.add_tool("agentsuite_marketing_resume", marketing_resume)
    server.add_tool("agentsuite_marketing_approve", marketing_approve)
    server.add_tool("agentsuite_marketing_get_status", marketing_get_status)
    server.add_tool("agentsuite_marketing_list_runs", marketing_list_runs)

    if expose_stages:
        def _stage_tool(stage: Stage) -> Any:
            def runner(run_id: str) -> RunResult:
                agent = agent_class()
                state = agent.resume(run_id=run_id, stage=stage, edits={})
                run_dir = require_run_dir(output_root_fn, run_id)
                return _result_from_state(state, run_dir)
            return runner

        server.add_tool("agentsuite_marketing_stage_intake", _stage_tool("intake"))
        server.add_tool("agentsuite_marketing_stage_extract", _stage_tool("extract"))
        server.add_tool("agentsuite_marketing_stage_spec", _stage_tool("spec"))
        server.add_tool("agentsuite_marketing_stage_execute", _stage_tool("execute"))
        server.add_tool("agentsuite_marketing_stage_qa", _stage_tool("qa"))
