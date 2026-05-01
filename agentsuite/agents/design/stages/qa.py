"""Stage 5 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.prompt_loader import render_prompt
from agentsuite.agents.design.rubric import DESIGN_RUBRIC
from agentsuite.agents.design.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.qa import QAStageConfig, kernel_qa_stage


def _build_prompt(artifact_bodies: dict[str, str], state: RunState) -> str:
    inp = cast(DesignAgentInput, state.inputs)
    return render_prompt(
        "qa_score",
        campaign_goal=inp.campaign_goal,
        target_audience=inp.target_audience,
        has_brand_samples=bool(inp.brand_docs),
        artifacts=artifact_bodies,
    )


_QA_CONFIG = QAStageConfig(
    rubric=DESIGN_RUBRIC,
    build_prompt_fn=_build_prompt,
    system_msg="You are scoring 9 design-agent artifacts. Return ONLY JSON.",
    spec_artifacts=SPEC_ARTIFACTS,
    write_qa_report=True,
)


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 5 handler: LLM scores design artifacts against DESIGN_RUBRIC.

    Reads 9 spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through DESIGN_RUBRIC.score(), writes qa_report.md and
    qa_scores.json, advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    return kernel_qa_stage(_QA_CONFIG, state, ctx)
