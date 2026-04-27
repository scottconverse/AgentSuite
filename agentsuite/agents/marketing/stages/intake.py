"""Stage 1 — intake: index source materials, no LLM."""
from __future__ import annotations

from pathlib import Path
from typing import cast

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


_DOC_EXTS = {".pdf", ".docx", ".txt", ".md"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _classify_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _DOC_EXTS:
        return "doc"
    if suffix in _IMAGE_EXTS:
        return "image"
    return "other"


def _walk(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.name.startswith("."))


def intake_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 1 handler: walk inputs, classify sources, write inputs_manifest.json.

    No LLM call. Advances state to 'extract'.
    """
    inp = cast(MarketingAgentInput, state.inputs)
    sources: list[dict[str, str]] = []

    if inp.inputs_dir is not None:
        for p in _walk(inp.inputs_dir):
            sources.append({"kind": _classify_path(p), "path": str(p)})

    for p in inp.existing_brand_docs:
        sources.append({"kind": "brand-doc", "path": str(p)})

    for p in inp.competitor_docs:
        sources.append({"kind": "competitor-doc", "path": str(p)})

    manifest = {
        "brand_name": inp.brand_name,
        "campaign_goal": inp.campaign_goal,
        "target_market": inp.target_market,
        "budget_range": inp.budget_range,
        "timeline": inp.timeline,
        "channels": inp.channels,
        "sources": sources,
        "source_count": len(sources),
    }
    ctx.writer.write_json("inputs_manifest.json", manifest, kind="data", stage="intake")

    return state.model_copy(update={"stage": "extract"})
