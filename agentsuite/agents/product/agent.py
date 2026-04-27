"""ProductAgent — wires the kernel BaseAgent to product stage handlers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentsuite.agents.product.rubric import PRODUCT_RUBRIC
from agentsuite.agents.product.stages.execute import execute_stage
from agentsuite.agents.product.stages.extract import extract_stage
from agentsuite.agents.product.stages.intake import intake_stage
from agentsuite.agents.product.stages.qa import qa_stage
from agentsuite.agents.product.stages.spec import spec_stage
from agentsuite.kernel.base_agent import BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class ProductAgent(BaseAgent):
    """Concrete agent that produces product specification artifacts.

    Subclasses BaseAgent. Wires the 5 product stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "product"
    qa_rubric = PRODUCT_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see ProductAgentInput-specific fields.
        """
        from agentsuite.agents.product.input_schema import ProductAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, ProductAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as product_name.  Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, ProductAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    else:
                        state = state.model_copy(update={
                            "inputs": ProductAgentInput.model_validate(state.inputs.model_dump())
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
    """Return the CLI spec for the Product agent."""
    from agentsuite.kernel.base_agent import AgentCLISpec
    import json
    from pathlib import Path
    import typer

    def run_cmd(
        product_name: str = typer.Option(..., help="Product name"),
        target_users: str = typer.Option(..., help="Who the product is for"),
        core_problem: str = typer.Option(..., help="Core problem being solved"),
        project_slug: str = typer.Option(..., help="Project slug for output dir"),
        inputs_dir: Path | None = typer.Option(None, help="Dir with research/competitive docs"),
        run_id: str | None = typer.Option(None, help="Run ID (auto-generated if omitted)"),
    ) -> None:
        """Run the Product Agent pipeline."""
        from agentsuite.agents.product.input_schema import ProductAgentInput
        from agentsuite.cli import _output_root, _resolve_llm_for_cli

        inp = ProductAgentInput(
            agent_name="product",
            role_domain="product-ops",
            user_request=f"Generate product spec for {product_name}",
            product_name=product_name,
            target_users=target_users,
            core_problem=core_problem,
            inputs_dir=inputs_dir,
        )
        agent = ProductAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
        result = agent.run(request=inp, run_id=run_id or "run-cli")
        typer.echo(json.dumps({
            "run_id": result.run_id,
            "status": "awaiting_approval" if result.stage == "approval" else result.stage,
            "stage": result.stage,
            "project_slug": project_slug,
            "cost_usd": result.cost_so_far.usd,
        }, indent=2, default=str))

    return AgentCLISpec(
        cli_name="product",
        help="Product Agent — generates PRD, roadmap, and brief templates.",
        run_fn=run_cmd,
        agent_class=ProductAgent,
        primary_artifact="product-requirements-doc.md",
        agent_name="product",
    )
