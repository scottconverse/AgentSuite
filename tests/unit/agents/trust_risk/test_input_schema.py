"""Unit tests for trust_risk.input_schema."""
import pytest
from pydantic import ValidationError

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput


def test_minimal_inputs_construct():
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="assess the risk posture of our cloud infrastructure",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering and security teams with low risk tolerance",
    )
    assert inp.product_name == "CloudPlatform"
    assert inp.risk_domain == "cloud infrastructure"
    assert inp.stakeholder_context == "engineering and security teams with low risk tolerance"


def test_product_name_required():
    with pytest.raises(ValidationError):
        TrustRiskAgentInput(
            agent_name="trust_risk",
            role_domain="trust-risk-ops",
            user_request="x",
            risk_domain="cloud infrastructure",
            stakeholder_context="engineering team",
        )


def test_risk_domain_required():
    with pytest.raises(ValidationError):
        TrustRiskAgentInput(
            agent_name="trust_risk",
            role_domain="trust-risk-ops",
            user_request="x",
            product_name="CloudPlatform",
            stakeholder_context="engineering team",
        )


def test_stakeholder_context_required():
    with pytest.raises(ValidationError):
        TrustRiskAgentInput(
            agent_name="trust_risk",
            role_domain="trust-risk-ops",
            user_request="x",
            product_name="CloudPlatform",
            risk_domain="cloud infrastructure",
        )


def test_agent_name_defaults_to_trust_risk():
    inp = TrustRiskAgentInput(
        user_request="x",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering team",
    )
    assert inp.agent_name == "trust_risk"


def test_inputs_dir_defaults_to_none():
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="x",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering team",
    )
    assert inp.inputs_dir is None


def test_existing_policies_defaults_to_empty():
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="x",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering team",
    )
    assert inp.existing_policies == []


def test_incident_reports_defaults_to_empty():
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="x",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering team",
    )
    assert inp.incident_reports == []


def test_regulatory_context_defaults_to_empty_string():
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="x",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering team",
    )
    assert inp.regulatory_context == ""


def test_threat_model_scope_defaults_to_empty_string():
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="x",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering team",
    )
    assert inp.threat_model_scope == ""


def test_compliance_frameworks_defaults_to_empty_string():
    inp = TrustRiskAgentInput(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="x",
        product_name="CloudPlatform",
        risk_domain="cloud infrastructure",
        stakeholder_context="engineering team",
    )
    assert inp.compliance_frameworks == ""
