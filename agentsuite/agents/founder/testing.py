"""Mock response builder for the Founder agent — used by _default_mock_for_cli."""
from __future__ import annotations

import json


def build_mock_responses() -> dict[str, str]:
    from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
    from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS

    _extracted = {
        "mission": "x",
        "audience": {"primary_persona": "y", "secondary_personas": []},
        "positioning": "z",
        "tone_signals": ["practical"],
        "visual_signals": [],
        "recurring_claims": [],
        "recurring_vocabulary": [],
        "prohibited_language": [],
        "gaps": [],
        # Design extract fields — shared via "extracting" key; extra keys ignored by Founder parser
        "audience_profile": {"primary_persona": "target user"},
        "brand_voice": {"tone_words": ["confident"], "writing_style": "terse", "forbidden_tones": []},
        "typography_signals": {"heading_style": "sans-serif"},
        "color_palette_observed": [],
        "craft_anti_patterns": [],
    }
    responses: dict[str, str] = {
        "extracting": json.dumps(_extracted),
        "checking 9 artifacts": json.dumps({"mismatches": []}),
        "scoring 9 founder": json.dumps({
            "scores": {d.name: 8.0 for d in FOUNDER_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\nMocked content."
    return responses
