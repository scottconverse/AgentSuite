"""AgentSuite MCP server entry point."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from agentsuite.agents.registry import default_registry
from agentsuite.mcp_models import RunSummary


def _output_root() -> Path:
    """Return the configured output root directory (default ``.agentsuite``)."""
    return Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite"))


def _expose_stages() -> bool:
    """Return True if AGENTSUITE_EXPOSE_STAGES env opts in to advanced stage tools."""
    return os.environ.get("AGENTSUITE_EXPOSE_STAGES", "").lower() in {"1", "true", "yes"}


class _ServerWrapper:
    """Thin wrapper around FastMCP exposing the registered tool list for tests."""

    def __init__(self, mcp: FastMCP) -> None:
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
    mcp = FastMCP("agentsuite")
    server = _ServerWrapper(mcp)

    registry = default_registry()
    enabled = registry.enabled_names()

    # Per-agent tools
    for name in enabled:
        try:
            agent_class = registry.get_class(name)
        except Exception:
            continue
        if name == "founder":
            from agentsuite.agents.founder import mcp_tools as founder_mcp

            founder_mcp.register_tools(
                server,
                agent_class=lambda cls=agent_class: cls(output_root=_output_root()),  # type: ignore[misc]
                output_root_fn=_output_root,
                expose_stages=_expose_stages(),
            )
        elif name == "design":
            from agentsuite.agents.design import mcp_tools as design_mcp

            design_mcp.register_tools(
                server,
                agent_class=lambda cls=agent_class: cls(output_root=_output_root()),  # type: ignore[misc]
                output_root_fn=_output_root,
                expose_stages=_expose_stages(),
            )
        elif name == "product":
            from agentsuite.agents.product import mcp_tools as product_mcp

            product_mcp.register_tools(
                server,
                agent_class=lambda cls=agent_class: cls(output_root=_output_root()),  # type: ignore[misc]
                output_root_fn=_output_root,
                expose_stages=_expose_stages(),
            )
        elif name == "engineering":
            from agentsuite.agents.engineering import mcp_tools as engineering_mcp

            engineering_mcp.register_tools(
                server,
                agent_class=lambda cls=agent_class: cls(output_root=_output_root()),  # type: ignore[misc]
                output_root_fn=_output_root,
                expose_stages=_expose_stages(),
            )
        elif name == "marketing":
            from agentsuite.agents.marketing import mcp_tools as marketing_mcp

            marketing_mcp.register_tools(
                server,
                agent_class=lambda cls=agent_class: cls(output_root=_output_root()),  # type: ignore[misc]
                output_root_fn=_output_root,
                expose_stages=_expose_stages(),
            )
        elif name == "trust_risk":
            from agentsuite.agents.trust_risk import mcp_tools as trust_risk_mcp

            trust_risk_mcp.register_tools(
                server,
                agent_class=lambda cls=agent_class: cls(output_root=_output_root()),  # type: ignore[misc]
                output_root_fn=_output_root,
                expose_stages=_expose_stages(),
            )

    # Cross-agent shared tools
    def agentsuite_list_agents() -> dict[str, Any]:
        """List all enabled agents and all registered agents."""
        return {"enabled": enabled, "all_registered": sorted(registry._registered.keys())}

    def agentsuite_kernel_artifacts(project_slug: str) -> dict[str, Any]:
        """List kernel artifacts for a given project."""
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
        from agentsuite.kernel.state_store import StateStore

        runs: list[RunSummary] = []
        total = 0.0
        for d in sorted(runs_dir.iterdir()):
            if not d.is_dir():
                continue
            store = StateStore(run_dir=d)
            state = store.load()
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
    """Entry point for the ``agentsuite-mcp`` console script."""
    server = build_server()
    server.run()


if __name__ == "__main__":
    main()
