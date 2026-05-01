"""Mock response builder for the Trust/Risk agent -- used by _default_mock_for_cli."""
from __future__ import annotations

import json


def build_mock_responses() -> dict[str, str]:
    from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC
    from agentsuite.agents.trust_risk.stages.spec import SPEC_ARTIFACTS

    responses: dict[str, str] = {
        "extracting structured trust and risk context": json.dumps({
            "threat_indicators": ["SQL injection vectors in API endpoints", "Weak credential policies"],
            "control_gaps": ["No MFA enforced", "Unpatched third-party libraries"],
            "regulatory_signals": ["GDPR Article 32 applies", "SOC 2 CC6.1 relevant"],
            "incident_patterns": ["Phishing attempt Q1 2026", "Unauthorized access attempt Q4 2025"],
            "open_questions": ["Is penetration testing scheduled?", "Who owns vendor risk reviews?"],
        }),
        "You are checking 9 trust-risk-agent artifacts for consistency. Return ONLY JSON.": json.dumps({"mismatches": []}),
        "You are scoring 9 trust-risk-agent artifacts. Return ONLY JSON.": json.dumps({
            "scores": {d.name: 8.0 for d in TRUST_RISK_RUBRIC.dimensions},
            "revision_instructions": {},
            "requires_revision": False,
        }),
    }
    for stem in SPEC_ARTIFACTS:
        key = f"writing {stem}.md for a trust and risk team"
        responses[key] = f"# {stem.replace('-', ' ').title()}\n\nMock trust/risk content."
    return responses
