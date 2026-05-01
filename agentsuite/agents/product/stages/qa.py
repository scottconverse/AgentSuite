"""Stage 5 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.prompt_loader import render_prompt
from agentsuite.agents.product.rubric import PRODUCT_RUBRIC
from agentsuite.agents.product.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.qa import QAStageConfig, kernel_qa_stage


def _build_prompt(artifact_bodies: dict[str, str], state: RunState) -> str:
    inp = cast(ProductAgentInput, state.inputs)
    return render_prompt(
        "qa_score",
        core_problem=inp.core_problem,
        target_users=inp.target_users,
        has_research_docs=bool(inp.research_docs),
        artifacts=artifact_bodies,
    )


_QA_CONFIG = QAStageConfig(
    rubric=PRODUCT_RUBRIC,
    build_prompt_fn=_build_prompt,
    system_msg="You are scoring 9 product-agent artifacts. Return ONLY JSON.",
    spec_artifacts=SPEC_ARTIFACTS,
    write_qa_report=True,
)


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 5 handler: LLM scores product artifacts against PRODUCT_RUBRIC.

    Reads 9 spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through PRODUCT_RUBRIC.score(), writes qa_report.md and
    qa_scores.json, advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    return kernel_qa_stage(_QA_CONFIG, state, ctx)
