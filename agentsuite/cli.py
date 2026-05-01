"""``agentsuite`` command-line entry point."""
from __future__ import annotations

import functools
import importlib
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

import click
import typer

from agentsuite.agents.registry import UnknownAgent, default_registry
from agentsuite.kernel.approval import RevisionRequired
from agentsuite.kernel.state_store import RunStateSchemaVersionError, StateStore
from agentsuite.llm.base import ProviderNotInstalled
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
    # NOTE: TEST-ONLY. Never set AGENTSUITE_LLM_PROVIDER_FACTORY in production.
    # This env var executes arbitrary Python via importlib. It exists solely for
    # test injection of mock LLM providers. If set outside of pytest, it is a
    # remote code execution vector.
    factory = os.environ.get("AGENTSUITE_LLM_PROVIDER_FACTORY")
    if factory and not os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("AGENTSUITE_ALLOW_MOCK_FACTORY"):
        raise RuntimeError(
            "AGENTSUITE_LLM_PROVIDER_FACTORY is set outside of a pytest run. "
            "This environment variable executes arbitrary Python and must only be "
            "used in tests. Unset it before running AgentSuite."
        )
    if factory:
        module_name, fn_name = factory.split(":", 1)
        return getattr(importlib.import_module(module_name), fn_name)()
    try:
        return resolve_provider()
    except NoProviderConfigured as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ProviderNotInstalled as e:
        typer.echo(
            f"Error: provider library not installed — {e}\n"
            'Reinstall with the provider extra, e.g.: pip install "agentsuite[anthropic] @ git+https://github.com/scottconverse/AgentSuite.git"',
            err=True,
        )
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
        project_slug: str = typer.Option(..., help="Stable slug for artifact promotion (e.g. 'my-app'); approved artifacts go to .agentsuite/_kernel/<slug>/"),
    ) -> None:
        """Approve a completed run and promote artifacts to ``_kernel/``."""
        try:
            if latest:
                resolved_run_id = _resolve_latest_run_id(agent_name_for_latest)
            elif run_id is not None:
                resolved_run_id = run_id
            else:
                typer.echo("Error: provide --run-id <id> or --latest.", err=True)
                raise typer.Exit(1)
            agent = agent_class(output_root=_output_root(), llm=_resolve_llm_for_cli())
            run_dir = _output_root() / "runs" / resolved_run_id
            summary = _artifact_summary(run_dir)
            if summary:
                typer.echo(f"\nArtifacts produced:\n{summary}", err=True)
            state = agent.approve(run_id=resolved_run_id, approver=approver, project_slug=project_slug)
        except typer.Exit:
            raise
        except RevisionRequired:
            run_dir = _output_root() / "runs" / resolved_run_id
            qa_report = run_dir / "qa_report.md"
            typer.echo(
                "Error: QA flagged this run as requiring revision before approval.\n"
                f"  Review the QA report: {qa_report}\n"
                f"  Address the feedback, then re-run the agent:\n"
                f"    agentsuite {agent_name_for_latest} run --run-id {resolved_run_id} --force\n"
                f"  Once the new run passes QA, approve it:\n"
                f"    agentsuite {agent_name_for_latest} approve --run-id NEW_RUN_ID --approver YOUR_NAME --project-slug YOUR_SLUG",
                err=True,
            )
            raise typer.Exit(1)
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
            try:
                state = StateStore(run_dir=d).load()
            except RunStateSchemaVersionError:
                typer.echo(f"[WARN] Skipping pre-v0.9 run dir {d.name} — delete it and re-run to include it in results.", err=True)
                continue
            if state is None or state.agent != agent_name:
                continue
            out.append({
                "run_id": state.run_id,
                "agent": state.agent,
                "stage": state.stage,
                "started_at": state.started_at.isoformat(),
                "cost_usd": state.cost_so_far.usd,
            })
        typer.echo(json.dumps(out, indent=2))
    return list_runs_cmd


