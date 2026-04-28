"""Unit tests for agents.registry."""
import pytest

from agentsuite.agents.registry import AgentRegistry, UnknownAgent


def test_registry_lists_only_enabled_agents(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    reg = AgentRegistry()
    reg._registered["founder"] = object  # type: ignore[assignment]
    assert reg.enabled_names() == ["founder"]


def test_registry_defaults_to_founder_only(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_ENABLED_AGENTS", raising=False)
    reg = AgentRegistry()
    reg._registered["founder"] = object  # type: ignore[assignment]
    assert reg.enabled_names() == ["founder"]


def test_registry_supports_comma_separated(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder,design,product")
    reg = AgentRegistry()
    for name in ("founder", "design", "product"):
        reg._registered[name] = object  # type: ignore[assignment]
    assert reg.enabled_names() == ["founder", "design", "product"]


def test_registry_strips_whitespace(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder, design ,  product")
    reg = AgentRegistry()
    for name in ("founder", "design", "product"):
        reg._registered[name] = object  # type: ignore[assignment]
    assert reg.enabled_names() == ["founder", "design", "product"]


def test_enabled_names_raises_on_unregistered_even_when_registry_empty(monkeypatch):
    """Validation is unconditional — empty registry rejects any env-listed agent."""
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    reg = AgentRegistry()
    with pytest.raises(UnknownAgent, match="founder"):
        reg.enabled_names()


def test_get_agent_class_raises_for_unknown(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    reg = AgentRegistry()
    with pytest.raises(UnknownAgent):
        reg.get_class("doesnotexist")


def test_get_agent_class_raises_for_disabled(monkeypatch):
    """Even if the agent module exists, disabled agents are not returned."""
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    reg = AgentRegistry()
    # Pretend "design" is registered in code but disabled via env
    reg._registered["design"] = object  # type: ignore[assignment]
    with pytest.raises(UnknownAgent):
        reg.get_class("design")


def test_default_registry_has_design_registered(monkeypatch):
    """DesignAgent is registered in bootstrap registry (accessible when enabled)."""
    from agentsuite.agents.registry import default_registry
    import agentsuite.agents.registry as reg_mod
    reg_mod._DEFAULT_REGISTRY = None  # reset singleton
    reg = default_registry()
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder,design")
    assert "design" in reg._registered


def test_design_agent_class_accessible_via_registry(monkeypatch):
    from agentsuite.agents.design.agent import DesignAgent
    from agentsuite.agents.registry import AgentRegistry
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "design")
    reg = AgentRegistry()
    reg.register("design", DesignAgent)
    cls = reg.get_class("design")
    assert cls is DesignAgent


def test_register_rejects_duplicate_name():
    """register() raises ValueError when the same name is registered twice."""
    reg = AgentRegistry()
    reg.register("founder", object)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="already registered"):
        reg.register("founder", object)  # type: ignore[arg-type]


def test_all_seven_default_agents_register_without_error():
    """bootstrap registry registers all 7 agents without hitting the duplicate guard."""
    from agentsuite.agents.registry import _bootstrap_default_registry
    reg = _bootstrap_default_registry()
    assert set(reg.registered_names()) == {
        "founder", "design", "product", "engineering", "marketing", "trust_risk", "cio"
    }
