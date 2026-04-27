"""Stage 4 — execute: instantiate engineering brief-template-library with project-specific values."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.agents.engineering.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _values_from_extracted(inp: EngineeringAgentInput, extracted: dict[str, Any]) -> dict[str, object]:
    bottlenecks = extracted.get("known_bottlenecks", [])
    component = bottlenecks[0] if bottlenecks else inp.problem_domain
    return {
        "system_name": inp.system_name,
        "problem_domain": inp.problem_domain,
        "tech_stack": inp.tech_stack,
        "scale_requirements": inp.scale_requirements,
        "team_size": inp.team_size,
        "component": str(component),
        "incident_title": f"{inp.system_name} incident",
        "severity": "SEV-2",
        "vendor_name": "TBD",
    }


def execute_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: instantiate 8 engineering brief templates with project-specific values.

    No LLM call. Reads extracted_context.json, derives Jinja2 vars, renders each
    template into ``brief-template-library/<name>.md``, writes
    ``export-manifest-template.json``, advances stage to "qa".
    """
    inp = cast(EngineeringAgentInput, state.inputs)
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
            "system_name": inp.system_name,
            "tech_stack": inp.tech_stack,
            "brief_templates": [f"{name}.md" for name in TEMPLATE_NAMES],
            "spec_artifacts": list(SPEC_ARTIFACTS),
        },
        kind="data",
        stage="execute",
    )

    return state.model_copy(update={"stage": "qa"})
