"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import cast

from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.agents.trust_risk.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest
from agentsuite.llm.json_extract import extract_json


SPEC_ARTIFACTS: list[str] = [
    "threat-model",
    "risk-register",
    "control-framework",
    "incident-response-plan",
    "compliance-matrix",
    "vendor-risk-assessment",
    "security-policy",
    "audit-readiness-report",
    "residual-risk-acceptance",
]


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any check has critical
    severity. Advances to 'execute' on success.
    """
    inp = cast(TrustRiskAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )
    extracted_context_str = json.dumps(extracted)

    template_vars: dict[str, object] = {
        "product_name": inp.product_name,
        "risk_domain": inp.risk_domain,
        "stakeholder_context": inp.stakeholder_context,
        "regulatory_context": inp.regulatory_context,
        "threat_model_scope": inp.threat_model_scope,
        "compliance_frameworks": inp.compliance_frameworks,
        "extracted_context": extracted_context_str,
    }

    artifact_contents: list[str] = []

    for stem in SPEC_ARTIFACTS:
        prompt = render_prompt(f"spec_{stem.replace('-', '_')}", **template_vars)
        response = llm.complete(LLMRequest(
            prompt=prompt,
            system=f"You are writing {stem}.md for a trust and risk team. Return ONLY markdown.",
            temperature=0.2,
        ))
        ctx.cost_tracker.add(Cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usd=response.usd,
            model=response.model,
        ))
        ctx.writer.write(f"{stem}.md", response.text, kind="spec", stage="spec")
        artifact_contents.append(response.text)

    artifact_snippets: dict[str, str] = {
        stem: content[:500]
        for stem, content in zip(SPEC_ARTIFACTS, artifact_contents)
    }
    consistency_prompt = render_prompt(
        "spec_consistency_check",
        product_name=inp.product_name,
        risk_domain=inp.risk_domain,
        artifact_snippets=artifact_snippets,
    )
    consistency_response = llm.complete(LLMRequest(
        prompt=consistency_prompt,
        system="You are checking 9 trust-risk-agent artifacts for consistency. Return ONLY JSON.",
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=consistency_response.input_tokens,
        output_tokens=consistency_response.output_tokens,
        usd=consistency_response.usd,
        model=consistency_response.model,
    ))

    try:
        report = extract_json(consistency_response.text)
    except ValueError as exc:
        raise ValueError(f"consistency check produced invalid JSON: {exc}") from exc

    ctx.writer.write_json("consistency_report.json", report, kind="data", stage="spec")

    critical = [c for c in report.get("mismatches", []) if c.get("severity") == "critical"]
    return state.model_copy(update={
        "stage": "execute",
        "requires_revision": bool(critical),
    })
