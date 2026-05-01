"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.spec import SpecStageConfig, kernel_spec_stage


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


def _build_artifact_prompt(stem: str, extracted: dict[str, Any], state: RunState) -> str:
    inp = cast(EngineeringAgentInput, state.inputs)
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
    return render_prompt(_ARTIFACT_TEMPLATE[stem], **template_vars)


def _artifact_system_msg(stem: str) -> str:
    return f"You are writing {stem}.md for an engineering team. Return ONLY markdown."


def _build_consistency_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    inp = cast(EngineeringAgentInput, state.inputs)
    return render_prompt(
        "spec_consistency_check",
        system_name=inp.system_name,
        artifact_names=SPEC_ARTIFACTS,
        artifact_snippets=artifact_snippets,
    )


_SPEC_CONFIG = SpecStageConfig(
    spec_artifacts=SPEC_ARTIFACTS,
    build_artifact_prompt_fn=_build_artifact_prompt,
    artifact_system_msg_fn=_artifact_system_msg,
    build_consistency_prompt_fn=_build_consistency_prompt,
    consistency_system_msg="You are checking 9 engineering-agent artifacts for consistency. Return ONLY JSON.",
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
