"""Stage 4 — execute: instantiate brief-template-library with project-specific values."""
from __future__ import annotations

import json
from typing import cast

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _values_from_extracted(inp: FounderAgentInput, extracted: dict) -> dict[str, str]:
    """Map extracted_context.json fields into the brief-template variable namespace."""
    audience = extracted.get("audience", {})
    primary = audience.get("primary_persona", "the target audience")
    tone = ", ".join(extracted.get("tone_signals", [])) or "neutral"
    visual = ", ".join(extracted.get("visual_signals", [])) or "to be defined"
    claims = "; ".join(extracted.get("recurring_claims", [])) or "(see claims-and-proof-library.md)"
    return {
        "product": inp.business_goal,
        "audience": primary,
        "core_message": extracted.get("positioning", "(see product-positioning.md)"),
        "proof": claims,
        "visual_metaphor": visual,
        "tone": tone,
        "format_constraint": "(define per asset)",
        "required_text": "(specify before draft)",
        "exclusions": "; ".join(extracted.get("prohibited_language", [])) or "no clichés",
    }


def execute_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: instantiate the 11 brief templates with values from extracted_context.

    No LLM call. Reads extracted_context.json, derives Jinja vars, renders each
    template into ``brief-template-library/<name>.md``, writes
    ``export-manifest-template.json``, advances stage to "qa".
    """
    inp = cast(FounderAgentInput, state.inputs)
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
            "ready_for": ["design-agent", "marketing-agent", "manual-edit"],
        },
        kind="data",
        stage="execute",
    )

    return state.model_copy(update={"stage": "qa"})
