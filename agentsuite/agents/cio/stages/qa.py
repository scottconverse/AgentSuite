"""Stage 4 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.prompt_loader import render_prompt
from agentsuite.agents.cio.rubric import CIO_RUBRIC
from agentsuite.agents.cio.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.qa import QAStageConfig, kernel_qa_stage


def _build_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    inp = cast(CIOAgentInput, state.inputs)
    return render_prompt(
        "qa_score",
        organization_name=inp.organization_name,
        strategic_priorities=inp.strategic_priorities,
        artifact_snippets=artifact_snippets,
    )


_QA_CONFIG = QAStageConfig(
    rubric=CIO_RUBRIC,
    build_prompt_fn=_build_prompt,
    system_msg="You are scoring 9 CIO artifacts. Return ONLY JSON.",
    spec_artifacts=SPEC_ARTIFACTS,
    write_qa_report=False,   # CIO writes only qa_scores.json, not qa_report.md
    artifact_key_fn=lambda s: s,  # CIO keys snippets by bare stem (no .md extension)
    artifact_truncate=500,   # CIO reads truncated content
)


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: LLM scores CIO artifacts against CIO_RUBRIC.

    Reads spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through CIO_RUBRIC.score(), writes qa_scores.json,
    advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    return kernel_qa_stage(_QA_CONFIG, state, ctx)
