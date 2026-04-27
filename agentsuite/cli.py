"""``agentsuite`` command-line entry point."""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any, Optional

import typer

from agentsuite.agents.registry import default_registry
from agentsuite.kernel.state_store import StateStore
from agentsuite.llm.resolver import NoProviderConfigured, resolve_provider


app = typer.Typer(help="AgentSuite — reasoning agents for vague intent → precise artifacts")
founder_app = typer.Typer(help="Founder agent commands")
app.add_typer(founder_app, name="founder")
design_app = typer.Typer(help="Design agent commands")
app.add_typer(design_app, name="design")
product_app = typer.Typer(name="product", help="Product Agent — generates PRD, roadmap, and brief templates.")
app.add_typer(product_app, name="product")
engineering_app = typer.Typer(name="engineering", help="Engineering Agent — generates architecture, API spec, runbook, and related artifacts.")
app.add_typer(engineering_app, name="engineering")
marketing_app = typer.Typer(name="marketing", help="Marketing Agent — generates campaign brief, messaging framework, channel strategy, and related artifacts.")
app.add_typer(marketing_app, name="marketing")
trust_risk_app = typer.Typer(name="trust-risk", help="Trust/Risk Agent — generates threat model, risk register, control framework, and related artifacts.")
app.add_typer(trust_risk_app, name="trust-risk")
cio_app = typer.Typer(name="cio", help="CIO Agent — generates IT strategy, technology roadmap, vendor portfolio, and related artifacts.")
app.add_typer(cio_app, name="cio")


def _output_root() -> Path:
    return Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite"))


def _resolve_llm_for_cli() -> Any:
    """Resolve an LLMProvider for CLI use.

    Honors ``AGENTSUITE_LLM_PROVIDER_FACTORY`` env var (``"module:fn"``) for
    test-only injection. Falls back to the standard provider resolver.
    """
    factory = os.environ.get("AGENTSUITE_LLM_PROVIDER_FACTORY")
    if factory:
        module_name, fn_name = factory.split(":", 1)
        return getattr(importlib.import_module(module_name), fn_name)()
    try:
        return resolve_provider()
    except NoProviderConfigured as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@founder_app.command("run")
def founder_run_cmd(
    business_goal: str = typer.Option(..., help="Required business goal"),
    project_slug: Optional[str] = typer.Option(None, help="Stable slug for `_kernel/` promotion"),
    inputs_dir: Optional[Path] = typer.Option(None, help="Directory of source materials"),
    run_id: Optional[str] = typer.Option(None, help="Caller-provided run id"),
) -> None:
    """Run the Founder agent end-to-end up to the approval gate."""
    from agentsuite.agents.founder.agent import FounderAgent
    from agentsuite.agents.founder.input_schema import FounderAgentInput
    from agentsuite.kernel.schema import Constraints

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
    rid = run_id or "run-cli"
    state = agent.run(request=inp, run_id=rid)
    typer.echo(json.dumps({
        "run_id": state.run_id,
        "status": "awaiting_approval" if state.stage == "approval" else state.stage,
        "stage": state.stage,
        "primary_path": str(_output_root() / "runs" / state.run_id / "brand-system.md"),
        "open_questions": state.open_questions,
        "cost_usd": state.cost_so_far.usd,
    }, indent=2))


@founder_app.command("approve")
def founder_approve_cmd(
    run_id: str = typer.Option(..., help="Run id to approve"),
    approver: str = typer.Option(..., help="Approver identity"),
    project_slug: str = typer.Option(..., help="Slug for `_kernel/<slug>/` promotion"),
) -> None:
    """Approve a completed Founder run and promote artifacts to ``_kernel/``."""
    from agentsuite.agents.founder.agent import FounderAgent

    agent = FounderAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
    state = agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
    typer.echo(json.dumps({
        "run_id": state.run_id,
        "status": "done",
        "approved_by": state.approved_by,
    }, indent=2))


