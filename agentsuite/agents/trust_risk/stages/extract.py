"""Stage 2 — extract: LLM pass over indexed trust/risk source materials."""
from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest

_FALLBACK: dict[str, object] = {
    "known_threats": [],
    "existing_controls": [],
    "compliance_gaps": [],
    "incident_patterns": [],
    "vendor_risks": [],
    "open_questions": [],
    "parse_error": True,
}


def _read_manifest_sources(manifest_path: Path) -> dict[str, list[str]]:
    """Read manifest and bucket source paths by kind."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    buckets: dict[str, list[str]] = {
        "policy-doc": [],
        "incident-report": [],
    }
    for s in manifest.get("sources", []):
        kind = s.get("kind", "other")
        if kind in buckets:
            buckets[kind].append(s["path"])
    return buckets


def extract_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 2 handler: LLM extracts structured trust/risk context, writes extracted_context.json.

    Reads inputs_manifest.json from intake stage, calls LLM with trust/risk extract prompt,
    parses JSON response. On parse failure returns fallback with parse_error=True.
    Advances to 'spec'.
    """
    inp = cast(TrustRiskAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    manifest_path = ctx.writer.run_dir / "inputs_manifest.json"
    buckets = _read_manifest_sources(manifest_path)

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_count = len(manifest_data.get("sources", []))

    prompt = render_prompt(
        "extract",
        product_name=inp.product_name,
        risk_domain=inp.risk_domain,
        stakeholder_context=inp.stakeholder_context,
        source_count=source_count,
        existing_policies=buckets["policy-doc"],
        incident_reports=buckets["incident-report"],
    )
    response = llm.complete(LLMRequest(
        prompt=prompt,
        system="You are extracting structured trust and risk context from policy and incident documents. Return ONLY valid JSON.",
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        usd=response.usd,
    ))

    try:
        parsed = json.loads(response.text)
    except json.JSONDecodeError:
        parsed = dict(_FALLBACK)

    ctx.writer.write_json("extracted_context.json", parsed, kind="data", stage="extract")

    return state.model_copy(update={"stage": "spec"})
