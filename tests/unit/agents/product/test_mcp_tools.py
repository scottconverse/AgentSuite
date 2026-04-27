"""Unit tests for product.mcp_tools."""
from __future__ import annotations

from pathlib import Path

from agentsuite.agents.product.mcp_tools import ProductRunRequest, register_tools
from agentsuite.mcp_server import build_server


class _StubServer:
    def __init__(self) -> None:
        self.tools: dict = {}

    def add_tool(self, name: str, fn) -> None:
        self.tools[name] = fn

    def tool_names(self) -> list[str]:
        return list(self.tools.keys())


def test_product_mcp_tools_registered() -> None:
    """build_server() registers product_run when product agent is enabled."""
    import os
    import agentsuite.agents.registry as reg_module

    # Reset singleton so bootstrap picks up our env
    reg_module._DEFAULT_REGISTRY = None
    os.environ["AGENTSUITE_ENABLED_AGENTS"] = "product"

    server = build_server()
    assert "product_run" in server.tool_names()

    # Restore
    reg_module._DEFAULT_REGISTRY = None


def test_product_run_request_defaults() -> None:
    """ProductRunRequest can be instantiated with no required positional args."""
    req = ProductRunRequest()
    assert req.user_request == "run product agent"
    assert req.product_name == "My Product"
    assert req.target_users == "target users"
    assert req.core_problem == "problem to solve"
    assert req.run_id is None


def test_product_list_runs_filters_by_agent(tmp_path: Path) -> None:
    """product_list_runs only returns runs whose state.agent == 'product'."""
    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.state_store import StateStore
    from agentsuite.agents.product.input_schema import ProductAgentInput

    shared_input = ProductAgentInput(
        agent_name="product",
        role_domain="product",
        user_request="req",
        product_name="P",
        target_users="users",
        core_problem="problem",
    )

    # Write a product run
    product_run_dir = tmp_path / "runs" / "run-product-001"
    product_run_dir.mkdir(parents=True)
    product_state = RunState(
        run_id="run-product-001",
        agent="product",
        stage="spec",
        inputs=shared_input,
        cost_so_far=Cost(),
    )
    StateStore(run_dir=product_run_dir).save(product_state)

    # Write a non-product run (design)
    other_run_dir = tmp_path / "runs" / "run-design-001"
    other_run_dir.mkdir(parents=True)
    other_state = RunState(
        run_id="run-design-001",
        agent="design",
        stage="spec",
        inputs=shared_input,
        cost_so_far=Cost(),
    )
    StateStore(run_dir=other_run_dir).save(other_state)

    # Register tools against tmp_path
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: None,  # not needed for list_runs
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )

    runs = server.tools["product_list_runs"]()
    assert len(runs) == 1
    assert runs[0].run_id == "run-product-001"
    assert runs[0].agent == "product"
