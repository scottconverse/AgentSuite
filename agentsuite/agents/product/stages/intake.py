"""Stage 1 — intake: index source materials, no LLM."""
from __future__ import annotations

from pathlib import Path
from typing import cast

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


_PDF_EXTS = {".pdf"}
_DOC_EXTS = {".md", ".txt"}
_DATA_EXTS = {".csv", ".json"}


def _classify_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _PDF_EXTS:
        return "pdf"
    if suffix in _DOC_EXTS:
        return "doc"
    if suffix in _DATA_EXTS:
        return "data"
    return "other"


def _walk(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.name.startswith("."))


def intake_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 1 handler: walk inputs, classify sources, write inputs_manifest.json.

    No LLM call. Advances state to 'extract'.
    """
    inp = cast(ProductAgentInput, state.inputs)
    sources: list[dict[str, str]] = []

    if inp.inputs_dir is not None:
        for p in _walk(inp.inputs_dir):
            sources.append({"kind": _classify_path(p), "path": str(p)})

    for p in inp.research_docs:
        sources.append({"kind": "research-doc", "path": str(p)})

    for p in inp.competitor_docs:
        sources.append({"kind": "competitor-doc", "path": str(p)})

    manifest = {
        "product_name": inp.product_name,
        "target_users": inp.target_users,
        "core_problem": inp.core_problem,
        "technical_constraints": inp.technical_constraints,
        "timeline_constraint": inp.timeline_constraint,
        "success_metric_goals": inp.success_metric_goals,
        "sources": sources,
        "source_count": len(sources),
    }
    ctx.writer.write_json("inputs_manifest.json", manifest, kind="data", stage="intake")

    return state.model_copy(update={"stage": "extract"})
