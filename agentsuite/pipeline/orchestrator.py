"""Pipeline orchestrator — drives agents sequentially with approval gates."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from agentsuite.pipeline.input_resolver import get_input_class, resolve_agent_input
from agentsuite.pipeline.schema import PipelineState, PipelineStepState
from agentsuite.pipeline.state_store import PipelineNotFound, PipelineStateStore

ProgressCallback = Callable[[str, PipelineStepState, PipelineState], None]


class PipelineOrchestrator:
    def __init__(self, output_root: Path) -> None:
        self.output_root = Path(output_root)
        self.pipelines_root = self.output_root / "pipelines"

    def run(
        self,
        *,
        agents: list[str],
        project_slug: str,
        business_goal: str,
        inputs_dir: Path | None = None,
        agent_extras: dict[str, dict[str, Any]] | None = None,
        pipeline_id: str | None = None,
        auto_approve: bool = False,
        llm: Any | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> PipelineState:
        """Start a new pipeline. Returns state at awaiting_approval or done."""
        if not agents:
            raise ValueError("agents list must not be empty")
        pid = pipeline_id or (
            f"pipeline-{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%S')}"
            f"-{uuid.uuid4().hex[:6]}"
        )
        steps = [PipelineStepState(agent=a, run_id=f"{pid}-{a}") for a in agents]
        state = PipelineState(
            pipeline_id=pid,
            project_slug=project_slug,
            business_goal=business_goal,
            agents=agents,
            steps=steps,
            auto_approve=auto_approve,
            inputs_dir=str(inputs_dir) if inputs_dir else None,
            agent_extras=agent_extras or {},
        )
        store = PipelineStateStore(self.pipelines_root, pid)
        store.save(state)
        return self._drive(state, store, llm=llm, on_progress=on_progress)

    def approve(
        self,
        *,
        pipeline_id: str,
        approver: str,
        llm: Any | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> PipelineState:
        """Approve current awaiting step, promote artifacts, advance pipeline."""
        store = PipelineStateStore(self.pipelines_root, pipeline_id)
        state = store.load()
        if state.status != "awaiting_approval":
            raise ValueError(
                f"Pipeline {pipeline_id!r} is {state.status!r}, not 'awaiting_approval'"
            )
        step = state.steps[state.current_step_index]
        self._approve_step(step, state=state, approver=approver, llm=llm)
        step.status = "done"
        state.current_step_index += 1

        if state.current_step_index >= len(state.steps):
            state.status = "done"
            state.updated_at = datetime.now(tz=timezone.utc)
            store.save(state)
            return state

        state.status = "running"
        store.save(state)
        return self._drive(state, store, llm=llm, on_progress=on_progress)

    def status(self, *, pipeline_id: str) -> PipelineState:
        """Return current pipeline state."""
        return PipelineStateStore(self.pipelines_root, pipeline_id).load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _drive(
        self,
        state: PipelineState,
        store: PipelineStateStore,
        *,
        llm: Any | None,
        on_progress: ProgressCallback | None = None,
    ) -> PipelineState:
        from agentsuite.agents.registry import default_registry
        registry = default_registry()
        inputs_dir = Path(state.inputs_dir) if state.inputs_dir else None

        while state.current_step_index < len(state.steps):
            step = state.steps[state.current_step_index]
            step.status = "running"
            state.status = "running"
            state.updated_at = datetime.now(tz=timezone.utc)
            store.save(state)

            if on_progress:
                on_progress("agent_start", step, state)

            agent_name = step.agent
            agent_class = registry.get_class(agent_name)
            agent = (
                agent_class(output_root=self.output_root, llm=llm)
                if llm is not None
                else agent_class(output_root=self.output_root)
            )

            extras = state.agent_extras.get(agent_name, {})
            input_kwargs = resolve_agent_input(
                agent_name,
                business_goal=state.business_goal,
                project_slug=state.project_slug,
                inputs_dir=inputs_dir,
                agent_extras=extras,
            )
            inp = get_input_class(agent_name)(**input_kwargs)
            run_state = agent.run(request=inp, run_id=step.run_id)

            step.cost_usd = run_state.cost_so_far.usd
            state.total_cost_usd = sum(s.cost_usd for s in state.steps)

            if state.auto_approve:
                self._approve_step(step, state=state, approver="pipeline", llm=llm)
                step.status = "done"
                if on_progress:
                    on_progress("agent_done", step, state)
                state.current_step_index += 1
                state.updated_at = datetime.now(tz=timezone.utc)
                store.save(state)
            else:
                step.status = "awaiting_approval"
                state.status = "awaiting_approval"
                state.updated_at = datetime.now(tz=timezone.utc)
                store.save(state)
                if on_progress:
                    on_progress("agent_waiting", step, state)
                return state

        state.status = "done"
        state.updated_at = datetime.now(tz=timezone.utc)
        store.save(state)
        return state

    def _approve_step(
        self,
        step: PipelineStepState,
        *,
        state: PipelineState,
        approver: str,
        llm: Any | None = None,
    ) -> None:
        from agentsuite.agents.registry import default_registry
        agent_class = default_registry().get_class(step.agent)
        agent = (
            agent_class(output_root=self.output_root, llm=llm)
            if llm is not None
            else agent_class(output_root=self.output_root)
        )
        agent.approve(
            run_id=step.run_id,
            approver=approver,
            project_slug=state.project_slug,
        )
