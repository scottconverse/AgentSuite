"""Stage 4 — execute: instantiate CIO brief-template-library with engagement-specific values."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.agents.cio.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _values_from_input(inp: CIOAgentInput, extracted: dict[str, Any]) -> dict[str, object]:
    vendor_landscape = extracted.get("vendor_landscape", [])
    vendor_name = vendor_landscape[0] if vendor_landscape else "Primary Vendor"
    cio_name = inp.strategic_priorities.split()[0] if inp.strategic_priorities else "CIO"
    return {
        "organization_name": inp.organization_name,
        "strategic_priorities": inp.strategic_priorities,
        "it_maturity_level": inp.it_maturity_level,
        "budget_context": inp.budget_context,
        "digital_initiatives": inp.digital_initiatives,
        "regulatory_environment": inp.regulatory_environment,
        "cio_name": cio_name,
        "briefing_date": "Q2 2026",
        "meeting_date": "Q2 2026",
        "meeting_time": "10:00 AM",
        "meeting_location": "Board Room / Video Conference",
        "committee_chair": cio_name,
        "audience": "Board of Directors",
        "target_audience": "IT Steering Committee",
        "reporting_period": "Q2 2026",
        "review_quarter": "Q2 2026",
        "review_period": "Q2 2026",
        "review_date": "Q2 2026",
        "report_date": "Q2 2026",
        "fiscal_year": "FY2026",
        "fiscal_years": "FY2026–FY2027",
        "total_it_budget": inp.budget_context or "TBD",
        "total_portfolio_budget": inp.budget_context or "TBD",
        "total_active_projects": str(len(extracted.get("technology_pain_points", [])) or 5),
        "initiative_name": inp.digital_initiatives.split("\n")[0] if inp.digital_initiatives else "Digital Transformation Initiative",
        "proposed_by": cio_name,
        "submission_date": "Q2 2026",
        "proposed_start_date": "Q3 2026",
        "estimated_duration": "12 months",
        "estimated_timeline": "12 months",
        "executive_sponsor": cio_name,
        "approving_authority": "CEO and Board",
        "investment_title": inp.digital_initiatives.split("\n")[0] if inp.digital_initiatives else "IT Investment Program",
        "requested_budget": inp.budget_context or "TBD",
        "total_investment": inp.budget_context or "TBD",
        "npv": "TBD",
        "discount_rate": "8",
        "case_date": "Q2 2026",
        "vendor_name": vendor_name,
        "contract_value": "TBD",
        "contract_expiry": "Q4 2026",
        "relationship_owner": cio_name,
        "recommendation": "Continue with performance review",
        "legacy_system_name": extracted.get("technology_pain_points", ["Legacy System"])[0] if extracted.get("technology_pain_points") else "Legacy System",
        "system_age": "7+ years",
        "modernization_approach": "Cloud-native migration",
        "pitch_date": "Q2 2026",
        "priority_1_title": inp.strategic_priorities.split("\n")[0] if inp.strategic_priorities else "Priority 1",
        "priority_2_title": inp.strategic_priorities.split("\n")[1] if len(inp.strategic_priorities.split("\n")) > 1 else "Priority 2",
        "priority_3_title": inp.strategic_priorities.split("\n")[2] if len(inp.strategic_priorities.split("\n")) > 2 else "Priority 3",
        "project_1_name": inp.digital_initiatives.split("\n")[0] if inp.digital_initiatives else "Project Alpha",
        "project_1_phase": "Planning",
        "project_2_name": inp.digital_initiatives.split("\n")[1] if len((inp.digital_initiatives or "").split("\n")) > 1 else "Project Beta",
        "project_2_phase": "Execution",
        "it_headcount": "TBD",
        "agenda_item_4_title": "Digital Initiative Updates",
        "agenda_item_4_duration": "20",
        "agenda_item_5_title": "Open Discussion",
        "agenda_item_5_duration": "10",
    }


def execute_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: instantiate 8 CIO brief templates with engagement-specific values.

    No LLM call. Reads extracted_context.json, derives Jinja2 vars, renders each
    template into ``brief-template-library/<name>.md``, writes
    ``export-manifest-template.json``, advances stage to "qa".
    """
    inp = cast(CIOAgentInput, state.inputs)
    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )
    values = _values_from_input(inp, extracted)

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
            "organization_name": inp.organization_name,
            "it_maturity_level": inp.it_maturity_level,
            "brief_templates": [f"{name}.md" for name in TEMPLATE_NAMES],
            "spec_artifacts": list(SPEC_ARTIFACTS),
        },
        kind="data",
        stage="execute",
    )

    return state.model_copy(update={"stage": "qa"})
