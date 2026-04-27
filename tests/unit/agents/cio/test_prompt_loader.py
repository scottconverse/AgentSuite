"""Unit tests for agentsuite.agents.cio.prompt_loader."""
from __future__ import annotations

import pytest

from agentsuite.agents.cio.prompt_loader import (
    UnknownPrompt,
    list_prompts,
    render_prompt,
)

EXPECTED_PROMPT_NAMES = [
    "extract",
    "intake",
    "qa_score",
    "spec_budget_allocation_model",
    "spec_consistency_check",
    "spec_digital_transformation_plan",
    "spec_enterprise_architecture",
    "spec_it_governance_framework",
    "spec_it_risk_appetite_statement",
    "spec_it_strategy",
    "spec_technology_roadmap",
    "spec_vendor_portfolio",
    "spec_workforce_development_plan",
]


def test_list_prompts_returns_13() -> None:
    """list_prompts returns exactly 13 templates."""
    prompts = list_prompts()
    assert len(prompts) == 13, f"Expected 13, got {len(prompts)}: {prompts}"


def test_list_prompts_contains_all_names() -> None:
    """All 13 expected prompt names are present."""
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
        organization_name="AcmeCorp",
        strategic_priorities="cloud migration, cost reduction",
        it_maturity_level="developing",
        source_count=5,
    )
    assert "AcmeCorp" in result
    assert "cloud migration" in result


def test_render_extract() -> None:
    """extract template renders with required variables and contains JSON instruction."""
    result = render_prompt(
        "extract",
        organization_name="AcmeCorp",
        strategic_priorities="digital transformation",
        it_maturity_level="developing",
        source_count=3,
        it_docs="IT strategy 2023, cloud roadmap draft",
    )
    assert "AcmeCorp" in result
    assert "technology_pain_points" in result
    assert "strategic_gaps" in result
    assert "vendor_landscape" in result
    assert "digital_maturity_signals" in result
    assert "budget_signals" in result
    assert "open_questions" in result


def test_render_qa_score() -> None:
    """qa_score template renders with required variables and 9 scoring dimensions."""
    artifact_snippets = {
        "it-strategy": "Three-year IT strategy focused on cloud adoption.",
        "technology-roadmap": "Migrate ERP to cloud by Q4 2026.",
    }
    result = render_prompt(
        "qa_score",
        organization_name="AcmeCorp",
        strategic_priorities="cloud migration",
        artifact_snippets=artifact_snippets,
    )
    assert "AcmeCorp" in result
    assert "strategic_alignment" in result
    assert "technology_debt_awareness" in result
    assert "vendor_discipline" in result
    assert "digital_readiness" in result
    assert "governance_maturity" in result
    assert "budget_realism" in result
    assert "workforce_capability" in result
    assert "risk_tolerance_clarity" in result
    assert "innovation_balance" in result


def test_render_spec_consistency_check_uses_items() -> None:
    """spec_consistency_check iterates artifact_snippets as a dict via .items()."""
    artifact_snippets = {
        "it-strategy": "Prioritize cloud-first architecture.",
        "technology-roadmap": "ERP migration to cloud by 2026.",
    }
    result = render_prompt(
        "spec_consistency_check",
        organization_name="AcmeCorp",
        strategic_priorities="cloud-first",
        artifact_snippets=artifact_snippets,
    )
    assert "it-strategy" in result
    assert "technology-roadmap" in result
    assert "cloud" in result


def test_render_spec_it_strategy() -> None:
    """spec_it_strategy renders with required variables."""
    result = render_prompt(
        "spec_it_strategy",
        organization_name="AcmeCorp",
        strategic_priorities="cloud migration, AI adoption",
        it_maturity_level="managed",
        extracted_context="legacy ERP, fragmented vendor landscape",
        budget_context="$10M annual IT budget",
        digital_initiatives="customer portal, data warehouse",
        regulatory_environment="SOC 2, GDPR",
    )
    assert "AcmeCorp" in result
    assert "IT Strategy" in result


def test_render_spec_technology_roadmap() -> None:
    """spec_technology_roadmap renders with required variables."""
    result = render_prompt(
        "spec_technology_roadmap",
        organization_name="AcmeCorp",
        strategic_priorities="modernization",
        it_maturity_level="developing",
        extracted_context="legacy on-prem ERP, 15-year-old data center",
        budget_context="$8M annual",
        digital_initiatives="ERP modernization",
        regulatory_environment="PCI-DSS",
    )
    assert "AcmeCorp" in result
    assert "Roadmap" in result


