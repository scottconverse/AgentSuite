"""MarketingAgent — wires the kernel BaseAgent to marketing stage handlers."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentsuite.agents.marketing.rubric import MARKETING_RUBRIC
from agentsuite.agents.marketing.stages.execute import execute_stage
from agentsuite.agents.marketing.stages.extract import extract_stage
from agentsuite.agents.marketing.stages.intake import intake_stage
from agentsuite.agents.marketing.stages.qa import qa_stage
from agentsuite.agents.marketing.stages.spec import spec_stage
from agentsuite.kernel.base_agent import AgentCLISpec, BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class MarketingAgent(BaseAgent):
    """Concrete agent that produces marketing campaign artifacts.

    Subclasses BaseAgent. Wires the 5 marketing stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "marketing"
    qa_rubric = MARKETING_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see MarketingAgentInput-specific fields.
        """
        from agentsuite.agents.marketing.input_schema import MarketingAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, MarketingAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as brand_name.  Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, MarketingAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    else:
                        state = state.model_copy(update={
                            "inputs": MarketingAgentInput.model_validate(state.inputs.model_dump())
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
    """Return the CLI spec for the Marketing agent."""
    import json
    import typer

    def run_cmd(
        brand_name: str = typer.Option(..., help="Name of the brand or product being marketed"),
        campaign_goal: str = typer.Option(..., help="What the campaign is trying to achieve"),
        target_market: str = typer.Option(..., help="Who the campaign is targeting"),
        project_slug: str | None = typer.Option(None, "--project-slug", help="Project slug for _kernel/ promotion"),
        inputs_dir: Path | None = typer.Option(None, help="Dir with existing brand assets, briefs, research docs"),
        budget_range: str = typer.Option("", help="e.g. '$50k–$100k over 3 months'"),
        timeline: str = typer.Option("", help="e.g. 'Q3 2024, 12-week campaign'"),
        channels: str = typer.Option("", help="e.g. 'paid social, email, content marketing'"),
        run_id: str | None = typer.Option(None, help="Run ID (default: auto-generated timestamp+uuid)"),
        force: bool = typer.Option(False, "--force", help="Overwrite existing run directory if it exists"),
    ) -> None:
        """Run the Marketing Agent pipeline."""
        from agentsuite.agents.marketing.input_schema import MarketingAgentInput
        from agentsuite.cli import _output_root, _resolve_llm_for_cli

        inp = MarketingAgentInput(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request=f"Generate marketing artifacts for {brand_name}",
            brand_name=brand_name,
            campaign_goal=campaign_goal,
            target_market=target_market,
            inputs_dir=inputs_dir,
            budget_range=budget_range,
            timeline=timeline,
            channels=channels,
        )
        agent = MarketingAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
        rid = run_id or f"run-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:6]}"
        run_dir = Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite")) / "runs" / rid
        if run_dir.exists() and not force:
            typer.echo(f"Error: run '{rid}' already exists. Use --force to overwrite.", err=True)
            raise typer.Exit(1)
        result = agent.run(request=inp, run_id=rid)
        typer.echo(json.dumps({
            "run_id": result.run_id,
            "primary_path": str(_output_root() / "runs" / result.run_id / "campaign-brief.md"),
            "status": result.stage,
        }, indent=2))

    return AgentCLISpec(
        cli_name="marketing",
        help="Marketing Agent — generates campaign brief, messaging framework, channel strategy, and related artifacts.",
        run_fn=run_cmd,
        agent_class=MarketingAgent,
        primary_artifact="campaign-brief.md",
        agent_name="marketing",
    )
