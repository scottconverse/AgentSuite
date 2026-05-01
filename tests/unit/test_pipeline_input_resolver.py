"""Unit tests for pipeline input resolver."""
import pytest

from agentsuite.pipeline.input_resolver import get_input_class, resolve_agent_input


_COMMON = dict(
    business_goal="Launch MyApp v1",
    project_slug="myapp",
    inputs_dir=None,
)


class TestGetInputClass:
    def test_returns_class_for_all_known_agents(self):
        for name in ("founder", "design", "product", "engineering", "marketing", "trust_risk", "cio"):
            cls = get_input_class(name)
            assert cls is not None

    def test_raises_for_unknown_agent(self):
        with pytest.raises(ValueError, match="Unknown agent"):
            get_input_class("nonexistent")


class TestResolveAgentInput:
    def test_founder_basic(self):
        kwargs = resolve_agent_input("founder", **_COMMON, agent_extras={})
        assert kwargs["business_goal"] == "Launch MyApp v1"
        assert kwargs["project_slug"] == "myapp"
        assert kwargs["agent_name"] == "founder"

    def test_founder_extras_passed_through(self):
        kwargs = resolve_agent_input(
            "founder", **_COMMON,
            agent_extras={"current_state": "launched"}
        )
        assert kwargs["current_state"] == "launched"

    def test_design_basic(self):
        kwargs = resolve_agent_input("design", **_COMMON, agent_extras={})
        assert kwargs["agent_name"] == "design"
        assert kwargs["project_slug"] == "myapp"

    def test_marketing_basic(self):
        kwargs = resolve_agent_input("marketing", **_COMMON, agent_extras={})
        assert kwargs["agent_name"] == "marketing"

    def test_engineering_requires_tech_stack_and_scale(self):
        with pytest.raises(ValueError, match="tech_stack"):
            resolve_agent_input("engineering", **_COMMON, agent_extras={})

    def test_engineering_requires_scale_requirements(self):
        with pytest.raises(ValueError, match="scale_requirements"):
            resolve_agent_input(
                "engineering", **_COMMON,
                agent_extras={"tech_stack": "Python + FastAPI"}
            )

    def test_engineering_with_required_extras(self):
        kwargs = resolve_agent_input(
            "engineering", **_COMMON,
            agent_extras={
                "tech_stack": "Python + FastAPI",
                "scale_requirements": "1k RPM",
            },
        )
        assert kwargs["tech_stack"] == "Python + FastAPI"
        assert kwargs["scale_requirements"] == "1k RPM"
        assert kwargs["system_name"] == "myapp"       # defaults to project_slug
        assert kwargs["problem_domain"] == "Launch MyApp v1"  # defaults to business_goal

    def test_engineering_system_name_override(self):
        kwargs = resolve_agent_input(
            "engineering", **_COMMON,
            agent_extras={
                "tech_stack": "Go",
                "scale_requirements": "10k RPM",
                "system_name": "custom-name",
            },
        )
        assert kwargs["system_name"] == "custom-name"

    def test_trust_risk_requires_risk_domain_and_stakeholder_context(self):
        with pytest.raises(ValueError, match="risk_domain"):
            resolve_agent_input("trust_risk", **_COMMON, agent_extras={})

    def test_trust_risk_with_required_extras(self):
        kwargs = resolve_agent_input(
            "trust_risk", **_COMMON,
            agent_extras={
                "risk_domain": "SaaS application",
                "stakeholder_context": "enterprise customers",
            },
        )
        assert kwargs["risk_domain"] == "SaaS application"
        assert kwargs["product_name"] == "myapp"  # defaults to project_slug

    def test_cio_requires_it_maturity_level(self):
        with pytest.raises(ValueError, match="it_maturity_level"):
            resolve_agent_input("cio", **_COMMON, agent_extras={})

    def test_cio_with_required_extras(self):
        kwargs = resolve_agent_input(
            "cio", **_COMMON,
            agent_extras={"it_maturity_level": "Level 2 - Repeatable"},
        )
        assert kwargs["it_maturity_level"] == "Level 2 - Repeatable"
        assert kwargs["organization_name"] == "myapp"
        assert kwargs["strategic_priorities"] == "Launch MyApp v1"

    def test_inputs_dir_included_when_set(self, tmp_path):
        kwargs = resolve_agent_input(
            "founder", business_goal="x", project_slug="p",
            inputs_dir=tmp_path, agent_extras={}
        )
        assert kwargs["inputs_dir"] == tmp_path

    def test_inputs_dir_absent_when_none(self):
        kwargs = resolve_agent_input("founder", **_COMMON, agent_extras={})
        assert "inputs_dir" not in kwargs

    def test_error_message_includes_example(self):
        with pytest.raises(ValueError, match="Example:"):
            resolve_agent_input("engineering", **_COMMON, agent_extras={})
