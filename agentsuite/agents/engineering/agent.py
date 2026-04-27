"""EngineeringAgent — wires the kernel BaseAgent to engineering stage handlers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC
from agentsuite.agents.engineering.stages.execute import execute_stage
from agentsuite.agents.engineering.stages.extract import extract_stage
from agentsuite.agents.engineering.stages.intake import intake_stage
from agentsuite.agents.engineering.stages.qa import qa_stage
from agentsuite.agents.engineering.stages.spec import spec_stage
from agentsuite.kernel.base_agent import BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class EngineeringAgent(BaseAgent):
    """Concrete agent that produces engineering specification artifacts.

    Subclasses BaseAgent. Wires the 5 engineering stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "engineering"
    qa_rubric = ENGINEERING_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see EngineeringAgentInput-specific fields.
        """
        from agentsuite.agents.engineering.input_schema import EngineeringAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, EngineeringAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as system_name.  Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, EngineeringAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    else:
                        state = state.model_copy(update={
                            "inputs": EngineeringAgentInput.model_validate(state.inputs.model_dump())
                        })
                return handler(state, ctx)
            return runner

        return {
            "intake": _wrap(intake_stage),
            "extract": _wrap(extract_stage),
            "spec": _wrap(spec_stage),
            "execute": _wrap(execute_stage),
            "qa": _wrap(qa_stage),
        }


def build_cli_spec() -> "AgentCLISpec":  # noqa: F821
    """Return the CLI spec for the Engineering agent."""
    from agentsuite.kernel.base_agent import AgentCLISpec
    import json
    import typer

    def run_cmd(
        system_name: str = typer.Option(..., help="Name of the system being designed/documented"),
        problem_domain: str = typer.Option(..., help="What problem does this system solve"),
        tech_stack: str = typer.Option(..., help="e.g. 'Python + FastAPI + PostgreSQL + Redis'"),
        scale_requirements: str = typer.Option(..., help="e.g. '10k RPM, 99.9% uptime, <200ms p99'"),
        project_slug: str | None = typer.Option(None, "--project-slug", help="Project slug for _kernel/ promotion"),
        inputs_dir: Path | None = typer.Option(None, help="Dir with existing docs, ADRs, runbooks"),
        run_id: str | None = typer.Option(None, help="Run ID (auto-generated if omitted)"),
    ) -> None:
        """Run the Engineering Agent pipeline."""
        from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
        from agentsuite.cli import _output_root, _resolve_llm_for_cli

        inp = EngineeringAgentInput(
            agent_name="engineering",
            role_domain="engineering-ops",
            user_request=f"Generate engineering specs for {system_name}",
            system_name=system_name,
            problem_domain=problem_domain,
            tech_stack=tech_stack,
            scale_requirements=scale_requirements,
            inputs_dir=inputs_dir,
        )
        agent = EngineeringAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
        result = agent.run(request=inp, run_id=run_id or "run-cli")
        typer.echo(json.dumps({
            "run_id": result.run_id,
            "status": "awaiting_approval" if result.stage == "approval" else result.stage,
            "stage": result.stage,
            "system_name": system_name,
            "cost_usd": result.cost_so_far.usd,
        }, indent=2, default=str))

    return AgentCLISpec(
        cli_name="engineering",
        help="Engineering Agent — generates architecture, API spec, runbook, and related artifacts.",
        run_fn=run_cmd,
        agent_class=EngineeringAgent,
        primary_artifact="architecture-decision-record.md",
        agent_name="engineering",
    )
