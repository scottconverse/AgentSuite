"""Unit tests for agentsuite.agents.trust_risk.prompt_loader."""
from __future__ import annotations

import pytest

from agentsuite.agents.trust_risk.prompt_loader import (
    UnknownPrompt,
    list_prompts,
    render_prompt,
)

EXPECTED_PROMPT_NAMES = [
    "extract",
    "intake",
    "spec_audit_readiness_report",
    "spec_compliance_matrix",
    "spec_consistency_check",
    "spec_control_framework",
    "spec_incident_response_plan",
    "spec_residual_risk_acceptance",
    "spec_risk_register",
    "spec_security_policy",
    "spec_threat_model",
    "spec_vendor_risk_assessment",
]


def test_list_prompts_count() -> None:
    """list_prompts returns exactly 12 templates."""
    prompts = list_prompts()
    assert len(prompts) == 12, f"Expected 12, got {len(prompts)}: {prompts}"


def test_list_prompts_contains_all_names() -> None:
    """All 12 expected prompt names are present."""
    prompts = list_prompts()
    for name in EXPECTED_PROMPT_NAMES:
        assert name in prompts, f"Missing expected prompt: {name}"


def test_list_prompts_is_sorted() -> None:
    """list_prompts returns names in sorted order."""
    prompts = list_prompts()
    assert prompts == sorted(prompts)


def test_render_intake() -> None:
    """intake template renders with required variables."""
    result = render_prompt(
        "intake",
        product_name="AcmePay",
        risk_domain="financial services",
        stakeholder_context="CISO and CFO",
        source_count=5,
    )
    assert "AcmePay" in result
    assert "financial services" in result


def test_render_extract() -> None:
    """extract template renders with required variables and contains JSON instruction."""
    result = render_prompt(
        "extract",
        product_name="AcmePay",
        risk_domain="financial services",
        stakeholder_context="CISO",
        source_count=3,
        existing_policies="Password policy, AUP",
        incident_reports="2023-Q4 phishing incident",
    )
    assert "AcmePay" in result
    assert "known_threats" in result
    assert "compliance_gaps" in result


def test_render_spec_threat_model() -> None:
    """spec_threat_model template renders with required variables."""
    result = render_prompt(
        "spec_threat_model",
        product_name="AcmePay",
        risk_domain="fintech",
        stakeholder_context="Security team",
        regulatory_context="PCI-DSS, SOC 2",
        threat_model_scope="Payment processing pipeline",
        compliance_frameworks="PCI-DSS v4, SOC 2 Type II",
        extracted_context="known_threats: [account takeover]",
    )
    assert "AcmePay" in result
    assert "STRIDE" in result


def test_render_spec_consistency_check_uses_items() -> None:
    """spec_consistency_check iterates artifact_snippets as a dict via .items()."""
    artifact_snippets = {
        "threat-model": "Threats include SQL injection.",
        "risk-register": "SQL injection rated High.",
    }
    result = render_prompt(
        "spec_consistency_check",
        product_name="AcmePay",
        risk_domain="fintech",
        artifact_snippets=artifact_snippets,
    )
    assert "threat-model" in result
    assert "risk-register" in result
    assert "SQL injection" in result


def test_render_spec_risk_register() -> None:
    """spec_risk_register renders with required variables."""
    result = render_prompt(
        "spec_risk_register",
        product_name="AcmePay",
        risk_domain="fintech",
        stakeholder_context="Risk committee",
        regulatory_context="SOC 2",
        threat_model_scope="Full stack",
        compliance_frameworks="SOC 2 Type II",
        extracted_context="vendor_risks: [cloud provider outage]",
    )
    assert "AcmePay" in result
    assert "Risk Register" in result


def test_render_spec_control_framework() -> None:
    """spec_control_framework renders with required variables."""
    result = render_prompt(
        "spec_control_framework",
        product_name="AcmePay",
        risk_domain="fintech",
        stakeholder_context="IT Security",
        regulatory_context="SOC 2, ISO 27001",
        threat_model_scope="Cloud infrastructure",
        compliance_frameworks="ISO 27001, SOC 2",
        extracted_context="existing_controls: [MFA, WAF]",
    )
    assert "AcmePay" in result
    assert "Control" in result


def test_render_spec_compliance_matrix() -> None:
    """spec_compliance_matrix renders with required variables."""
    result = render_prompt(
        "spec_compliance_matrix",
        product_name="AcmePay",
        risk_domain="fintech",
        stakeholder_context="Compliance team",
        regulatory_context="GDPR, PCI-DSS",
        threat_model_scope="Payment data",
        compliance_frameworks="GDPR, PCI-DSS v4",
        extracted_context="compliance_gaps: [data retention policy missing]",
    )
    assert "AcmePay" in result
    assert "Compliance" in result


def test_unknown_prompt_raises() -> None:
    """render_prompt raises UnknownPrompt for a non-existent template name."""
    with pytest.raises(UnknownPrompt):
        render_prompt("does_not_exist", foo="bar")


def test_unknown_prompt_is_key_error() -> None:
    """UnknownPrompt is a subclass of KeyError for backward compatibility."""
    assert issubclass(UnknownPrompt, KeyError)
