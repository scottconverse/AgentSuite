"""Mock response builder for the Marketing agent — used by _default_mock_for_cli."""
from __future__ import annotations

import json


def build_mock_responses() -> dict[str, str]:
    from agentsuite.agents.marketing.stages.spec import SPEC_ARTIFACTS

    responses: dict[str, str] = {
        "You are extracting structured marketing context from brand and competitor documents. Return ONLY valid JSON.": json.dumps({
            "audience_insights": ["SMBs"],
            "competitor_gaps": ["pricing"],
            "brand_signals": ["innovative"],
            "channel_signals": ["email"],
            "budget_signals": ["$10k"],
            "open_questions": [],
        }),
        "You are checking 9 marketing-agent artifacts for consistency. Return ONLY JSON.": json.dumps({"mismatches": []}),
        "You are scoring 9 marketing-agent artifacts. Return ONLY JSON.": json.dumps({
            "scores": {
                "audience_clarity": 8.0, "message_resonance": 8.0, "channel_fit": 8.0,
                "metric_specificity": 8.0, "budget_realism": 8.0, "anti_vanity_metrics": 8.0,
                "content_depth": 8.0, "competitive_awareness": 8.0, "launch_sequencing": 8.0,
            },
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        key = f"writing {stem}.md for a marketing team"
        responses[key] = f"# {stem.replace('-', ' ').title()}\n\nMock marketing content."
    return responses
