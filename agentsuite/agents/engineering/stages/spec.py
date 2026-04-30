"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import cast

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest
from agentsuite.llm.json_extract import extract_json


SPEC_ARTIFACTS: list[str] = [
    "architecture-decision-record",
    "system-design",
    "api-spec",
    "data-model",
    "security-review",
    "deployment-plan",
    "runbook",
    "tech-debt-register",
    "performance-requirements",
]


_ARTIFACT_TEMPLATE: dict[str, str] = {
    "architecture-decision-record": "spec_architecture_decision_record",
    "system-design": "spec_system_design",
    "api-spec": "spec_api_spec",
    "data-model": "spec_data_model",
    "security-review": "spec_security_review",
    "deployment-plan": "spec_deployment_plan",
    "runbook": "spec_runbook",
    "tech-debt-register": "spec_tech_debt_register",
    "performance-requirements": "spec_performance_requirements",
}


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any check has critical
    severity. Advances to 'execute' on success.
    """
    inp = cast(EngineeringAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )

    template_vars: dict[str, object] = {
        "system_name": inp.system_name,
        "problem_domain": inp.problem_domain,
        "tech_stack": inp.tech_stack,
        "scale_requirements": inp.scale_requirements,
        "security_requirements": inp.security_requirements,
        "team_size": inp.team_size,
        "existing_patterns": extracted.get("existing_patterns", []),
        "known_bottlenecks": extracted.get("known_bottlenecks", []),
        "security_risks": extracted.get("security_risks", []),
        "tech_debt_items": extracted.get("tech_debt_items", []),
        "integration_points": extracted.get("integration_points", []),
        "open_questions": extracted.get("open_questions", []),
    }

    artifact_bodies: dict[str, str] = {}

    for stem in SPEC_ARTIFACTS:
        prompt_name = _ARTIFACT_TEMPLATE[stem]
        prompt = render_prompt(prompt_name, **template_vars)
        response = llm.complete(LLMRequest(
            prompt=prompt,
            system=f"You are writing {stem}.md for an engineering team. Return ONLY markdown.",
            temperature=0.2,
        ))
        ctx.cost_tracker.add(Cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usd=response.usd,
            model=response.model,
        ))
        ctx.writer.write(f"{stem}.md", response.text, kind="spec", stage="spec")
        artifact_bodies[stem] = response.text

    artifact_snippets = {stem: body[:500] for stem, body in artifact_bodies.items()}
    consistency_prompt = render_prompt(
        "spec_consistency_check",
        system_name=inp.system_name,
        artifact_names=SPEC_ARTIFACTS,
        artifact_snippets=artifact_snippets,
    )
    consistency_response = llm.complete(LLMRequest(
        prompt=consistency_prompt,
        system="You are checking 9 engineering-agent artifacts for consistency. Return ONLY JSON.",
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=consistency_response.input_tokens,
        output_tokens=consistency_response.output_tokens,
        usd=consistency_response.usd,
        model=consistency_response.model,
    ))

    try:
        report = extract_json(consistency_response.text)
    except ValueError as exc:
        raise ValueError(f"consistency check produced invalid JSON: {exc}") from exc

    ctx.writer.write_json("consistency_report.json", report, kind="data", stage="spec")

    mismatches_raw = report.get("mismatches") if isinstance(report, dict) else None
    mismatches = mismatches_raw if isinstance(mismatches_raw, list) else []
    critical = [c for c in mismatches if isinstance(c, dict) and c.get("severity") == "critical"]
    return state.model_copy(update={
        "stage": "execute",
        "requires_revision": bool(critical),
    })
