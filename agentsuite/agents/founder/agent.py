"""FounderAgent — wires the kernel BaseAgent to founder stage handlers."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.execute import execute_stage
from agentsuite.agents.founder.stages.extract import extract_stage
from agentsuite.agents.founder.stages.intake import intake_stage
from agentsuite.agents.founder.stages.qa import qa_stage
from agentsuite.agents.founder.stages.spec import spec_stage
from agentsuite.kernel.base_agent import AgentCLISpec, BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class FounderAgent(BaseAgent):
    """Concrete agent that builds reusable creative-ops artifacts for founders.

    Subclasses BaseAgent. Wires the 5 founder stage handlers into the kernel's
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "founder"
    qa_rubric = FOUNDER_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider

            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-cast inputs.

        After JSON round-trip on resume, state.inputs may be an AgentRequest instance
        lacking FounderAgentInput-specific fields. Re-validate from its dump so handlers
        see the correct shape.
        """
        from agentsuite.agents.founder.input_schema import FounderAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, FounderAgentInput):
                    state = state.model_copy(update={
                        "inputs": FounderAgentInput.model_validate(state.inputs.model_dump())
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
    """Return the CLI spec for the Founder agent."""
    import json
    import typer

    def run_cmd(
        business_goal: str = typer.Option(..., help="Required business goal"),
        project_slug: str | None = typer.Option(None, help="Stable slug for `_kernel/` promotion"),
        inputs_dir: Path | None = typer.Option(None, help="Directory of source materials"),
        run_id: str | None = typer.Option(None, help="Run ID (default: auto-generated timestamp+uuid)"),
        force: bool = typer.Option(False, "--force", help="Overwrite existing run directory if it exists"),
    ) -> None:
        """Run the Founder agent end-to-end up to the approval gate."""
        from agentsuite.agents.founder.input_schema import FounderAgentInput
        from agentsuite.kernel.schema import Constraints
        from agentsuite.cli import _output_root, _resolve_llm_for_cli

        agent = FounderAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
        inp = FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request=f"build creative ops for {business_goal}",
            business_goal=business_goal,
            project_slug=project_slug,
            inputs_dir=inputs_dir,
            constraints=Constraints(),
        )
        rid = run_id or f"run-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:6]}"
        run_dir = Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite")) / "runs" / rid
        if run_dir.exists() and not force:
            typer.echo(f"Error: run '{rid}' already exists. Use --force to overwrite.", err=True)
            raise typer.Exit(1)
        state = agent.run(request=inp, run_id=rid)
        typer.echo(json.dumps({
            "run_id": state.run_id,
            "primary_path": str(_output_root() / "runs" / state.run_id / "brand-system.md"),
            "status": state.stage,
        }, indent=2))

    return AgentCLISpec(
        cli_name="founder",
        help="Founder agent commands",
        run_fn=run_cmd,
        agent_class=FounderAgent,
        primary_artifact="brand-system.md",
        agent_name="founder",
        next_step_hint="Next: agentsuite founder approve --latest --approver <your-name> --project-slug <slug>",
    )
