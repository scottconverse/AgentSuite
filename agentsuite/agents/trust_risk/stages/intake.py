"""Stage 1 — intake: index source materials, no LLM."""
from __future__ import annotations

from pathlib import Path
from typing import cast

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


_DOC_EXTS = {".pdf", ".docx", ".txt", ".md"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}


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
    inp = cast(TrustRiskAgentInput, state.inputs)
    sources: list[dict[str, str]] = []

    if inp.inputs_dir is not None:
        for p in _walk(inp.inputs_dir):
            sources.append({"kind": _classify_path(p), "path": str(p)})

    for p in inp.existing_policies:
        sources.append({"kind": "policy-doc", "path": str(p)})

    for p in inp.incident_reports:
        sources.append({"kind": "incident-report", "path": str(p)})

    manifest = {
        "product_name": inp.product_name,
        "risk_domain": inp.risk_domain,
        "stakeholder_context": inp.stakeholder_context,
        "regulatory_context": inp.regulatory_context,
        "threat_model_scope": inp.threat_model_scope,
        "compliance_frameworks": inp.compliance_frameworks,
        "sources": sources,
        "source_count": len(sources),
    }
    ctx.writer.write_json("inputs_manifest.json", manifest, kind="data", stage="intake")

    return state.model_copy(update={"stage": "extract"})
