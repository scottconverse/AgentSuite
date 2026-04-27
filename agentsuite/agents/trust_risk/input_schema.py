"""Input schema for the Trust/Risk Agent."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from agentsuite.kernel.schema import AgentRequest


class TrustRiskAgentInput(AgentRequest):
    product_name: str                              # name of the product or system being assessed
    risk_domain: str                               # domain of risk being evaluated (e.g. cloud infra, SaaS app)
    stakeholder_context: str                       # who is affected and what their risk tolerance is
    inputs_dir: Optional[Path] = None              # existing policy docs, audit reports, threat models
    existing_policies: list[Path] = []             # security policies, data governance docs, access control specs
    incident_reports: list[Path] = []              # past incident reports, post-mortems, vulnerability disclosures
    regulatory_context: str = ""                   # e.g. "SOC 2 Type II, HIPAA, GDPR"
    threat_model_scope: str = ""                   # e.g. "external attackers, insider threats, supply chain"
    compliance_frameworks: str = ""                # e.g. "NIST CSF, ISO 27001, CIS Controls"
    agent_name: str = "trust_risk"
    role_domain: str = "trust-risk-ops"
