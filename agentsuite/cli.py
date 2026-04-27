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


app = typer.Typer(help="AgentSuite — reasoning agents for vague intent → precise artifacts")
founder_app = typer.Typer(help="Founder agent commands")
app.add_typer(founder_app, name="founder")
design_app = typer.Typer(help="Design agent commands")
app.add_typer(design_app, name="design")
product_app = typer.Typer(name="product", help="Product Agent — generates PRD, roadmap, and brief templates.")
app.add_typer(product_app, name="product")


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
    from agentsuite.llm.resolver import resolve_provider

    return resolve_provider()


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
        "all_registered": sorted(reg._registered.keys()),
    }, indent=2))


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