@design_app.command("run")
def design_run_cmd(
    target_audience: str = typer.Option(..., help="Target audience for the campaign"),
    campaign_goal: str = typer.Option(..., help="Campaign goal"),
    channel: str = typer.Option("web", help="Output channel: web/social/email/print/video/deck/other"),
    project_slug: Optional[str] = typer.Option(None, help="Stable slug for `_kernel/` promotion"),
    inputs_dir: Optional[Path] = typer.Option(None, help="Directory of brand source materials"),
    run_id: Optional[str] = typer.Option(None, help="Caller-provided run id"),
) -> None:
    """Run the Design agent end-to-end up to the approval gate."""
    from agentsuite.agents.design.agent import DesignAgent
    from agentsuite.agents.design.input_schema import DesignAgentInput

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
    rid = run_id or "run-cli"
    state = agent.run(request=inp, run_id=rid)
    typer.echo(json.dumps({
        "run_id": state.run_id,
        "status": "awaiting_approval" if state.stage == "approval" else state.stage,
        "stage": state.stage,
        "primary_path": str(_output_root() / "runs" / state.run_id / "visual-direction.md"),
        "open_questions": state.open_questions,
        "cost_usd": state.cost_so_far.usd,
    }, indent=2))


@design_app.command("approve")
def design_approve_cmd(
    run_id: str = typer.Option(..., help="Run id to approve"),
    approver: str = typer.Option(..., help="Approver identity"),
    project_slug: str = typer.Option(..., help="Slug for `_kernel/<slug>/` promotion"),
) -> None:
    """Approve a completed Design run and promote artifacts to ``_kernel/``."""
    from agentsuite.agents.design.agent import DesignAgent

    agent = DesignAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
    state = agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
    typer.echo(json.dumps({
        "run_id": state.run_id,
        "status": "done",
        "approved_by": state.approved_by,
    }, indent=2))


@product_app.command("run")
def product_run_cmd(
    product_name: str = typer.Option(..., help="Product name"),
    target_users: str = typer.Option(..., help="Who the product is for"),
    core_problem: str = typer.Option(..., help="Core problem being solved"),
    project_slug: str = typer.Option(..., help="Project slug for output dir"),
    inputs_dir: Optional[Path] = typer.Option(None, help="Dir with research/competitive docs"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if omitted)"),
) -> None:
    """Run the Product Agent pipeline."""
    from agentsuite.agents.product.agent import ProductAgent
    from agentsuite.agents.product.input_schema import ProductAgentInput
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


@product_app.command("approve")
def product_approve_cmd(
    run_id: str = typer.Option(..., help="Run ID to approve"),
    approver: str = typer.Option(..., help="Approver name"),
    project_slug: str = typer.Option(..., help="Project slug"),
) -> None:
    """Approve a Product Agent run and promote artifacts."""
    from agentsuite.agents.product.agent import ProductAgent
    agent = ProductAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
    agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
    typer.echo(f"Approved {run_id} by {approver}")


@engineering_app.command("run")
def engineering_run_cmd(
    system_name: str = typer.Option(..., help="Name of the system being designed/documented"),
    problem_domain: str = typer.Option(..., help="What problem does this system solve"),
    tech_stack: str = typer.Option(..., help="e.g. 'Python + FastAPI + PostgreSQL + Redis'"),
    scale_requirements: str = typer.Option(..., help="e.g. '10k RPM, 99.9% uptime, <200ms p99'"),
    project_slug: Optional[str] = typer.Option(None, "--project-slug", help="Project slug for _kernel/ promotion"),
    inputs_dir: Optional[Path] = typer.Option(None, help="Dir with existing docs, ADRs, runbooks"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if omitted)"),
) -> None:
    """Run the Engineering Agent pipeline."""
    from agentsuite.agents.engineering.agent import EngineeringAgent
    from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
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


@engineering_app.command("approve")
def engineering_approve_cmd(
    run_id: str = typer.Option(..., help="Run ID to approve"),
    approver: str = typer.Option(..., help="Approver name"),
    project_slug: str = typer.Option(..., help="Project slug"),
) -> None:
    """Approve an Engineering Agent run and promote artifacts."""
    from agentsuite.agents.engineering.agent import EngineeringAgent
    agent = EngineeringAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
    agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
    typer.echo(f"Approved {run_id} by {approver}")


