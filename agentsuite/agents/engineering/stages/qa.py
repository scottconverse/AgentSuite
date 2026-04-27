"""Stage 5 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

import json
from typing import cast

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.prompt_loader import render_prompt
from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC
from agentsuite.agents.engineering.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 5 handler: LLM scores engineering artifacts against ENGINEERING_RUBRIC.

    Reads spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through ENGINEERING_RUBRIC.score(), writes qa_report.md and
    qa_scores.json, advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    inp = cast(EngineeringAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    artifact_bodies: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        path = ctx.writer.run_dir / f"{stem}.md"
        if path.exists():
            artifact_bodies[f"{stem}.md"] = path.read_text(encoding="utf-8")

    prompt = render_prompt(
        "qa_score",
        problem_domain=inp.problem_domain,
        tech_stack=inp.tech_stack,
        has_source_docs=bool(inp.existing_codebase_docs),
        artifacts=artifact_bodies,
    )
    response = llm.complete(LLMRequest(
        prompt=prompt,
        system="You are scoring 9 engineering-agent artifacts. Return ONLY JSON.",
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        usd=response.usd,
    ))

    try:
        parsed = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"qa stage produced invalid JSON: {exc}") from exc

    report = ENGINEERING_RUBRIC.score(
        scores=parsed["scores"],
        revision_instructions=list(parsed.get("revision_instructions", [])),
    )
    ctx.writer.write("qa_report.md", report.to_markdown(), kind="qa_report", stage="qa")
    ctx.writer.write_json("qa_scores.json", report.model_dump(), kind="data", stage="qa")

    return state.model_copy(update={
        "stage": "approval",
        "requires_revision": report.requires_revision,
    })
