"""``agentsuite`` command-line entry point."""
from __future__ import annotations

import importlib
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

import typer

from agentsuite.agents.registry import default_registry
from agentsuite.kernel.state_store import StateStore
from agentsuite.llm.resolver import NoProviderConfigured, resolve_provider


# Force UTF-8 on stdout/stderr early so Typer help text containing non-ASCII
# characters (em-dash, arrow) does not crash on default Windows cp1252 consoles.
# Idempotent and a no-op on terminals that already speak UTF-8.
def _force_utf8_io() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except Exception:
                # Some test harnesses swap stdout for a buffer without
                # reconfigure(); a failure here is non-fatal.
                pass


_force_utf8_io()

app = typer.Typer(
    help="AgentSuite -- reasoning agents for vague intent -> precise artifacts"
)

# Module-level flag toggled by the --debug callback so inner helpers can read it.
_debug_mode: bool = False


@app.callback()
def _global_options(
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on errors."),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Suppress per-stage progress markers on stderr (UX-006/QA-005).",
    ),
) -> None:
    """Global options applied to every subcommand."""
    global _debug_mode
    _debug_mode = debug
    if quiet:
        os.environ["AGENTSUITE_QUIET"] = "1"


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


def _resolve_latest_run_id(agent_name: str) -> str:
    """Return the run_id of the most recently modified run for *agent_name*.

    Raises ``typer.Exit(1)`` (with an error message) if no matching run is found.
    """
    runs_dir = _output_root() / "runs"
    if not runs_dir.exists():
        typer.echo("Error: no runs directory found — nothing to approve.", err=True)
        raise typer.Exit(1)
    best_run_id: str | None = None
    best_mtime: float = -1.0
    for d in runs_dir.iterdir():
        if not d.is_dir():
            continue
        state = StateStore(run_dir=d).load()
        if state is None or state.agent != agent_name:
            continue
        mtime = d.stat().st_mtime
        if mtime > best_mtime:
            best_mtime = mtime
            best_run_id = state.run_id
    if best_run_id is None:
        typer.echo(f"Error: no runs found for agent '{agent_name}'.", err=True)
        raise typer.Exit(1)
    return best_run_id


def _make_approve_fn(agent_class: type) -> Any:
    """Generate a generic approve command for any agent."""
    # Capture the agent name at registration time for --latest resolution.
    agent_name_for_latest: str = getattr(agent_class, "name", "")

    def approve_cmd(
        run_id: Optional[str] = typer.Option(None, help="Run id to approve (omit with --latest)"),
        latest: bool = typer.Option(False, "--latest", help="Approve the most recently created run."),
        approver: str = typer.Option(..., help="Approver identity"),
        project_slug: str = typer.Option(..., help="Slug for `_kernel/<slug>/` promotion"),
    ) -> None:
        """Approve a completed run and promote artifacts to ``_kernel/``."""
        if latest:
            resolved_run_id = _resolve_latest_run_id(agent_name_for_latest)
        elif run_id is not None:
            resolved_run_id = run_id
        else:
            typer.echo("Error: provide --run-id <id> or --latest.", err=True)
            raise typer.Exit(1)
        try:
            agent = agent_class(output_root=_output_root(), llm=_resolve_llm_for_cli())
            state = agent.approve(run_id=resolved_run_id, approver=approver, project_slug=project_slug)
        except Exception as exc:
            if _debug_mode:
                traceback.print_exc()
            else:
                typer.echo(f"Error: {exc}", err=True)
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
