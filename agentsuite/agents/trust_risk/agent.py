"""TrustRiskAgent — wires the kernel BaseAgent to trust/risk stage handlers."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC
from agentsuite.agents.trust_risk.stages.execute import execute_stage
from agentsuite.agents.trust_risk.stages.extract import extract_stage
from agentsuite.agents.trust_risk.stages.intake import intake_stage
from agentsuite.agents.trust_risk.stages.qa import qa_stage
from agentsuite.agents.trust_risk.stages.spec import spec_stage
from agentsuite.kernel.base_agent import AgentCLISpec, BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class TrustRiskAgent(BaseAgent):
    """Concrete agent that produces trust and risk assessment artifacts.

    Subclasses BaseAgent. Wires the 5 trust/risk stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "trust_risk"
    qa_rubric = TRUST_RISK_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see TrustRiskAgentInput-specific fields.
        """
        from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, TrustRiskAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as product_name. Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, TrustRiskAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    elif isinstance(typed_inputs, dict):
                        state = state.model_copy(update={
                            "inputs": TrustRiskAgentInput(**typed_inputs)
                        })
                    else:
                        state = state.model_copy(update={
                            "inputs": TrustRiskAgentInput.model_validate(state.inputs.model_dump())
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
    """Return the CLI spec for the Trust/Risk agent."""
    import json
    import typer

    def run_cmd(
        product_name: str = typer.Option(..., help="Name of the product or system being assessed"),
        risk_domain: str = typer.Option(..., help="Risk domain (e.g. 'cloud infrastructure', 'SaaS application')"),
        stakeholder_context: str = typer.Option(..., help="Who the assessment is for and their security responsibilities"),
        regulatory_context: str = typer.Option("", help="Applicable regulations (e.g. 'SOC 2 Type II, HIPAA')"),
        threat_model_scope: str = typer.Option("", help="Scope of the threat model (e.g. 'external attackers, insider threats')"),
        compliance_frameworks: str = typer.Option("", help="Compliance frameworks (e.g. 'NIST CSF, ISO 27001')"),
        policy_dir: Path | None = typer.Option(None, help="Dir with existing security policy documents"),
        incident_dir: Path | None = typer.Option(None, help="Dir with incident reports"),
        run_id: str | None = typer.Option(None, help="Run ID (default: auto-generated timestamp+uuid)"),
        force: bool = typer.Option(False, "--force", help="Overwrite existing run directory if it exists"),
    ) -> None:
        """Run the Trust/Risk Agent pipeline."""
        from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
        from agentsuite.cli import _output_root, _resolve_llm_for_cli

        existing_policies: list[Path] = list(policy_dir.iterdir()) if policy_dir and policy_dir.is_dir() else []
        incident_reports: list[Path] = list(incident_dir.iterdir()) if incident_dir and incident_dir.is_dir() else []
        inp = TrustRiskAgentInput(
            agent_name="trust-risk",
            role_domain="trust-risk-ops",
            user_request=f"Generate trust and risk assessment for {product_name}",
            product_name=product_name,
            risk_domain=risk_domain,
            stakeholder_context=stakeholder_context,
            regulatory_context=regulatory_context,
            threat_model_scope=threat_model_scope,
            compliance_frameworks=compliance_frameworks,
            existing_policies=existing_policies,
            incident_reports=incident_reports,
        )
        agent = TrustRiskAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
        rid = run_id or f"run-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:6]}"
        run_dir = Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite")) / "runs" / rid
        if run_dir.exists() and not force:
            typer.echo(f"Error: run '{rid}' already exists. Use --force to overwrite.", err=True)
            raise typer.Exit(1)
        result = agent.run(request=inp, run_id=rid)
        typer.echo(json.dumps({
            "run_id": result.run_id,
            "primary_path": str(_output_root() / "runs" / result.run_id / "threat-model.md"),
            "status": result.stage,
        }, indent=2))

    return AgentCLISpec(
        cli_name="trust-risk",
        help="Trust/Risk Agent — generates threat model, risk register, control framework, and related artifacts.",
        run_fn=run_cmd,
        agent_class=TrustRiskAgent,
        primary_artifact="threat-model.md",
        agent_name="trust_risk",
        has_list_runs=True,
    )
