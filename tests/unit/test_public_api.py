"""Verify public API surface is importable from the top-level package."""
import agentsuite


def test_all_agent_classes_importable():
    for name in [
        "FounderAgent",
        "DesignAgent",
        "ProductAgent",
        "EngineeringAgent",
        "MarketingAgent",
        "TrustRiskAgent",
        "CIOAgent",
    ]:
        assert hasattr(agentsuite, name), f"Missing from public API: {name}"


def test_kernel_types_importable():
    assert hasattr(agentsuite, "BaseAgent")
    assert hasattr(agentsuite, "AgentRequest")
    assert hasattr(agentsuite, "RunState")
    assert hasattr(agentsuite, "ArtifactWriter")


def test_registry_importable():
    assert hasattr(agentsuite, "AgentRegistry")
    assert hasattr(agentsuite, "default_registry")


def test_llm_types_importable():
    assert hasattr(agentsuite, "LLMProvider")
    assert hasattr(agentsuite, "ProviderNotInstalled")


def test_direct_import():
    from agentsuite import FounderAgent, DesignAgent, CIOAgent  # noqa: F401
