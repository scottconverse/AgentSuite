"""DesignAgent — wires the kernel BaseAgent to design stage handlers."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentsuite.agents.design.rubric import DESIGN_RUBRIC
from agentsuite.agents.design.stages.execute import execute_stage
from agentsuite.agents.design.stages.extract import extract_stage
from agentsuite.agents.design.stages.intake import intake_stage
from agentsuite.agents.design.stages.qa import qa_stage
from agentsuite.agents.design.stages.spec import spec_stage
from agentsuite.kernel.base_agent import AgentCLISpec, BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class DesignAgent(BaseAgent):
    """Concrete agent that produces design specification artifacts and asset briefs.

    Subclasses BaseAgent. Wires the 5 design stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "design"
    qa_rubric = DESIGN_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see DesignAgentInput-specific fields.
        """
        from agentsuite.agents.design.input_schema import DesignAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, DesignAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as campaign_goal.  Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, DesignAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    else:
                        state = state.model_copy(update={
                            "inputs": DesignAgentInput.model_validate(state.inputs.model_dump())
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
    """Return the CLI spec for the Design agent."""
    import json
    import typer

    def run_cmd(
        target_audience: str = typer.Option(..., help="Target audience for the campaign"),
        campaign_goal: str = typer.Option(..., help="Campaign goal"),
        channel: str = typer.Option("web", help="Output channel: web/social/email/print/video/deck/other"),
        project_slug: str | None = typer.Option(None, help="Stable slug for `_kernel/` promotion"),
        inputs_dir: Path | None = typer.Option(None, help="Directory of brand source materials"),
        run_id: str | None = typer.Option(None, help="Run ID (default: auto-generated timestamp+uuid)"),
        force: bool = typer.Option(False, "--force", help="Overwrite existing run directory if it exists"),
    ) -> None:
        """Run the Design agent end-to-end up to the approval gate."""
        from agentsuite.agents.design.input_schema import DesignAgentInput
        from agentsuite.cli import _output_root, _resolve_llm_for_cli

        agent = DesignAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
        inp = DesignAgentInput(
            agent_name="design",
            role_domain="design-ops",
            user_request=f"create design artifacts for {campaign_goal}",
            target_audience=target_audience,
            campaign_goal=campaign_goal,
            channel=channel,  # type: ignore[arg-type]
            project_slug=project_slug,
            inputs_dir=inputs_dir,
        )
        rid = run_id or f"run-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:6]}"
        run_dir = Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite")) / "runs" / rid
        if run_dir.exists() and not force:
            typer.echo(f"Error: run '{rid}' already exists. Use --force to overwrite.", err=True)
            raise typer.Exit(1)
        state = agent.run(request=inp, run_id=rid)
        typer.echo(json.dumps({
            "run_id": state.run_id,
            "status": "awaiting_approval" if state.stage == "approval" else state.stage,
            "stage": state.stage,
            "primary_path": str(_output_root() / "runs" / state.run_id / "visual-direction.md"),
            "open_questions": state.open_questions,
            "cost_usd": state.cost_so_far.usd,
        }, indent=2))

    return AgentCLISpec(
        cli_name="design",
        help="Design agent commands",
        run_fn=run_cmd,
        agent_class=DesignAgent,
        primary_artifact="visual-direction.md",
        agent_name="design",
    )
