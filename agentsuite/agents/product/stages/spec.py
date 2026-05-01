"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

from typing import Any, cast

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.spec import SpecStageConfig, kernel_spec_stage


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


def _build_artifact_prompt(stem: str, extracted: dict[str, Any], state: RunState) -> str:
    inp = cast(ProductAgentInput, state.inputs)
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
    return render_prompt(_ARTIFACT_TEMPLATE[stem], **template_vars)


def _artifact_system_msg(stem: str) -> str:
    return f"You are writing {stem}.md for a product manager. Return ONLY markdown."


def _build_consistency_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    inp = cast(ProductAgentInput, state.inputs)
    # Original passed list of tuples: [(stem, body[:500]) for stem, body in artifact_bodies.items()]
    # Convert dict back to list of tuples to preserve original template behaviour.
    snippets_as_tuples = list(artifact_snippets.items())
    return render_prompt(
        "spec_consistency_check",
        product_name=inp.product_name,
        artifact_names=SPEC_ARTIFACTS,
        artifact_snippets=snippets_as_tuples,
    )


_SPEC_CONFIG = SpecStageConfig(
    spec_artifacts=SPEC_ARTIFACTS,
    build_artifact_prompt_fn=_build_artifact_prompt,
    artifact_system_msg_fn=_artifact_system_msg,
    build_consistency_prompt_fn=_build_consistency_prompt,
    consistency_system_msg="You are checking 9 product-agent artifacts for consistency. Return ONLY JSON.",
    artifact_snippet_truncate=500,
    snippet_key_fn=lambda s: s,
)


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any check has critical
    severity. Advances to 'execute' on success.
    """
    return kernel_spec_stage(_SPEC_CONFIG, state, ctx)
