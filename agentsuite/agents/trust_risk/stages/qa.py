"""Stage 4 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.prompt_loader import render_prompt
from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC
from agentsuite.agents.trust_risk.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.qa import QAStageConfig, kernel_qa_stage


def _build_prompt(artifact_bodies: dict[str, str], state: RunState) -> str:
    inp = cast(TrustRiskAgentInput, state.inputs)
    return render_prompt(
        "qa_score",
        product_name=inp.product_name,
        risk_domain=inp.risk_domain,
        has_source_docs=bool(inp.existing_policies or inp.incident_reports),
        artifacts=artifact_bodies,
    )


_QA_CONFIG = QAStageConfig(
    rubric=TRUST_RISK_RUBRIC,
    build_prompt_fn=_build_prompt,
    system_msg="You are scoring 9 trust-risk-agent artifacts. Return ONLY JSON.",
    spec_artifacts=SPEC_ARTIFACTS,
    write_qa_report=True,
)


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: LLM scores trust-risk artifacts against TRUST_RISK_RUBRIC.

    Reads spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through TRUST_RISK_RUBRIC.score(), writes qa_report.md and
    qa_scores.json, advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    return kernel_qa_stage(_QA_CONFIG, state, ctx)
