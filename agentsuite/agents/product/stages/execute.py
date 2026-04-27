"""Stage 4 — execute: instantiate product brief-template-library with project-specific values."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _values_from_extracted(inp: ProductAgentInput, extracted: dict[str, Any]) -> dict[str, str]:
    """Map extracted_context.json fields into the product brief-template variable namespace."""
    pain_points = extracted.get("user_pain_points", [])
    key_feature = pain_points[0] if pain_points else inp.core_problem

    return {
        "product_name": inp.product_name,
        "target_users": inp.target_users,
        "core_problem": inp.core_problem,
        "success_metric_goals": inp.success_metric_goals,
        "timeline_constraint": inp.timeline_constraint,
        "key_feature": key_feature,
        "audience": inp.target_users,
        "channel": "all",
        "call_to_action": f"Try {inp.product_name} today",
    }


def execute_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: instantiate 8 product brief templates with project-specific values.

    No LLM call. Reads extracted_context.json, derives Jinja2 vars, renders each
    template into ``brief-template-library/<name>.md``, writes
    ``export-manifest-template.json``, advances stage to "qa".
    """
    inp = cast(ProductAgentInput, state.inputs)
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
            kind="brief",
            stage="execute",
        )
        rendered.append(ref.path.name)

    spec_artifacts = [
        p.name
        for p in (ctx.writer.run_dir).glob("*.md")
    ]

    ctx.writer.write_json(
        "export-manifest-template.json",
        {
            "product_name": inp.product_name,
            "target_users": inp.target_users,
            "brief_templates": [f"{name}.md" for name in TEMPLATE_NAMES],
            "spec_artifacts": spec_artifacts,
        },
        kind="data",
        stage="execute",
    )

    return state.model_copy(update={"stage": "qa"})
