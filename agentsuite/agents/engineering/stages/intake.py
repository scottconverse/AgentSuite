"""Stage 1 — intake: index source materials, no LLM."""
from __future__ import annotations

from pathlib import Path
from typing import cast

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


_PDF_EXTS = {".pdf"}
_DOC_EXTS = {".md", ".txt"}
_CODE_EXTS = {".py", ".ts", ".go", ".rs", ".java", ".sql"}
_CONFIG_EXTS = {".yaml", ".yml", ".json", ".toml"}


def _classify_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _PDF_EXTS:
        return "pdf"
    if suffix in _DOC_EXTS:
        return "doc"
    if suffix in _CODE_EXTS:
        return "code"
    if suffix in _CONFIG_EXTS:
        return "config"
    return "other"


def _walk(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.name.startswith("."))


def intake_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 1 handler: walk inputs, classify sources, write inputs_manifest.json.

    No LLM call. Advances state to 'extract'.
    """
    inp = cast(EngineeringAgentInput, state.inputs)
    sources: list[dict[str, str]] = []

    if inp.inputs_dir is not None:
        for p in _walk(inp.inputs_dir):
            sources.append({"kind": _classify_path(p), "path": str(p)})

    for p in inp.existing_codebase_docs:
        sources.append({"kind": "codebase-doc", "path": str(p)})

    for p in inp.adr_history:
        sources.append({"kind": "adr", "path": str(p)})

    for p in inp.incident_history:
        sources.append({"kind": "incident-report", "path": str(p)})

    manifest = {
        "system_name": inp.system_name,
        "problem_domain": inp.problem_domain,
        "tech_stack": inp.tech_stack,
        "scale_requirements": inp.scale_requirements,
        "security_requirements": inp.security_requirements,
        "team_size": inp.team_size,
        "sources": sources,
        "source_count": len(sources),
    }
    ctx.writer.write_json("inputs_manifest.json", manifest, kind="data", stage="intake")

    return state.model_copy(update={"stage": "extract"})
