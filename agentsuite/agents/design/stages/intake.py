"""Stage 1 — intake: index source materials, no LLM."""
from __future__ import annotations

from pathlib import Path
from typing import cast

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}
_PDF_EXTS = {".pdf"}
_DOC_EXTS = {".md", ".txt"}


def _classify_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _IMAGE_EXTS:
        return "image"
    if suffix in _PDF_EXTS:
        return "pdf"
    if suffix in _DOC_EXTS:
        return "doc"
    return "other"


def _walk(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.name.startswith("."))


def intake_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 1 handler: walk inputs, classify sources, write inputs_manifest.json.

    No LLM call. Advances state to 'extract'.
    """
    inp = cast(DesignAgentInput, state.inputs)
    sources: list[dict[str, str]] = []

    if inp.inputs_dir is not None:
        for p in _walk(inp.inputs_dir):
            sources.append({"kind": _classify_path(p), "path": str(p)})

    for p in inp.brand_docs:
        sources.append({"kind": "brand-doc", "path": str(p)})

    for p in inp.reference_assets:
        sources.append({"kind": "reference-asset", "path": str(p)})

    for p in inp.anti_examples:
        sources.append({"kind": "anti-example", "path": str(p)})

    manifest = {
        "target_audience": inp.target_audience,
        "campaign_goal": inp.campaign_goal,
        "channel": inp.channel,
        "accessibility_requirements": inp.accessibility_requirements,
        "sources": sources,
        "source_count": len(sources),
    }
    ctx.writer.write_json("inputs_manifest.json", manifest, kind="data", stage="intake")

    return state.model_copy(update={"stage": "extract"})