@marketing_app.command("run")
def marketing_run_cmd(
    brand_name: str = typer.Option(..., help="Name of the brand or product being marketed"),
    campaign_goal: str = typer.Option(..., help="What the campaign is trying to achieve"),
    target_market: str = typer.Option(..., help="Who the campaign is targeting"),
    project_slug: Optional[str] = typer.Option(None, "--project-slug", help="Project slug for _kernel/ promotion"),
    inputs_dir: Optional[Path] = typer.Option(None, help="Dir with existing brand assets, briefs, research docs"),
    budget_range: str = typer.Option("", help="e.g. '$50k–$100k over 3 months'"),
    timeline: str = typer.Option("", help="e.g. 'Q3 2024, 12-week campaign'"),
    channels: str = typer.Option("", help="e.g. 'paid social, email, content marketing'"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if omitted)"),
) -> None:
    """Run the Marketing Agent pipeline."""
    from agentsuite.agents.marketing.agent import MarketingAgent
    from agentsuite.agents.marketing.input_schema import MarketingAgentInput
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
    result = agent.run(request=inp, run_id=run_id or "run-cli")
    typer.echo(json.dumps({
        "run_id": result.run_id,
        "status": "awaiting_approval" if result.stage == "approval" else result.stage,
        "stage": result.stage,
        "brand_name": brand_name,
        "cost_usd": result.cost_so_far.usd,
    }, indent=2, default=str))


@marketing_app.command("approve")
def marketing_approve_cmd(
    run_id: str = typer.Option(..., help="Run ID to approve"),
    approver: str = typer.Option(..., help="Approver name"),
    project_slug: str = typer.Option(..., help="Project slug"),
) -> None:
    """Approve a Marketing Agent run and promote artifacts."""
    from agentsuite.agents.marketing.agent import MarketingAgent
    agent = MarketingAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
    agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
    typer.echo(f"Approved {run_id} by {approver}")


@trust_risk_app.command("run")
def trust_risk_run_cmd(
    product_name: str = typer.Option(..., help="Name of the product or system being assessed"),
    risk_domain: str = typer.Option(..., help="Risk domain (e.g. 'cloud infrastructure', 'SaaS application')"),
    stakeholder_context: str = typer.Option(..., help="Who the assessment is for and their security responsibilities"),
    regulatory_context: str = typer.Option("", help="Applicable regulations (e.g. 'SOC 2 Type II, HIPAA')"),
    threat_model_scope: str = typer.Option("", help="Scope of the threat model (e.g. 'external attackers, insider threats')"),
    compliance_frameworks: str = typer.Option("", help="Compliance frameworks (e.g. 'NIST CSF, ISO 27001')"),
    policy_dir: Optional[Path] = typer.Option(None, help="Dir with existing security policy documents"),
    incident_dir: Optional[Path] = typer.Option(None, help="Dir with incident reports"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if omitted)"),
) -> None:
    """Run the Trust/Risk Agent pipeline."""
    from agentsuite.agents.trust_risk.agent import TrustRiskAgent
    from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput

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
    result = agent.run(request=inp, run_id=run_id or "run-cli")
    typer.echo(json.dumps({
        "run_id": result.run_id,
        "status": "awaiting_approval" if result.stage == "approval" else result.stage,
        "stage": result.stage,
        "product_name": product_name,
        "cost_usd": result.cost_so_far.usd,
    }, indent=2, default=str))


@trust_risk_app.command("approve")
def trust_risk_approve_cmd(
    run_id: str = typer.Option(..., help="Run ID to approve"),
    approver: str = typer.Option(..., help="Approver name"),
    project_slug: str = typer.Option(..., help="Project slug"),
) -> None:
    """Approve a Trust/Risk Agent run and promote artifacts."""
    from agentsuite.agents.trust_risk.agent import TrustRiskAgent
    agent = TrustRiskAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
    agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
    typer.echo(f"Approved {run_id} by {approver}")


