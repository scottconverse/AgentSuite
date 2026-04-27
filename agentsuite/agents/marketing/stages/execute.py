"""Stage 4 — execute: instantiate marketing brief-template-library with campaign-specific values."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.agents.marketing.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _values_from_extracted(inp: MarketingAgentInput, extracted: dict[str, Any]) -> dict[str, object]:
    return {
        "brand_name": inp.brand_name,
        "campaign_goal": inp.campaign_goal,
        "target_market": inp.target_market,
        "budget_range": inp.budget_range,
        "timeline": inp.timeline,
        "channels": inp.channels,
        "product_feature": extracted.get("brand_signals", [""])[0] if extracted.get("brand_signals") else "",
        "audience_segment": extracted.get("audience_insights", [""])[0] if extracted.get("audience_insights") else "",
        "call_to_action": extracted.get("channel_signals", ["Learn More"])[0] if extracted.get("channel_signals") else "Learn More",
        "platform": inp.channels.split(",")[0].strip() if inp.channels else "email",
        "metric_target": extracted.get("budget_signals", [""])[0] if extracted.get("budget_signals") else "",
        "quarter": "Q2 2026",
    }


def execute_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: instantiate 8 marketing brief templates with campaign-specific values.

    No LLM call. Reads extracted_context.json, derives Jinja2 vars, renders each
    template into ``brief-template-library/<name>.md``, writes
    ``export-manifest-template.json``, advances stage to "qa".
    """
    inp = cast(MarketingAgentInput, state.inputs)
    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )
    values = _values_from_extracted(inp, extracted)

    for name in TEMPLATE_NAMES:
        body = render_template(name, **values)
        ctx.writer.write(
            f"brief-template-library/{name}.md",
            body,
            kind="brief",
            stage="execute",
        )

    ctx.writer.write_json(
        "export-manifest-template.json",
        {
            "brand_name": inp.brand_name,
            "campaign_goal": inp.campaign_goal,
            "brief_templates": [f"{name}.md" for name in TEMPLATE_NAMES],
            "spec_artifacts": list(SPEC_ARTIFACTS),
        },
        kind="data",
        stage="execute",
    )

    return state.model_copy(update={"stage": "qa"})
