"""Agent registry with env-driven enablement."""
from __future__ import annotations

import os
from typing import Type

from agentsuite.kernel.base_agent import BaseAgent


class UnknownAgent(KeyError):
    """Raised when an agent name is not registered or not enabled."""


class AgentRegistry:
    """Maps agent names to BaseAgent subclasses, gated by AGENTSUITE_ENABLED_AGENTS env."""

    DEFAULT_ENABLED = "founder"

    def __init__(self) -> None:
        self._registered: dict[str, Type[BaseAgent]] = {}

    def register(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register a concrete agent class under ``name``."""
        self._registered[name] = agent_class

    def enabled_names(self) -> list[str]:
        """Return enabled agent names from AGENTSUITE_ENABLED_AGENTS env (or default)."""
        raw = os.environ.get("AGENTSUITE_ENABLED_AGENTS", self.DEFAULT_ENABLED)
        return [n.strip() for n in raw.split(",") if n.strip()]

    def get_class(self, name: str) -> Type[BaseAgent]:
        """Return the registered class for ``name``. Raises UnknownAgent if disabled or unregistered."""
        if name not in self.enabled_names():
            raise UnknownAgent(f"Agent '{name}' is not enabled or not registered")
        if name not in self._registered:
            raise UnknownAgent(f"Agent '{name}' is not registered")
        return self._registered[name]


def _bootstrap_default_registry() -> AgentRegistry:
    from agentsuite.agents.cio.agent import CIOAgent
    from agentsuite.agents.design.agent import DesignAgent
    from agentsuite.agents.engineering.agent import EngineeringAgent
    from agentsuite.agents.founder.agent import FounderAgent
    from agentsuite.agents.marketing.agent import MarketingAgent
    from agentsuite.agents.product.agent import ProductAgent
    from agentsuite.agents.trust_risk.agent import TrustRiskAgent

    reg = AgentRegistry()
    reg.register("founder", FounderAgent)
    reg.register("design", DesignAgent)
    reg.register("product", ProductAgent)
    reg.register("engineering", EngineeringAgent)
    reg.register("marketing", MarketingAgent)
    reg.register("trust_risk", TrustRiskAgent)
    reg.register("cio", CIOAgent)
    return reg


_DEFAULT_REGISTRY: AgentRegistry | None = None


def default_registry() -> AgentRegistry:
    """Return the singleton default registry with built-in agents pre-registered."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = _bootstrap_default_registry()
    return _DEFAULT_REGISTRY
