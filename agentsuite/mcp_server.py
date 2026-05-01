"""AgentSuite MCP server entry point."""
from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from agentsuite.agents.registry import UnknownAgent, default_registry
from agentsuite.kernel.identifiers import validate_project_slug
from agentsuite.mcp_models import RunSummary

# Registry mapping agent name → dotted module path for its MCP tools.
# To add a new agent: register it here — no other changes needed in this file.
_MCP_MODULES: dict[str, str] = {
    "founder":     "agentsuite.agents.founder.mcp_tools",
    "design":      "agentsuite.agents.design.mcp_tools",
    "product":     "agentsuite.agents.product.mcp_tools",
    "engineering": "agentsuite.agents.engineering.mcp_tools",
    "marketing":   "agentsuite.agents.marketing.mcp_tools",
    "trust_risk":  "agentsuite.agents.trust_risk.mcp_tools",
    "cio":         "agentsuite.agents.cio.mcp_tools",
}

_log = logging.getLogger(__name__)


def _output_root() -> Path:
    """Return the configured output root directory (default ``.agentsuite``)."""
    return Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite"))


def _expose_stages() -> bool:
    """Return True if AGENTSUITE_EXPOSE_STAGES env opts in to advanced stage tools."""
    return os.environ.get("AGENTSUITE_EXPOSE_STAGES", "").lower() in {"1", "true", "yes"}


class _ServerWrapper:
    """Thin wrapper around FastMCP exposing the registered tool list for tests."""

    def __init__(self, mcp: "FastMCP") -> None:
        self.mcp = mcp
        self._tool_names: list[str] = []

    def add_tool(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a tool with the underlying MCP server and track its name."""
        self.mcp.tool(name=name)(fn)
        self._tool_names.append(name)

    def tool_names(self) -> list[str]:
        """Return the list of registered tool names."""
        return list(self._tool_names)

    def run(self) -> None:
        """Run the underlying FastMCP server (stdio loop)."""
        self.mcp.run()


def build_server() -> _ServerWrapper:
    """Build the AgentSuite MCP server with all enabled-agent tools registered."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise ImportError(
            'MCP SDK not installed. Run: pip install "agentsuite[mcp]"'
        ) from exc
    mcp = FastMCP("agentsuite")
    server = _ServerWrapper(mcp)

    registry = default_registry()
    try:
        enabled = registry.enabled_names()
    except UnknownAgent as e:
        raise RuntimeError(
            f"AGENTSUITE_ENABLED_AGENTS contains an unknown agent name: {e}. "
            "Valid agents: founder, design, product, engineering, marketing, trust_risk, cio"
        ) from e

    # Per-agent tools
    for name in enabled:
        try:
            agent_class = registry.get_class(name)
        except UnknownAgent as e:
            _log.warning("Skipping agent %s: not registered — %r", name, e)
            continue
        module_path = _MCP_MODULES.get(name)
        if module_path is None:
            _log.warning("Skipping agent %s: no MCP tools module in _MCP_MODULES", name)
            continue
        mcp_module = importlib.import_module(module_path)
        mcp_module.register_tools(
            server,
            agent_class=lambda cls=agent_class: cls(output_root=_output_root()),
            output_root_fn=_output_root,
            expose_stages=_expose_stages(),
        )

    # Cross-agent shared tools
    def agentsuite_list_agents() -> dict[str, Any]:
        """List all enabled agents and all registered agents."""
        return {"enabled": enabled, "all_registered": sorted(registry._registered.keys())}

    def agentsuite_kernel_artifacts(project_slug: str) -> dict[str, Any]:
        """List kernel artifacts for a given project."""
        validate_project_slug(project_slug)
        kernel_dir = _output_root() / "_kernel" / project_slug
        if not kernel_dir.exists():
            return {"artifacts": []}
        return {
            "artifacts": sorted(
                str(p.relative_to(kernel_dir))
                for p in kernel_dir.rglob("*")
                if p.is_file()
            )
        }

    def agentsuite_cost_report() -> dict[str, Any]:
        """Generate a cost report across all runs."""
        runs_dir = _output_root() / "runs"
        if not runs_dir.exists():
            return {"runs": [], "total_usd": 0.0}
        from agentsuite.kernel.state_store import RunStateSchemaVersionError, StateStore

        runs: list[RunSummary] = []
        total = 0.0
        for d in sorted(runs_dir.iterdir()):
            if not d.is_dir():
                continue
            store = StateStore(run_dir=d)
            try:
                state = store.load()
            except RunStateSchemaVersionError:
                _log.warning(
                    "Skipping run dir %s: schema version mismatch "
                    "(pre-v0.9 run directory — delete it and re-run)",
                    d.name,
                )
                continue
            if state is None:
                continue
            runs.append(RunSummary(
                run_id=state.run_id,
                agent=state.agent,
                stage=state.stage,
                started_at=state.started_at,
                cost_usd=state.cost_so_far.usd,
            ))
            total += state.cost_so_far.usd
        return {"runs": [r.model_dump(mode="json") for r in runs], "total_usd": total}

    server.add_tool("agentsuite_list_agents", agentsuite_list_agents)
    server.add_tool("agentsuite_kernel_artifacts", agentsuite_kernel_artifacts)
    server.add_tool("agentsuite_cost_report", agentsuite_cost_report)

    return server


def main() -> None:
    """Entry point for the ``agentsuite-mcp`` console script.

    Handles ``--help`` and ``--version`` directly so the binary surfaces a
    usable response to the first command every Codex / Claude Code
    integrator types. Without this, FastMCP.run() takes over stdin and
    silently exits 0 with no stdout (audit QA-101).
    """
    import sys
    args = sys.argv[1:]
    if args and args[0] in ("--help", "-h"):
        from agentsuite.__version__ import __version__
        help_lines = [
            "agentsuite-mcp -- AgentSuite MCP server",
            "",
            "Usage:",
            "  agentsuite-mcp                Start the MCP stdio server",
            "  agentsuite-mcp --help         Show this help",
            "  agentsuite-mcp --version      Print the package version",
            "",
            "Configuration via environment variables:",
            "  AGENTSUITE_ENABLED_AGENTS    Comma-separated agent names to enable",
            "                               (default: founder; allowed: founder, design,",
            "                                product, engineering, marketing, trust_risk, cio)",
            "  AGENTSUITE_OUTPUT_DIR        Output root for agent runs (default: .agentsuite)",
            "  AGENTSUITE_LLM_PROVIDER      Force a specific provider (default: auto-detect)",
            "  AGENTSUITE_EXPOSE_STAGES     Set to 1 to expose advanced stage tools",
            "  AGENTSUITE_QUIET             Set to 1 to suppress stage-progress lines",
            "",
            "MCP wiring: see README.md and docs/USER-MANUAL.md for Codex / Claude Code /",
            "Cowork client config snippets.",
            f"Version {__version__}.",
            "",
        ]
        sys.stdout.write("\n".join(help_lines))
        sys.stdout.flush()
        return
    if args and args[0] in ("--version", "-V"):
        from agentsuite.__version__ import __version__
        sys.stdout.write(f"agentsuite-mcp {__version__}\n")
        sys.stdout.flush()
        return
    server = build_server()
    server.run()


if __name__ == "__main__":
    main()
