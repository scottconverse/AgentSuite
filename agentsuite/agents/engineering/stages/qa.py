"""Stage 5 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.prompt_loader import render_prompt
from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC
from agentsuite.agents.engineering.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.qa import QAStageConfig, kernel_qa_stage


def _build_prompt(artifact_bodies: dict[str, str], state: RunState) -> str:
    inp = cast(EngineeringAgentInput, state.inputs)
    return render_prompt(
        "qa_score",
        problem_domain=inp.problem_domain,
        tech_stack=inp.tech_stack,
        has_source_docs=bool(inp.existing_codebase_docs),
        artifacts=artifact_bodies,
    )


_QA_CONFIG = QAStageConfig(
    rubric=ENGINEERING_RUBRIC,
    build_prompt_fn=_build_prompt,
    system_msg="You are scoring 9 engineering-agent artifacts. Return ONLY JSON.",
    spec_artifacts=SPEC_ARTIFACTS,
    write_qa_report=True,
)


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 5 handler: LLM scores engineering artifacts against ENGINEERING_RUBRIC.

    Reads spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through ENGINEERING_RUBRIC.score(), writes qa_report.md and
    qa_scores.json, advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    return kernel_qa_stage(_QA_CONFIG, state, ctx)
