"""Stage 4 — execute: instantiate trust/risk brief-template-library with assessment-specific values."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.agents.trust_risk.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _values_from_extracted(inp: TrustRiskAgentInput, extracted: dict[str, Any]) -> dict[str, object]:
    return {
        "product_name": inp.product_name,
        "risk_domain": inp.risk_domain,
        "stakeholder_context": inp.stakeholder_context,
        "regulatory_context": inp.regulatory_context,
        "compliance_frameworks": inp.compliance_frameworks,
        "threat_category": extracted.get("known_threats", [""])[0] if extracted.get("known_threats") else "",
        "control_name": extracted.get("existing_controls", [""])[0] if extracted.get("existing_controls") else "",
        "incident_title": extracted.get("incident_patterns", [""])[0] if extracted.get("incident_patterns") else "",
        "severity": "High",
        "vendor_name": extracted.get("vendor_risks", [""])[0] if extracted.get("vendor_risks") else "",
        "quarter": "Q2 2026",
        "team_lead": inp.stakeholder_context.split()[0] if inp.stakeholder_context else "Security Team",
    }


def execute_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: instantiate 8 trust/risk brief templates with assessment-specific values.

    No LLM call. Reads extracted_context.json, derives Jinja2 vars, renders each
    template into ``brief-template-library/<name>.md``, writes
    ``export-manifest-template.json``, advances stage to "qa".
    """
    inp = cast(TrustRiskAgentInput, state.inputs)
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
            "product_name": inp.product_name,
            "risk_domain": inp.risk_domain,
            "brief_templates": [f"{name}.md" for name in TEMPLATE_NAMES],
            "spec_artifacts": list(SPEC_ARTIFACTS),
        },
        kind="data",
        stage="execute",
    )

    return state.model_copy(update={"stage": "qa"})
