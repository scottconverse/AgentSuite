"""Stage 5 — qa: rubric scoring + revision-instruction capture."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.prompt_loader import render_prompt
from agentsuite.agents.marketing.rubric import MARKETING_RUBRIC
from agentsuite.agents.marketing.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest
from agentsuite.llm.json_extract import extract_json


def qa_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 5 handler: LLM scores marketing artifacts against MARKETING_RUBRIC.

    Reads spec artifacts from disk, calls LLM to score each rubric dimension,
    runs scores through MARKETING_RUBRIC.score(), writes qa_report.md and
    qa_scores.json, advances stage to "approval".

    Raises ValueError if the LLM response isn't valid JSON.
    """
    inp = cast(MarketingAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    artifact_bodies: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        path = ctx.writer.run_dir / f"{stem}.md"
        if path.exists():
            artifact_bodies[f"{stem}.md"] = path.read_text(encoding="utf-8")

    prompt = render_prompt(
        "qa_score",
        brand_name=inp.brand_name,
        campaign_goal=inp.campaign_goal,
        has_source_docs=bool(inp.existing_brand_docs),
        artifacts=artifact_bodies,
    )
    response = llm.complete(LLMRequest(
        prompt=prompt,
        system="You are scoring 9 marketing-agent artifacts. Return ONLY JSON.",
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

    if not isinstance(parsed, dict):
        parsed = {}
    raw_scores = parsed.get("scores")
    if not isinstance(raw_scores, dict):
        raw_scores = {}
    raw_revisions = parsed.get("revision_instructions")
    if not isinstance(raw_revisions, list):
        raw_revisions = []
    report = MARKETING_RUBRIC.score(scores=raw_scores, revision_instructions=raw_revisions)
    ctx.writer.write("qa_report.md", report.to_markdown(), kind="qa_report", stage="qa")
    ctx.writer.write_json("qa_scores.json", report.model_dump(), kind="data", stage="qa")

    return state.model_copy(update={
        "stage": "approval",
        "requires_revision": report.requires_revision,
    })
