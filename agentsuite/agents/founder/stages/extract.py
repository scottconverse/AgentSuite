"""Stage 2 — extract: LLM pass over indexed sources."""
from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest


def _summarize_sources(manifest_path: Path) -> str:
    """Build a flat text summary of the inputs_manifest.json sources for the LLM prompt."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("sources"):
        return "(no sources supplied)"
    lines = []
    for s in manifest["sources"]:
        path = Path(s["path"])
        kind = s["kind"]
        try:
            if path.exists() and path.is_file():
                snippet = path.read_text(encoding="utf-8", errors="replace")[:1500]
                lines.append(f"[{kind}] {path}\n{snippet}\n")
            else:
                lines.append(f"[{kind}] {s['path']} (URL or unreachable)")
        except Exception:
            lines.append(f"[{kind}] {s['path']} (unreadable)")
    return "\n---\n".join(lines)


def extract_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 2 handler: LLM extracts structured brand context, writes extracted_context.json.

    Reads inputs_manifest.json from intake stage, summarizes sources, calls LLM,
    parses JSON response, surfaces ``gaps`` array as open_questions on the state.
    Raises ``ValueError`` if the LLM response is not valid JSON.
    """
    inp = cast(FounderAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    manifest_path = ctx.writer.run_dir / "inputs_manifest.json"
    sources_summary = _summarize_sources(manifest_path)

    prompt = render_prompt(
        "extract",
        sources_summary=sources_summary,
        business_goal=inp.business_goal,
        current_state=inp.current_state,
    )
    response = llm.complete(LLMRequest(
        prompt=prompt,
        system="You are extracting structured brand context. Return ONLY valid JSON.",
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
        raise ValueError(f"extract stage produced invalid JSON: {exc}") from exc

    ctx.writer.write_json("extracted_context.json", parsed, kind="data", stage="extract")

    open_questions = list(parsed.get("gaps", []))
    return state.model_copy(update={
        "stage": "spec",
        "open_questions": state.open_questions + open_questions,
    })
