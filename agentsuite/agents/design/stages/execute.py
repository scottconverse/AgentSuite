"""Stage 4 — execute: instantiate design brief-template-library with project-specific values."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _values_from_extracted(inp: DesignAgentInput, extracted: dict[str, Any]) -> dict[str, str]:
    """Map extracted_context.json fields into the design brief-template variable namespace."""
    audience_profile = extracted.get("audience_profile", {})
    primary = audience_profile.get("primary_persona", inp.target_audience)
    brand_voice = extracted.get("brand_voice", {})
    tone_words = brand_voice.get("tone_words", [])
    tone = ", ".join(tone_words) if tone_words else "neutral"
    visual_signals = extracted.get("visual_signals", [])
    visual = ", ".join(visual_signals) if visual_signals else "to be defined"
    craft_anti = extracted.get("craft_anti_patterns", [])
    exclusions = "; ".join(craft_anti) if craft_anti else "no clichés"
    forbidden = brand_voice.get("forbidden_tones", [])
    if forbidden:
        exclusions = exclusions + "; forbidden tones: " + ", ".join(forbidden)

    return {
        "product": inp.user_request,
        "target_audience": primary,
        "campaign_goal": inp.campaign_goal,
        "core_message": "(see design-brief.md)",
        "brand_voice": tone,
        "visual_direction": visual,
        "tone": tone,
        "format_constraint": f"(define per {inp.channel} asset)",
        "required_text": "(specify before draft)",
        "exclusions": exclusions,
    }


def execute_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: instantiate 8 design brief templates with project-specific values.

    No LLM call. Reads extracted_context.json, derives Jinja2 vars, renders each
    template into ``brief-template-library/<name>.md``, writes
    ``export-manifest-template.json``, advances stage to "qa".
    """
    inp = cast(DesignAgentInput, state.inputs)
    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )
    values = _values_from_extracted(inp, extracted)

    rendered: list[str] = []
    for name in TEMPLATE_NAMES:
        body = render_template(name, **values)
        ref = ctx.writer.write(
            f"brief-template-library/{name}.md",
            body,
            kind="template",
            stage="execute",
        )
        rendered.append(ref.path.name)

    ctx.writer.write_json(
        "export-manifest-template.json",
        {
            "templates": rendered,
            "values_snapshot": values,
            "ready_for": ["marketing-agent", "manual-edit"],
        },
        kind="data",
        stage="execute",
    )

    return state.model_copy(update={"stage": "qa"})
