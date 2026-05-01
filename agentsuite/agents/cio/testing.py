"""Mock response builder for the CIO agent -- used by _default_mock_for_cli."""
from __future__ import annotations

import json


def build_mock_responses() -> dict[str, str]:
    from agentsuite.agents.cio.rubric import CIO_RUBRIC
    from agentsuite.agents.cio.stages.spec import SPEC_ARTIFACTS

    responses: dict[str, str] = {
        "You are indexing IT source materials for a CIO strategy assessment.": "Indexed IT source materials. Ready to extract context.",
        "You are extracting structured IT and technology context from documents. Return ONLY valid JSON.": json.dumps({
            "technology_pain_points": ["Legacy ERP on-premise with high maintenance cost"],
            "strategic_gaps": ["No cloud adoption strategy", "Weak data governance"],
            "vendor_landscape": ["SAP ERP", "Microsoft 365", "AWS (limited use)"],
            "digital_maturity_signals": ["Ad-hoc project management", "Limited self-service analytics"],
            "budget_signals": ["Flat IT budget YoY", "Capex-heavy spend profile"],
            "open_questions": ["Is cloud migration a board priority?", "Who owns the data strategy?"],
        }),
        "You are checking 9 CIO artifacts for consistency. Return ONLY JSON.": json.dumps({"mismatches": []}),
        "You are scoring 9 CIO artifacts. Return ONLY JSON.": json.dumps({
            "scores": {d.name: 8.0 for d in CIO_RUBRIC.dimensions},
            "revision_instructions": {},
            "requires_revision": False,
        }),
    }
    for stem in SPEC_ARTIFACTS:
        key = f"writing {stem}.md for a CIO team"
        responses[key] = f"# {stem.replace('-', ' ').title()}\n\nMock CIO content."
    return responses
