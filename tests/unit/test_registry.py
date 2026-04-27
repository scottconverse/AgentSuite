"""Unit tests for AgentRegistry API hygiene."""
import os
import pytest
from agentsuite.agents.registry import AgentRegistry, UnknownAgent


def _make_registry(*names: str) -> AgentRegistry:
    """Build a registry with stub agent classes for the given names."""
    reg = AgentRegistry()
    for name in names:
        # Use a simple lambda-class as a stub; registry only stores the class ref
        reg.register(name, type(f"{name}Agent", (), {}))  # type: ignore[arg-type]
    return reg


def test_registered_names_returns_sorted(monkeypatch):
    reg = _make_registry("zephyr", "alpha", "beta")
    assert reg.registered_names() == ["alpha", "beta", "zephyr"]


def test_registered_names_empty():
    reg = AgentRegistry()
    assert reg.registered_names() == []


def test_enabled_names_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_ENABLED_AGENTS", raising=False)
    reg = _make_registry("founder")
    assert reg.enabled_names() == ["founder"]


def test_enabled_names_from_env(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder,design")
    reg = _make_registry("founder", "design", "product")
    assert reg.enabled_names() == ["founder", "design"]


def test_enabled_names_unknown_agent_raises(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder,typo_agent")
    reg = _make_registry("founder")
    with pytest.raises(UnknownAgent, match="typo_agent"):
        reg.enabled_names()


def test_enabled_names_error_includes_registered_list(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "bad")
    reg = _make_registry("founder", "design")
    with pytest.raises(UnknownAgent, match="Registered:"):
        reg.enabled_names()


def test_no_private_registered_access_in_cli(tmp_path):
    """Verify cli.py no longer accesses reg._registered directly."""
    import re
    cli_src = (
        __import__("pathlib").Path(__file__).parent.parent.parent
        / "agentsuite" / "cli.py"
    ).read_text(encoding="utf-8")
    # Allow _registered only within registry.py itself
    matches = re.findall(r"\._registered", cli_src)
    assert matches == [], f"cli.py still accesses _registered: {matches}"
