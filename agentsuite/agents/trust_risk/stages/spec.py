"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.spec import SpecStageConfig, kernel_spec_stage


SPEC_ARTIFACTS: list[str] = [
    "threat-model",
    "risk-register",
    "control-framework",
    "incident-response-plan",
    "compliance-matrix",
    "vendor-risk-assessment",
    "security-policy",
    "audit-readiness-report",
    "residual-risk-acceptance",
]


def _build_artifact_prompt(stem: str, extracted: dict[str, Any], state: RunState) -> str:
    inp = cast(TrustRiskAgentInput, state.inputs)
    template_vars: dict[str, object] = {
        "product_name": inp.product_name,
        "risk_domain": inp.risk_domain,
        "stakeholder_context": inp.stakeholder_context,
        "regulatory_context": inp.regulatory_context,
        "threat_model_scope": inp.threat_model_scope,
        "compliance_frameworks": inp.compliance_frameworks,
        "extracted_context": json.dumps(extracted),
    }
    return render_prompt(f"spec_{stem.replace('-', '_')}", **template_vars)


def _artifact_system_msg(stem: str) -> str:
    return f"You are writing {stem}.md for a trust and risk team. Return ONLY markdown."


def _build_consistency_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    inp = cast(TrustRiskAgentInput, state.inputs)
    return render_prompt(
        "spec_consistency_check",
        product_name=inp.product_name,
        risk_domain=inp.risk_domain,
        artifact_snippets=artifact_snippets,
    )


_SPEC_CONFIG = SpecStageConfig(
    spec_artifacts=SPEC_ARTIFACTS,
    build_artifact_prompt_fn=_build_artifact_prompt,
    artifact_system_msg_fn=_artifact_system_msg,
    build_consistency_prompt_fn=_build_consistency_prompt,
    consistency_system_msg="You are checking 9 trust-risk-agent artifacts for consistency. Return ONLY JSON.",
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
