"""CIOAgent — wires the kernel BaseAgent to CIO stage handlers."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentsuite.agents.cio.rubric import CIO_RUBRIC
from agentsuite.agents.cio.stages.execute import execute_stage
from agentsuite.agents.cio.stages.extract import extract_stage
from agentsuite.agents.cio.stages.intake import intake_stage
from agentsuite.agents.cio.stages.qa import qa_stage
from agentsuite.agents.cio.stages.spec import spec_stage
from agentsuite.kernel.base_agent import AgentCLISpec, BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class CIOAgent(BaseAgent):
    """Concrete agent that produces CIO strategy and IT roadmap artifacts.

    Subclasses BaseAgent. Wires the 5 CIO stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "cio"
    qa_rubric = CIO_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see CIOAgentInput-specific fields.
        """
        from agentsuite.agents.cio.input_schema import CIOAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, CIOAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as organization_name. Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, CIOAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    elif isinstance(typed_inputs, dict):
                        state = state.model_copy(update={
                            "inputs": CIOAgentInput(**typed_inputs)
                        })
                    else:
                        state = state.model_copy(update={
                            "inputs": CIOAgentInput.model_validate(state.inputs.model_dump())
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
    """Return the CLI spec for the CIO agent."""
    import json
    import typer

    def run_cmd(
        organization_name: str = typer.Option(..., help="Name of the organization being assessed"),
        strategic_priorities: str = typer.Option(..., help="Top IT/digital strategic priorities"),
        it_maturity_level: str = typer.Option(..., help="e.g. 'Level 1 – Ad hoc', 'Level 3 – Defined'"),
        budget_context: str = typer.Option("", help="e.g. 'flat budget', '$5M annual IT capex'"),
        digital_initiatives: str = typer.Option("", help="Active or planned digital transformation programs"),
        regulatory_environment: str = typer.Option("", help="e.g. 'HIPAA, SOX, FedRAMP'"),
        it_docs_dir: Path | None = typer.Option(None, help="Dir with existing IT strategy, roadmap, or architecture docs"),
        run_id: str | None = typer.Option(None, help="Run ID (default: auto-generated timestamp+uuid)"),
        force: bool = typer.Option(False, "--force", help="Overwrite existing run directory if it exists"),
    ) -> None:
        """Run the CIO Agent pipeline."""
        from agentsuite.agents.cio.input_schema import CIOAgentInput
        from agentsuite.cli import _output_root, _resolve_llm_for_cli

        existing_it_docs: list[Path] = list(it_docs_dir.iterdir()) if it_docs_dir and it_docs_dir.is_dir() else []
        inp = CIOAgentInput(
            agent_name="cio",
            role_domain="cio-ops",
            user_request=f"Generate CIO strategy artifacts for {organization_name}",
            organization_name=organization_name,
            strategic_priorities=strategic_priorities,
            it_maturity_level=it_maturity_level,
            budget_context=budget_context,
            digital_initiatives=digital_initiatives,
            regulatory_environment=regulatory_environment,
            existing_it_docs=existing_it_docs,
        )
        agent = CIOAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
        rid = run_id or f"run-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:6]}"
        run_dir = Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite")) / "runs" / rid
        if run_dir.exists() and not force:
            typer.echo(f"Error: run '{rid}' already exists. Use --force to overwrite.", err=True)
            raise typer.Exit(1)
        result = agent.run(request=inp, run_id=rid)
        typer.echo(json.dumps({
            "run_id": result.run_id,
            "primary_path": str(_output_root() / "runs" / result.run_id / "it-strategy.md"),
            "status": result.stage,
        }, indent=2))

    return AgentCLISpec(
        cli_name="cio",
        help="CIO Agent — generates IT strategy, technology roadmap, vendor portfolio, and related artifacts.",
        run_fn=run_cmd,
        agent_class=CIOAgent,
        primary_artifact="it-strategy.md",
        agent_name="cio",
        has_list_runs=True,
        next_step_hint="Next: agentsuite cio approve --latest --approver <your-name> --project-slug <slug>",
    )
