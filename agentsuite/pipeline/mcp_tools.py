"""MCP tools for pipeline orchestration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from agentsuite.pipeline.schema import PipelineState
from agentsuite.pipeline.state_store import PipelineNotFound


def register_pipeline_tools(
    server: Any,
    output_root_fn: Callable[[], Path],
) -> None:
    """Register agentsuite_pipeline_run/approve/status MCP tools."""
    from agentsuite.pipeline.orchestrator import PipelineOrchestrator

    def agentsuite_pipeline_run(
        agents: str,
        project_slug: str,
        business_goal: str,
        inputs_dir: str | None = None,
        agent_extras: dict[str, dict[str, Any]] | None = None,
        auto_approve: bool = False,
    ) -> dict[str, Any]:
        """Run a multi-agent pipeline. agents is comma-separated (e.g. 'founder,design,product')."""
        agent_list = [a.strip().replace("-", "_") for a in agents.split(",") if a.strip()]
        orch = PipelineOrchestrator(output_root=output_root_fn())
        try:
            state = orch.run(
                agents=agent_list,
                project_slug=project_slug,
                business_goal=business_goal,
                inputs_dir=Path(inputs_dir) if inputs_dir else None,
                agent_extras=agent_extras or {},
                auto_approve=auto_approve,
            )
        except ValueError as e:
            return {"error": str(e)}
        return _state_to_dict(state)

    def agentsuite_pipeline_approve(
        pipeline_id: str,
        approver: str,
    ) -> dict[str, Any]:
        """Approve the current awaiting step and advance the pipeline to the next agent."""
        orch = PipelineOrchestrator(output_root=output_root_fn())
        try:
            state = orch.approve(pipeline_id=pipeline_id, approver=approver)
        except PipelineNotFound:
            return {"error": f"Pipeline {pipeline_id!r} not found"}
        except ValueError as e:
            return {"error": str(e)}
        return _state_to_dict(state)

    def agentsuite_pipeline_status(pipeline_id: str) -> dict[str, Any]:
        """Return the current status of a pipeline run."""
        orch = PipelineOrchestrator(output_root=output_root_fn())
        try:
            state = orch.status(pipeline_id=pipeline_id)
        except PipelineNotFound:
            return {"error": f"Pipeline {pipeline_id!r} not found"}
        return _state_to_dict(state)

    server.add_tool("agentsuite_pipeline_run", agentsuite_pipeline_run)
    server.add_tool("agentsuite_pipeline_approve", agentsuite_pipeline_approve)
    server.add_tool("agentsuite_pipeline_status", agentsuite_pipeline_status)


def _state_to_dict(state: PipelineState) -> dict[str, Any]:
    return {
        "pipeline_id": state.pipeline_id,
        "status": state.status,
        "project_slug": state.project_slug,
        "agents": state.agents,
        "current_step": state.current_step_index,
        "total_steps": len(state.steps),
        "steps": [
            {
                "agent": s.agent,
                "run_id": s.run_id,
                "status": s.status,
                "cost_usd": s.cost_usd,
            }
            for s in state.steps
        ],
        "total_cost_usd": state.total_cost_usd,
    }