def _make_run_fn_with_hint(fn: Callable[..., None], hint: str) -> Callable[..., None]:
    """Return a wrapper that calls *fn* then emits *hint* to stderr."""
    @functools.wraps(fn)
    def _wrapper(*args: Any, **kwargs: Any) -> None:
        fn(*args, **kwargs)
        typer.echo(hint, err=True)
    return _wrapper


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
        _hint = spec.next_step_hint
        _fn = spec.run_fn
        run_fn = _make_run_fn_with_hint(_fn, _hint) if _hint else _fn
        sub.command("run")(run_fn)
        sub.command("approve")(_make_approve_fn(spec.agent_class))
        if spec.has_list_runs:
            agent_name = spec.agent_name or spec.cli_name
            sub.command("list-runs")(_make_list_runs_fn(agent_name))
        app.add_typer(sub, name=spec.cli_name)


_register_agents()


def _artifact_summary(run_dir: Path, max_shown: int = 6) -> str:
    """Return a short human-readable summary of the artifacts in *run_dir*.

    Lists user-facing files (excludes _state.json, _meta.json and directories).
    """
    if not run_dir.exists():
        return ""
    files = sorted(
        f for f in run_dir.iterdir()
        if f.is_file() and not f.name.startswith("_")
    )
    if not files:
        return ""
    lines = []
    for f in files[:max_shown]:
        size_kb = f.stat().st_size / 1024
        lines.append(f"  {f.name:<30}  {size_kb:.1f} KB")
    if len(files) > max_shown:
        lines.append(f"  (+ {len(files) - max_shown} more in {run_dir})")
    return "\n".join(lines)


def _default_approver() -> str:
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return "user"


def _make_pipeline_progress(total_steps: int) -> Any:
    import time
    timers: dict[str, float] = {}

    def on_progress(event: str, step: Any, state: Any) -> None:
        idx = state.current_step_index
        label = f"[{idx + 1}/{total_steps}] {step.agent}"
        if event == "agent_start":
            timers[step.run_id] = time.monotonic()
            typer.echo(f"{label}  starting...", err=True)
        elif event == "agent_done":
            elapsed = time.monotonic() - timers.get(step.run_id, time.monotonic())
            typer.echo(
                f"{label}  done  ${step.cost_usd:.4f}  ({elapsed:.1f}s)", err=True
            )
        elif event == "agent_waiting":
            elapsed = time.monotonic() - timers.get(step.run_id, time.monotonic())
            typer.echo(
                f"{label}  ready for review  ({elapsed:.1f}s)", err=True
            )

    return on_progress


