"""Unit tests for agents.registry."""
import pytest

from agentsuite.agents.registry import AgentRegistry, UnknownAgent


def test_registry_lists_only_enabled_agents(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    reg = AgentRegistry()
    assert reg.enabled_names() == ["founder"]


def test_registry_defaults_to_founder_only(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_ENABLED_AGENTS", raising=False)
    reg = AgentRegistry()
    assert reg.enabled_names() == ["founder"]


def test_registry_supports_comma_separated(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder,design,product")
    reg = AgentRegistry()
    assert reg.enabled_names() == ["founder", "design", "product"]


def test_registry_strips_whitespace(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder, design ,  product")
    reg = AgentRegistry()
    assert reg.enabled_names() == ["founder", "design", "product"]


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
