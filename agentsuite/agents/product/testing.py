"""Mock response builder for the Product agent — used by _default_mock_for_cli."""
from __future__ import annotations

import json


def build_mock_responses() -> dict[str, str]:
    from agentsuite.agents.product.stages.spec import SPEC_ARTIFACTS

    responses: dict[str, str] = {
        "extracting structured product context": json.dumps({
            "user_pain_points": ["Users spend too long on manual specification tasks"],
            "competitor_gaps": ["Competitor A lacks automated PRD generation"],
            "market_signals": ["Growing demand for AI-assisted product management"],
            "technical_constraints": ["Must integrate with existing issue trackers"],
            "assumed_non_goals": ["Mobile app", "Offline mode"],
            "open_questions": ["What is the target launch date?", "Who owns the roadmap?"],
        }),
        "checking 9 product-agent artifacts": json.dumps({
            "mismatches": [
                {"dimension": "persona_consistency", "status": "ok", "severity": "ok", "detail": "Personas consistent across PRD and story map"},
                {"dimension": "feature_roadmap_alignment", "status": "ok", "severity": "ok", "detail": "Features in prioritization match roadmap"},
            ]
        }),
        "scoring 9 product-agent": json.dumps({
            "scores": {
                "problem_clarity": 8.0,
                "user_grounding": 7.5,
                "scope_discipline": 8.0,
                "metric_specificity": 7.0,
                "feasibility_awareness": 8.0,
                "anti_feature_creep": 7.5,
                "acceptance_completeness": 8.0,
                "stakeholder_clarity": 7.0,
                "roadmap_sequencing": 8.0,
            },
            "revision_instructions": ["Clarify the success metrics timeframe"],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        key = f"writing {stem}.md for a product manager"
        responses[key] = f"# {stem.replace('-', ' ').title()}\n\nThis is the {stem} artifact for the product."
    return responses
