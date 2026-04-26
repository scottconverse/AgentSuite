"""Stage 1 — intake: index source materials, no LLM."""
from __future__ import annotations

from pathlib import Path
from typing import cast

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


_VOICE_EXTS = {".txt", ".md"}
_SCREENSHOT_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _classify_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _SCREENSHOT_EXTS:
        return "screenshot"
    if path.name.lower() in {"readme.md", "readme.rst", "readme.txt"}:
        return "product-doc"
    if suffix in _VOICE_EXTS:
        return "product-doc"
    return "other"


def _walk(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.name.startswith("."))


def intake_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 1 handler: walks input dir, classifies sources, writes inputs_manifest.json.

    Returns a new RunState advanced to the ``extract`` stage. No LLM call.
    """
    inp = cast(FounderAgentInput, state.inputs)
    sources: list[dict[str, str]] = []

    if inp.inputs_dir is not None:
        for p in _walk(inp.inputs_dir):
            sources.append({"kind": _classify_path(p), "path": str(p)})

    for doc in inp.explicit_brand_docs:
        sources.append({"kind": "brand-doc", "path": str(doc)})

    for sample in inp.founder_voice_samples:
        sources.append({"kind": "voice-sample", "path": str(sample)})

    for shot in inp.screenshots:
        sources.append({"kind": "screenshot", "path": str(shot)})

    for url in inp.repo_urls:
        sources.append({"kind": "repo", "path": url})

    for url in inp.web_urls:
        sources.append({"kind": "other", "path": url})

    manifest = {
        "business_goal": inp.business_goal,
        "current_state": inp.current_state,
        "sources": sources,
        "source_count": len(sources),
    }
    ctx.writer.write_json("inputs_manifest.json", manifest, kind="data", stage="intake")

    return state.model_copy(update={"stage": "extract"})
