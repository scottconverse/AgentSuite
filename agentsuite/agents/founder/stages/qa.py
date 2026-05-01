"""Stage 5 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.prompt_loader import render_prompt
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.qa import QAStageConfig, kernel_qa_stage


def _build_prompt(artifact_bodies: dict[str, str], state: RunState) -> str:
    inp = cast(FounderAgentInput, state.inputs)
    return render_prompt(
        "qa_score",
        business_goal=inp.business_goal,
        has_voice_samples=bool(inp.founder_voice_samples),
        artifacts=artifact_bodies,
    )


_QA_CONFIG = QAStageConfig(
    rubric=FOUNDER_RUBRIC,
    build_prompt_fn=_build_prompt,
    system_msg="You are scoring 9 founder-agent artifacts. Return ONLY JSON.",
    spec_artifacts=SPEC_ARTIFACTS,
    write_qa_report=True,
)


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 5 handler: LLM scores artifacts against FOUNDER_RUBRIC.

    Reads the 9 spec artifacts from disk, asks the LLM to score each rubric
    dimension 0-10, runs the scores through FOUNDER_RUBRIC.score() for the
    pass/fail decision, writes ``qa_report.md`` (markdown) and ``qa_scores.json``
    (raw scores), advances stage to "approval".

    Raises ``ValueError`` if the LLM response isn't valid JSON.
    """
    return kernel_qa_stage(_QA_CONFIG, state, ctx)
