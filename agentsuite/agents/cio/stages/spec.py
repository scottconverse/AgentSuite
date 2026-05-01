"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.spec import SpecStageConfig, kernel_spec_stage


SPEC_ARTIFACTS: list[str] = [
    "it-strategy",
    "technology-roadmap",
    "vendor-portfolio",
    "digital-transformation-plan",
    "it-governance-framework",
    "enterprise-architecture",
    "budget-allocation-model",
    "workforce-development-plan",
    "it-risk-appetite-statement",
]


def _build_artifact_prompt(stem: str, extracted: dict[str, Any], state: RunState) -> str:
    inp = cast(CIOAgentInput, state.inputs)
    template_vars: dict[str, object] = {
        "organization_name": inp.organization_name,
        "strategic_priorities": inp.strategic_priorities,
        "it_maturity_level": inp.it_maturity_level,
        "extracted_context": json.dumps(extracted),
        "budget_context": inp.budget_context,
        "digital_initiatives": inp.digital_initiatives,
        "regulatory_environment": inp.regulatory_environment,
    }
    return render_prompt(f"spec_{stem.replace('-', '_')}", **template_vars)


def _artifact_system_msg(stem: str) -> str:
    return f"You are writing {stem}.md for a CIO team. Return ONLY markdown."


def _build_consistency_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    inp = cast(CIOAgentInput, state.inputs)
    return render_prompt(
        "spec_consistency_check",
        organization_name=inp.organization_name,
        strategic_priorities=inp.strategic_priorities,
        artifact_snippets=artifact_snippets,
    )


_SPEC_CONFIG = SpecStageConfig(
    spec_artifacts=SPEC_ARTIFACTS,
    build_artifact_prompt_fn=_build_artifact_prompt,
    artifact_system_msg_fn=_artifact_system_msg,
    build_consistency_prompt_fn=_build_consistency_prompt,
    consistency_system_msg="You are checking 9 CIO artifacts for consistency. Return ONLY JSON.",
    artifact_snippet_truncate=200,  # CIO uses 200-char truncation
    snippet_key_fn=lambda s: s,
)


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any check has critical
    severity. Advances to 'execute' on success.
    """
    return kernel_spec_stage(_SPEC_CONFIG, state, ctx)
