"""Stage 2 — extract: LLM pass over indexed source materials."""
from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest


def _read_sources_by_kind(manifest_path: Path) -> dict[str, list[str]]:
    """Read manifest and bucket sources by kind into text summaries."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    buckets: dict[str, list[str]] = {
        "brand-doc": [],
        "reference-asset": [],
        "anti-example": [],
        "other": [],
    }
    for s in manifest.get("sources", []):
        kind = s.get("kind", "other")
        path = Path(s["path"])
        try:
            if path.exists() and path.is_file() and path.suffix.lower() in {".txt", ".md"}:
                snippet = path.read_text(encoding="utf-8", errors="replace")[:1500]
                entry = f"[{path.name}]\n{snippet}"
            else:
                entry = f"[{s['path']}] (binary or unreachable)"
        except Exception:
            entry = f"[{s['path']}] (unreadable)"
        bucket_key = kind if kind in buckets else "other"
        buckets[bucket_key].append(entry)
    return buckets


def _join(entries: list[str]) -> str:
    return "\n---\n".join(entries) if entries else "(none supplied)"


def extract_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 2 handler: LLM extracts structured design context, writes extracted_context.json.

    Reads inputs_manifest.json from intake stage, calls LLM with design extract prompt,
    parses JSON response, surfaces ``gaps`` as open_questions. Advances to 'spec'.
    Raises ``ValueError`` if the LLM response is not valid JSON.
    """
    inp = cast(DesignAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    manifest_path = ctx.writer.run_dir / "inputs_manifest.json"
    buckets = _read_sources_by_kind(manifest_path)

    prompt = render_prompt(
        "extract",
        campaign_goal=inp.campaign_goal,
        target_audience=inp.target_audience,
        brand_docs=_join(buckets["brand-doc"]),
        references=_join(buckets["reference-asset"]),
        anti_examples=_join(buckets["anti-example"]),
    )
    response = llm.complete(LLMRequest(
        prompt=prompt,
        system="You are extracting structured visual-design context. Return ONLY valid JSON.",
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
