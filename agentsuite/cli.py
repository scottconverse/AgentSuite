"""``agentsuite`` command-line entry point."""
from __future__ import annotations

import importlib
import json
import os
import traceback
from pathlib import Path
from typing import Any, Optional

import typer

from agentsuite.agents.registry import default_registry
from agentsuite.kernel.state_store import StateStore
from agentsuite.llm.resolver import NoProviderConfigured, resolve_provider


app = typer.Typer(help="AgentSuite — reasoning agents for vague intent → precise artifacts")


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


def _latest_run_id(agent_name: str) -> Optional[str]:
    """Return the run_id of the most recently modified run dir for ``agent_name``."""
    runs_dir = _output_root() / "runs"
    if not runs_dir.exists():
        return None
    best: Optional[Path] = None
    best_mtime = 0.0
    for d in runs_dir.iterdir():
        if not d.is_dir():
            continue
        state = StateStore(run_dir=d).load()
        if state is None or state.agent != agent_name:
            continue
        mtime = d.stat().st_mtime
        if mtime > best_mtime:
            best_mtime = mtime
            best = d
    return best.name if best else None


def _make_approve_fn(agent_class: type) -> Any:
    """Generate a generic approve command for any agent."""
    agent_name = getattr(agent_class, "AGENT_NAME", agent_class.__name__.lower().replace("agent", ""))

    def approve_cmd(
        run_id: Optional[str] = typer.Option(None, help="Run id to approve"),
        approver: str = typer.Option(..., help="Approver identity"),
        project_slug: str = typer.Option(..., help="Slug for `_kernel/<slug>/` promotion"),
        latest: bool = typer.Option(False, "--latest", help="Auto-select the most recent run"),
        debug: bool = typer.Option(False, "--debug", help="Print full traceback on error"),
    ) -> None:
        """Approve a completed run and promote artifacts to ``_kernel/``."""
        rid = run_id
        if rid is None:
            if latest:
                rid = _latest_run_id(agent_name)
                if rid is None:
                    typer.echo(f"Error: no runs found for agent '{agent_name}'.", err=True)
                    raise typer.Exit(1)
            else:
                typer.echo("Error: provide --run-id or use --latest to select the most recent run.", err=True)
                raise typer.Exit(1)
        try:
            agent = agent_class(output_root=_output_root(), llm=_resolve_llm_for_cli())
            state = agent.approve(run_id=rid, approver=approver, project_slug=project_slug)
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"Error: {exc}", err=True)
            if debug:
                typer.echo(traceback.format_exc(), err=True)
            else:
                typer.echo("Re-run with --debug for full traceback.", err=True)
            raise typer.Exit(1)
        typer.echo(json.dumps({
            "run_id": state.run_id,
            "status": "done",
            "approved_by": state.approved_by,
        }, indent=2))
    return approve_cmd


def _make_list_runs_fn(agent_name: str) -> Any:
    """Generate a list-runs command that filters by agent name."""
    def list_runs_cmd() -> None:
        """List all runs for this agent in the current output directory."""
        runs_dir = _output_root() / "runs"
        if not runs_dir.exists():
            typer.echo("[]")
            return
        out = []
        for d in sorted(runs_dir.iterdir()):
            if not d.is_dir():
                continue
            state = StateStore(run_dir=d).load()
            if state is None or state.agent != agent_name:
                continue
            out.append({
                "run_id": state.run_id,
                "agent": state.agent,
                "stage": state.stage,
                "cost_usd": state.cost_so_far.usd,
            })
        typer.echo(json.dumps(out, indent=2))
    return list_runs_cmd


def _register_agents() -> None:
    """Import each agent module, read its AgentCLISpec, and register Typer subcommands."""
    agent_modules = [
        "agentsuite.agents.founder.agent",
        "agentsuite.agents.design.agent",
        "agentsuite.agents.product.agent",
        "agentsuite.agents.engineering.agent",
        "agentsuite.agents.marketing.agent",
        "agentsuite.agents.trust_risk.agent",
        "agentsuite.agents.cio.agent",
    ]
    for module_path in agent_modules:
        mod = importlib.import_module(module_path)
        spec = mod.build_cli_spec()
        sub = typer.Typer(name=spec.cli_name, help=spec.help)
        sub.command("run")(spec.run_fn)
        sub.command("approve")(_make_approve_fn(spec.agent_class))
        if spec.has_list_runs:
            agent_name = spec.agent_name or spec.cli_name
            sub.command("list-runs")(_make_list_runs_fn(agent_name))
        app.add_typer(sub, name=spec.cli_name)


_register_agents()


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