def test_render_spec_enterprise_architecture() -> None:
    """spec_enterprise_architecture renders with required variables."""
    result = render_prompt(
        "spec_enterprise_architecture",
        organization_name="AcmeCorp",
        strategic_priorities="API-led integration",
        it_maturity_level="managed",
        extracted_context="30+ point-to-point integrations",
        budget_context="$12M",
        digital_initiatives="API gateway, microservices migration",
        regulatory_environment="SOC 2",
    )
    assert "AcmeCorp" in result
    assert "Architecture" in result


def test_render_spec_digital_transformation_plan() -> None:
    """spec_digital_transformation_plan renders with required variables."""
    result = render_prompt(
        "spec_digital_transformation_plan",
        organization_name="AcmeCorp",
        strategic_priorities="customer experience, automation",
        it_maturity_level="developing",
        extracted_context="manual approval workflows, paper-based processes",
        budget_context="$5M transformation budget",
        digital_initiatives="customer portal, RPA",
        regulatory_environment="GDPR",
    )
    assert "AcmeCorp" in result
    assert "Digital" in result


def test_render_spec_it_governance_framework() -> None:
    """spec_it_governance_framework renders with required variables."""
    result = render_prompt(
        "spec_it_governance_framework",
        organization_name="AcmeCorp",
        strategic_priorities="governance, risk management",
        it_maturity_level="initial",
        extracted_context="no formal IT steering committee",
        budget_context="$6M",
        digital_initiatives="ERP upgrade",
        regulatory_environment="SOX, ISO 27001",
    )
    assert "AcmeCorp" in result
    assert "Governance" in result


def test_render_spec_vendor_portfolio() -> None:
    """spec_vendor_portfolio renders with required variables."""
    result = render_prompt(
        "spec_vendor_portfolio",
        organization_name="AcmeCorp",
        strategic_priorities="vendor consolidation",
        it_maturity_level="managed",
        extracted_context="87 active vendors, heavy SAP and Salesforce dependency",
        budget_context="$4M vendor spend",
        digital_initiatives="platform consolidation",
        regulatory_environment="GDPR",
    )
    assert "AcmeCorp" in result
    assert "Vendor" in result


def test_render_spec_workforce_development_plan() -> None:
    """spec_workforce_development_plan renders with required variables."""
    result = render_prompt(
        "spec_workforce_development_plan",
        organization_name="AcmeCorp",
        strategic_priorities="cloud skills, data engineering",
        it_maturity_level="developing",
        extracted_context="50% of staff on legacy mainframe skills",
        budget_context="$2M L&D budget",
        digital_initiatives="cloud migration",
        regulatory_environment="none",
    )
    assert "AcmeCorp" in result
    assert "Workforce" in result


def test_render_spec_budget_allocation_model() -> None:
    """spec_budget_allocation_model renders with required variables."""
    result = render_prompt(
        "spec_budget_allocation_model",
        organization_name="AcmeCorp",
        strategic_priorities="transformation investment",
        it_maturity_level="managed",
        extracted_context="80% run spend, 15% grow, 5% transform",
        budget_context="$15M total IT budget",
        digital_initiatives="cloud migration, AI",
        regulatory_environment="SOC 2",
    )
    assert "AcmeCorp" in result
    assert "Budget" in result


def test_render_spec_it_risk_appetite_statement() -> None:
    """spec_it_risk_appetite_statement renders with required variables."""
    result = render_prompt(
        "spec_it_risk_appetite_statement",
        organization_name="AcmeCorp",
        strategic_priorities="security, resilience",
        it_maturity_level="managed",
        extracted_context="two major outages in 2023, PCI-DSS audit finding",
        budget_context="$3M security budget",
        digital_initiatives="zero-trust network",
        regulatory_environment="PCI-DSS, SOC 2",
    )
    assert "AcmeCorp" in result
    assert "Risk" in result


def test_unknown_prompt_raises() -> None:
    """render_prompt raises UnknownPrompt for a non-existent template name."""
    with pytest.raises(UnknownPrompt):
        render_prompt("does_not_exist", foo="bar")


def test_unknown_prompt_is_key_error() -> None:
    """UnknownPrompt is a subclass of KeyError for backward compatibility."""
    assert issubclass(UnknownPrompt, KeyError)