def _register_pipeline() -> None:
    """Register the ``pipeline`` subapp with run / approve / status commands."""
    pipeline_app = typer.Typer(name="pipeline", help="Multi-agent pipeline commands.")

    @pipeline_app.command("run")
    def pipeline_run(
        agents: str = typer.Option(
            ..., help="Comma-separated agent names in run order (e.g. founder,design,product)"
        ),
        project_slug: str = typer.Option(...),
        business_goal: str = typer.Option(...),
        inputs_dir: Optional[Path] = typer.Option(None),
        agent_inputs: Optional[Path] = typer.Option(
            None, help="JSON file with per-agent extra fields required by Engineering / Trust-Risk / CIO"
        ),
        auto_approve: bool = typer.Option(
            False, "--auto-approve", help="Approve each step automatically without pausing"
        ),
        pipeline_id: Optional[str] = typer.Option(None, help="Custom pipeline ID (auto-generated if omitted)"),
    ) -> None:
        """Run a multi-agent pipeline end-to-end."""
        from agentsuite.pipeline.orchestrator import PipelineOrchestrator

        agent_list = [a.strip().replace("-", "_") for a in agents.split(",") if a.strip()]
        extras: dict[str, Any] = {}
        if agent_inputs is not None:
            if not agent_inputs.exists():
                typer.echo(f"Error: --agent-inputs file not found: {agent_inputs}", err=True)
                raise typer.Exit(1)
            import json as _json
            try:
                raw = _json.loads(agent_inputs.read_text(encoding="utf-8"))
            except _json.JSONDecodeError as exc:
                typer.echo(
                    f"Error: --agent-inputs is not valid JSON.\n"
                    f"  File: {agent_inputs}\n"
                    f"  Problem: {exc.msg} at line {exc.lineno}, column {exc.colno}\n"
                    f"  Expected format: {{\"engineering\": {{\"tech_stack\": \"...\", \"scale_requirements\": \"...\"}}}}",
                    err=True,
                )
                raise typer.Exit(1)
            except Exception as exc:
                typer.echo(f"Error: could not read --agent-inputs: {exc}", err=True)
                raise typer.Exit(1)
            if not isinstance(raw, dict):
                typer.echo(
                    f"Error: --agent-inputs must be a JSON object, got {type(raw).__name__}.\n"
                    f"  Expected: {{\"<agent-name>\": {{\"field\": \"value\"}}}}",
                    err=True,
                )
                raise typer.Exit(1)
            extras = raw

        on_progress = _make_pipeline_progress(len(agent_list))
        output_root = _output_root()

        try:
            orch = PipelineOrchestrator(output_root=output_root)
            state = orch.run(
                agents=agent_list,
                project_slug=project_slug,
                business_goal=business_goal,
                inputs_dir=inputs_dir,
                agent_extras=extras,
                pipeline_id=pipeline_id,
                auto_approve=auto_approve,
                llm=_resolve_llm_for_cli(),
                on_progress=on_progress,
            )
        except Exception as exc:
            if _debug_mode:
                traceback.print_exc()
            else:
                typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(1)

        typer.echo(json.dumps({
            "pipeline_id": state.pipeline_id,
            "status": state.status,
            "current_step": state.current_step_index,
            "total_steps": len(state.steps),
            "total_cost_usd": state.total_cost_usd,
        }, indent=2))

        if state.status == "awaiting_approval":
            current = state.steps[state.current_step_index]
            run_dir = output_root / "runs" / current.run_id
            summary = _artifact_summary(run_dir)
            artifact_block = f"\nProduced by {current.agent!r}:\n{summary}\n" if summary else ""
            typer.echo(
                f"{artifact_block}"
                f"Awaiting approval. Review, then run:\n"
                f"  agentsuite pipeline approve --pipeline-id {state.pipeline_id}",
                err=True,
            )
        elif state.status == "done":
            kernel_dir = output_root / "_kernel" / project_slug
            typer.echo(
                f"\nPipeline complete. Artifacts in {kernel_dir}",
                err=True,
            )

    @pipeline_app.command("approve")
    def pipeline_approve(
        pipeline_id: str = typer.Option(...),
        approver: Optional[str] = typer.Option(
            None, help="Your name recorded in the approval log (defaults to OS username)"
        ),
    ) -> None:
        """Approve the current awaiting step and advance the pipeline."""
        from agentsuite.pipeline.orchestrator import PipelineOrchestrator
        from agentsuite.pipeline.state_store import PipelineNotFound

        resolved_approver = approver or _default_approver()
        output_root = _output_root()

        try:
            orch = PipelineOrchestrator(output_root=output_root)
            # Load state first to know total steps for progress label
            pre_state = orch.status(pipeline_id=pipeline_id)
            on_progress = _make_pipeline_progress(len(pre_state.agents))
            state = orch.approve(
                pipeline_id=pipeline_id,
                approver=resolved_approver,
                llm=_resolve_llm_for_cli(),
                on_progress=on_progress,
            )
        except PipelineNotFound:
            typer.echo(f"Error: pipeline {pipeline_id!r} not found", err=True)
            raise typer.Exit(1)
        except Exception as exc:
            if _debug_mode:
                traceback.print_exc()
            else:
                typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(1)

        typer.echo(json.dumps({
            "pipeline_id": state.pipeline_id,
            "status": state.status,
            "current_step": state.current_step_index,
            "total_steps": len(state.steps),
        }, indent=2))

        if state.status == "awaiting_approval":
            current = state.steps[state.current_step_index]
            run_dir = output_root / "runs" / current.run_id
            summary = _artifact_summary(run_dir)
            artifact_block = f"\nProduced by {current.agent!r}:\n{summary}\n" if summary else ""
            typer.echo(
                f"{artifact_block}"
                f"Awaiting approval. Review, then run:\n"
                f"  agentsuite pipeline approve --pipeline-id {state.pipeline_id}",
                err=True,
            )
        elif state.status == "done":
            kernel_dir = output_root / "_kernel" / state.project_slug
            typer.echo(
                f"\nPipeline complete. Artifacts in {kernel_dir}",
                err=True,
            )

    @pipeline_app.command("status")
    def pipeline_status(
        pipeline_id: str = typer.Option(...),
    ) -> None:
        """Show the current status of a pipeline run."""
        from agentsuite.pipeline.orchestrator import PipelineOrchestrator
        from agentsuite.pipeline.state_store import PipelineNotFound

        try:
            orch = PipelineOrchestrator(output_root=_output_root())
            state = orch.status(pipeline_id=pipeline_id)
        except PipelineNotFound:
            typer.echo(f"Error: pipeline {pipeline_id!r} not found", err=True)
            raise typer.Exit(1)

        typer.echo(json.dumps({
            "pipeline_id": state.pipeline_id,
            "status": state.status,
            "project_slug": state.project_slug,
            "agents": state.agents,
            "steps": [
                {
                    "agent": s.agent,
                    "run_id": s.run_id,
                    "status": s.status,
                    "cost_usd": s.cost_usd,
                }
                for s in state.steps
            ],
            "current_step": state.current_step_index,
            "total_cost_usd": state.total_cost_usd,
        }, indent=2))

    @pipeline_app.command("list")
    def pipeline_list() -> None:
        """List all pipelines in the current output directory, newest first."""
        from agentsuite.pipeline.state_store import PipelineStateStore

        pipelines_root = _output_root() / "pipelines"
        if not pipelines_root.exists():
            typer.echo("[]")
            return

        out = []
        for d in pipelines_root.iterdir():
            if not d.is_dir():
                continue
            store = PipelineStateStore(pipelines_root, d.name)
            try:
                state = store.load()
            except Exception:
                continue
            out.append({
                "pipeline_id": state.pipeline_id,
                "status": state.status,
                "project_slug": state.project_slug,
                "agents": state.agents,
                "current_step": state.current_step_index,
                "total_steps": len(state.steps),
                "total_cost_usd": state.total_cost_usd,
                "updated_at": state.updated_at.isoformat(),
            })

        out.sort(key=lambda x: str(x["updated_at"]), reverse=True)
        typer.echo(json.dumps(out, indent=2))

    app.add_typer(pipeline_app, name="pipeline")


_register_pipeline()


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
        try:
            state = StateStore(run_dir=d).load()
        except RunStateSchemaVersionError:
            typer.echo(f"[WARN] Skipping pre-v0.9 run dir {d.name} — delete it and re-run to include it in results.", err=True)
            continue
        if state is None:
            continue
        if project_slug is not None:
            run_slug = getattr(state.inputs, "project_slug", None)
            if run_slug != project_slug:
                continue
        out.append({
            "run_id": state.run_id,
            "agent": state.agent,
            "stage": state.stage,
            "started_at": state.started_at.isoformat(),
            "cost_usd": state.cost_so_far.usd,
        })
    typer.echo(json.dumps(out, indent=2))


@app.command("agents")
def agents_cmd() -> None:
    """List enabled and registered agents."""
    reg = default_registry()
    try:
        enabled = reg.enabled_names()
    except UnknownAgent:
        click.echo(
            "Unknown agent name. Valid agents: "
            "founder, design, product, engineering, marketing, trust_risk, cio",
            err=True,
        )
        raise SystemExit(1)
    typer.echo(json.dumps({
        "enabled": enabled,
        "registered": reg.registered_names(),
    }, indent=2))


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
