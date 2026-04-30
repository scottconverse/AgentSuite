"""Stage 4 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.prompt_loader import render_prompt
from agentsuite.agents.cio.rubric import CIO_RUBRIC
from agentsuite.agents.cio.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest
from agentsuite.llm.json_extract import extract_json


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 4 handler: LLM scores CIO artifacts against CIO_RUBRIC.

    Reads spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through CIO_RUBRIC.score(), writes qa_scores.json,
    advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    inp = cast(CIOAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    artifact_snippets: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        path = ctx.writer.run_dir / f"{stem}.md"
        if path.exists():
            artifact_snippets[stem] = path.read_text(encoding="utf-8")[:500]

    prompt = render_prompt(
        "qa_score",
        organization_name=inp.organization_name,
        strategic_priorities=inp.strategic_priorities,
        artifact_snippets=artifact_snippets,
    )
    response = llm.complete(LLMRequest(
        prompt=prompt,
        system="You are scoring 9 CIO artifacts. Return ONLY JSON.",
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        usd=response.usd,
        model=response.model,
    ))

    try:
        parsed = extract_json(response.text)
    except ValueError as exc:
        raise ValueError(f"qa stage produced invalid JSON: {exc}") from exc

    report = CIO_RUBRIC.score(
        scores=parsed["scores"],
        revision_instructions=list(parsed.get("revision_instructions", [])),
    )
    ctx.writer.write_json("qa_scores.json", report.model_dump(), kind="data", stage="qa")

    return state.model_copy(update={
        "stage": "approval",
        "requires_revision": report.requires_revision,
    })
