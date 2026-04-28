"""EngineeringAgent — wires the kernel BaseAgent to engineering stage handlers."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC
from agentsuite.agents.engineering.stages.execute import execute_stage
from agentsuite.agents.engineering.stages.extract import extract_stage
from agentsuite.agents.engineering.stages.intake import intake_stage
from agentsuite.agents.engineering.stages.qa import qa_stage
from agentsuite.agents.engineering.stages.spec import spec_stage
from agentsuite.kernel.base_agent import AgentCLISpec, BaseAgent, StageContext, StageHandler
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


def build_cli_spec() -> AgentCLISpec:
    """Return the CLI spec for the Engineering agent."""
    import json
    import typer

    def run_cmd(
        system_name: str = typer.Option(..., help="Name of the system being designed/documented"),
        problem_domain: str = typer.Option(..., help="What problem does this system solve"),
        tech_stack: str = typer.Option(..., help="e.g. 'Python + FastAPI + PostgreSQL + Redis'"),
        scale_requirements: str = typer.Option(..., help="e.g. '10k RPM, 99.9% uptime, <200ms p99'"),
        project_slug: str | None = typer.Option(None, "--project-slug", help="Project slug for _kernel/ promotion"),
        inputs_dir: Path | None = typer.Option(None, help="Dir with existing docs, ADRs, runbooks"),
        run_id: str | None = typer.Option(None, help="Run ID (default: auto-generated timestamp+uuid)"),
        force: bool = typer.Option(False, "--force", help="Overwrite existing run directory if it exists"),
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
        rid = run_id or f"run-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:6]}"
        run_dir = Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite")) / "runs" / rid
        if run_dir.exists() and not force:
            typer.echo(f"Error: run '{rid}' already exists. Use --force to overwrite.", err=True)
            raise typer.Exit(1)
        result = agent.run(request=inp, run_id=rid)
        typer.echo(json.dumps({
            "run_id": result.run_id,
            "primary_path": str(_output_root() / "runs" / result.run_id / "architecture-decision-record.md"),
            "status": result.stage,
        }, indent=2))

    return AgentCLISpec(
        cli_name="engineering",
        help="Engineering Agent — generates architecture, API spec, runbook, and related artifacts.",
        run_fn=run_cmd,
        agent_class=EngineeringAgent,
        primary_artifact="architecture-decision-record.md",
        agent_name="engineering",
    )