@trust_risk_app.command("list-runs")
def trust_risk_list_runs_cmd() -> None:
    """List all trust-risk runs in the current output directory."""
    runs_dir = _output_root() / "runs"
    if not runs_dir.exists():
        typer.echo("[]")
        return
    out = []
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        state = StateStore(run_dir=d).load()
        if state is None or state.agent != "trust-risk":
            continue
        out.append({
            "run_id": state.run_id,
            "agent": state.agent,
            "stage": state.stage,
            "cost_usd": state.cost_so_far.usd,
        })
    typer.echo(json.dumps(out, indent=2))


@cio_app.command("run")
def cio_run_cmd(
    organization_name: str = typer.Option(..., help="Name of the organization being assessed"),
    strategic_priorities: str = typer.Option(..., help="Top IT/digital strategic priorities"),
    it_maturity_level: str = typer.Option(..., help="e.g. 'Level 1 – Ad hoc', 'Level 3 – Defined'"),
    budget_context: str = typer.Option("", help="e.g. 'flat budget', '$5M annual IT capex'"),
    digital_initiatives: str = typer.Option("", help="Active or planned digital transformation programs"),
    regulatory_environment: str = typer.Option("", help="e.g. 'HIPAA, SOX, FedRAMP'"),
    it_docs_dir: Optional[Path] = typer.Option(None, help="Dir with existing IT strategy, roadmap, or architecture docs"),
    run_id: Optional[str] = typer.Option(None, help="Run ID (auto-generated if omitted)"),
) -> None:
    """Run the CIO Agent pipeline."""
    from agentsuite.agents.cio.agent import CIOAgent
    from agentsuite.agents.cio.input_schema import CIOAgentInput

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
    result = agent.run(request=inp, run_id=run_id or "run-cli")
    typer.echo(json.dumps({
        "run_id": result.run_id,
        "status": "awaiting_approval" if result.stage == "approval" else result.stage,
        "stage": result.stage,
        "organization_name": organization_name,
        "cost_usd": result.cost_so_far.usd,
    }, indent=2, default=str))


@cio_app.command("approve")
def cio_approve_cmd(
    run_id: str = typer.Option(..., help="Run ID to approve"),
    approver: str = typer.Option(..., help="Approver name"),
    project_slug: str = typer.Option(..., help="Project slug"),
) -> None:
    """Approve a CIO Agent run and promote artifacts."""
    from agentsuite.agents.cio.agent import CIOAgent
    agent = CIOAgent(output_root=_output_root(), llm=_resolve_llm_for_cli())
    agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
    typer.echo(f"Approved {run_id} by {approver}")


@cio_app.command("list-runs")
def cio_list_runs_cmd() -> None:
    """List all CIO runs in the current output directory."""
    runs_dir = _output_root() / "runs"
    if not runs_dir.exists():
        typer.echo("[]")
        return
    out = []
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        state = StateStore(run_dir=d).load()
        if state is None or state.agent != "cio":
            continue
        out.append({
            "run_id": state.run_id,
            "agent": state.agent,
            "stage": state.stage,
            "cost_usd": state.cost_so_far.usd,
        })
    typer.echo(json.dumps(out, indent=2))


@app.command("list-runs")
def list_runs_cmd(project_slug: Optional[str] = typer.Option(None)) -> None:
    """List all runs in the current output directory."""
    runs_dir = _output_root() / "runs"
    if not runs_dir.exists():
        typer.echo("[]")
        return
    out = []
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        state = StateStore(run_dir=d).load()
        if state is None:
            continue
        out.append({
            "run_id": state.run_id,
            "agent": state.agent,
            "stage": state.stage,
            "cost_usd": state.cost_so_far.usd,
        })
    typer.echo(json.dumps(out, indent=2))


@app.command("agents")
def agents_cmd() -> None:
    """List enabled and registered agents."""
    reg = default_registry()
    typer.echo(json.dumps({
        "enabled": reg.enabled_names(),
        "all_registered": reg.registered_names(),
    }, indent=2))


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
