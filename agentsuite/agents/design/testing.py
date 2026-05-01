"""Mock response builder for the Design agent — used by _default_mock_for_cli."""
from __future__ import annotations

import json


def build_mock_responses() -> dict[str, str]:
    from agentsuite.agents.design.rubric import DESIGN_RUBRIC
    from agentsuite.agents.design.stages.spec import SPEC_ARTIFACTS

    responses: dict[str, str] = {
        "scoring 9 design-agent": json.dumps({
            "scores": {d.name: 8.0 for d in DESIGN_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        key = f"writing {stem}.md"
        responses[key] = f"# {stem}\n\nContent."
    return responses
