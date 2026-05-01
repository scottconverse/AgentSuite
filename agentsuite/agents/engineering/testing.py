"""Mock response builder for the Engineering agent -- used by _default_mock_for_cli."""
from __future__ import annotations

import json


def build_mock_responses() -> dict[str, str]:
    from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC
    from agentsuite.agents.engineering.stages.spec import SPEC_ARTIFACTS

    responses: dict[str, str] = {
        "extracting structured engineering context": json.dumps({
            "existing_patterns": ["Repository pattern for data access", "Event-driven messaging via queues"],
            "known_bottlenecks": ["Database connection pool exhaustion under peak load"],
            "security_risks": ["Unvalidated input in public API endpoints"],
            "tech_debt_items": ["Legacy synchronous HTTP client blocking async event loop"],
            "integration_points": ["Payment gateway", "Identity provider (OIDC)"],
            "open_questions": ["What is the target SLA for batch jobs?", "Is multi-region deployment required?"],
        }),
        "checking 9 engineering-agent artifacts": json.dumps({"mismatches": []}),
        "scoring 9 engineering-agent": json.dumps({
            "scores": {d.name: 8.0 for d in ENGINEERING_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        key = f"writing {stem}.md for an engineering team"
        responses[key] = f"# {stem}\n\nMock engineering content."
    return responses
