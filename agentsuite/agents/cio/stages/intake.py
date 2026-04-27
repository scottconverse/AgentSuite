"""Stage 1 — intake: index IT source materials, render intake prompt."""
from __future__ import annotations

from typing import cast

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest


def intake_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 1 handler: index IT docs, render intake prompt, write inputs_manifest.json.

    Advances state to 'extract'.
    """
    inp = cast(CIOAgentInput, state.inputs)
    sources: list[dict[str, str]] = []

    for p in inp.existing_it_docs:
        sources.append({"kind": "it-doc", "path": str(p)})

    source_count = len(sources)

    prompt = render_prompt(
        "intake",
        organization_name=inp.organization_name,
        strategic_priorities=inp.strategic_priorities,
        it_maturity_level=inp.it_maturity_level,
        source_count=source_count,
    )

    llm: LLMProvider | None = ctx.edits.get("llm")
    if llm is not None:
        response = llm.complete(LLMRequest(
            prompt=prompt,
            system="You are indexing IT source materials for a CIO strategy assessment. Be concise.",
            temperature=0.0,
        ))
        ctx.cost_tracker.add(Cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usd=response.usd,
        ))

    manifest = {
        "organization_name": inp.organization_name,
        "strategic_priorities": inp.strategic_priorities,
        "it_maturity_level": inp.it_maturity_level,
        "sources": sources,
        "source_count": source_count,
        "intake_prompt": prompt,
    }
    ctx.writer.write_json("inputs_manifest.json", manifest, kind="data", stage="intake")

    return state.model_copy(update={"stage": "extract"})
