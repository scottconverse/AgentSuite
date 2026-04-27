"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import cast

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest


SPEC_ARTIFACTS: list[str] = [
    "product-requirements-doc",
    "user-story-map",
    "feature-prioritization",
    "success-metrics",
    "competitive-analysis",
    "user-persona-map",
    "acceptance-criteria",
    "product-roadmap",
    "risk-register",
]


_ARTIFACT_TEMPLATE: dict[str, str] = {
    "product-requirements-doc": "spec_prd",
    "user-story-map": "spec_user_story_map",
    "feature-prioritization": "spec_feature_prioritization",
    "success-metrics": "spec_success_metrics",
    "competitive-analysis": "spec_competitive_analysis",
    "user-persona-map": "spec_user_persona_map",
    "acceptance-criteria": "spec_acceptance_criteria",
    "product-roadmap": "spec_product_roadmap",
    "risk-register": "spec_risk_register",
}


class ConsistencyCheckFailed(RuntimeError):
    """Raised when the cross-artifact consistency check finds critical mismatches."""


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any check has critical
    severity. Advances to 'execute' on success.
    """
    inp = cast(ProductAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )

    template_vars: dict[str, object] = {
        "product_name": inp.product_name,
        "target_users": inp.target_users,
        "core_problem": inp.core_problem,
        "technical_constraints": inp.technical_constraints or extracted.get("technical_constraints", []),
        "timeline_constraint": inp.timeline_constraint,
        "success_metric_goals": inp.success_metric_goals,
        "user_pain_points": extracted.get("user_pain_points", []),
        "competitor_gaps": extracted.get("competitor_gaps", []),
        "market_signals": extracted.get("market_signals", []),
        "assumed_non_goals": extracted.get("assumed_non_goals", []),
        "open_questions": extracted.get("open_questions", []),
    }

    artifact_bodies: dict[str, str] = {}

    for stem in SPEC_ARTIFACTS:
        prompt_name = _ARTIFACT_TEMPLATE[stem]
        prompt = render_prompt(prompt_name, **template_vars)
        response = llm.complete(LLMRequest(
            prompt=prompt,
            system=f"You are writing {stem}.md for a product manager. Return ONLY markdown.",
            temperature=0.2,
        ))
        ctx.cost_tracker.add(Cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usd=response.usd,
        ))
        ctx.writer.write(f"{stem}.md", response.text, kind="spec", stage="spec")
        artifact_bodies[stem] = response.text

    artifact_snippets = [(stem, body[:500]) for stem, body in artifact_bodies.items()]
    consistency_prompt = render_prompt(
        "spec_consistency_check",
        product_name=inp.product_name,
        artifact_names=SPEC_ARTIFACTS,
        artifact_snippets=artifact_snippets,
    )
    consistency_response = llm.complete(LLMRequest(
        prompt=consistency_prompt,
        system="You are checking 9 product-agent artifacts for consistency. Return ONLY JSON.",
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=consistency_response.input_tokens,
        output_tokens=consistency_response.output_tokens,
        usd=consistency_response.usd,
    ))

    try:
        report = json.loads(consistency_response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"consistency check produced invalid JSON: {exc}") from exc

    ctx.writer.write_json("consistency_report.json", report, kind="data", stage="spec")

    critical = [c for c in report.get("checks", []) if c.get("severity") == "critical"]
    if critical:
        raise ConsistencyCheckFailed(
            f"{len(critical)} critical consistency failure(s): "
            + "; ".join(c.get("detail", "") for c in critical)
        )

    return state.model_copy(update={"stage": "execute"})
