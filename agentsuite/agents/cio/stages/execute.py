"""Stage 4 — execute: instantiate CIO brief-template-library with engagement-specific values."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any, cast

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.stages.spec import SPEC_ARTIFACTS
from agentsuite.agents.cio.template_loader import TEMPLATE_NAMES, render_template
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _resolve_as_of(inp: CIOAgentInput) -> date:
    """Return ``inp.as_of_date`` if set, else today's UTC date.

    Centralizing here keeps the date source explicit and testable: callers
    can pass an ``as_of_date`` for reproducibility (golden-tests, backdated
    reports) and production runs continue to default to "now".
    """
    if inp.as_of_date is not None:
        return inp.as_of_date
    return datetime.now(tz=timezone.utc).date()


def _current_quarter(as_of: date) -> str:
    q = (as_of.month - 1) // 3 + 1
    return f"Q{q} {as_of.year}"


def _next_quarter(as_of: date) -> str:
    q = (as_of.month - 1) // 3 + 1
    year = as_of.year
    if q == 4:
        q, year = 1, year + 1
    else:
        q += 1
    return f"Q{q} {year}"


def _current_fiscal_year(as_of: date) -> str:
    return f"FY{as_of.year}"


def _fiscal_year_range(as_of: date) -> str:
    return f"FY{as_of.year}–FY{as_of.year + 2}"


def _values_from_input(inp: CIOAgentInput, extracted: dict[str, Any]) -> dict[str, object]:
    vendor_landscape = extracted.get("vendor_landscape", [])
    vendor_name = vendor_landscape[0] if vendor_landscape else "Primary Vendor"
    cio_name = inp.cio_name
    as_of = _resolve_as_of(inp)
    current_q = _current_quarter(as_of)
    next_q = _next_quarter(as_of)
    fy = _current_fiscal_year(as_of)
    fy_range = _fiscal_year_range(as_of)
    return {
        "organization_name": inp.organization_name,
        "strategic_priorities": inp.strategic_priorities,
        "it_maturity_level": inp.it_maturity_level,
        "budget_context": inp.budget_context,
        "digital_initiatives": inp.digital_initiatives,
        "regulatory_environment": inp.regulatory_environment,
        "cio_name": cio_name,
        "briefing_date": current_q,
        "meeting_date": current_q,
        "meeting_time": "10:00 AM",
        "meeting_location": "Board Room / Video Conference",
        "committee_chair": cio_name,
        "audience": "Board of Directors",
        "target_audience": "IT Steering Committee",
        "reporting_period": current_q,
        "review_quarter": current_q,
        "review_period": current_q,
        "review_date": current_q,
        "report_date": current_q,
        "fiscal_year": fy,
        "fiscal_years": fy_range,
        "total_it_budget": inp.budget_context or "TBD",
        "total_portfolio_budget": inp.budget_context or "TBD",
        "total_active_projects": str(len(extracted.get("technology_pain_points", [])) or 5),
        "initiative_name": inp.digital_initiatives.split("\n")[0] if inp.digital_initiatives else "Digital Transformation Initiative",
        "proposed_by": cio_name,
        "submission_date": current_q,
        "proposed_start_date": next_q,
        "estimated_duration": "12 months",
        "estimated_timeline": "12 months",
        "executive_sponsor": cio_name,
        "approving_authority": "CEO and Board",
        "investment_title": inp.digital_initiatives.split("\n")[0] if inp.digital_initiatives else "IT Investment Program",
        "requested_budget": inp.budget_context or "TBD",
        "total_investment": inp.budget_context or "TBD",
        "npv": "TBD",
        "discount_rate": "8",
        "case_date": current_q,
        "vendor_name": vendor_name,
        "contract_value": "TBD",
        "contract_expiry": next_q,
        "relationship_owner": cio_name,
        "recommendation": "Continue with performance review",
        "legacy_system_name": extracted.get("technology_pain_points", ["Legacy System"])[0] if extracted.get("technology_pain_points") else "Legacy System",
        "system_age": "7+ years",
        "modernization_approach": "Cloud-native migration",
        "pitch_date": current_q,
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
