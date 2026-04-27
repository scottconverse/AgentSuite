"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import cast

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest


SPEC_ARTIFACTS: list[str] = [
    "it-strategy",
    "technology-roadmap",
    "vendor-portfolio",
    "digital-transformation-plan",
    "it-governance-framework",
    "enterprise-architecture",
    "budget-allocation-model",
    "workforce-development-plan",
    "it-risk-appetite-statement",
]


class ConsistencyCheckFailed(RuntimeError):
    """Raised when the cross-artifact consistency check finds critical mismatches."""


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any check has critical
    severity. Advances to 'execute' on success.
    """
    inp = cast(CIOAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )
    extracted_context_str = json.dumps(extracted)

    template_vars: dict[str, object] = {
        "organization_name": inp.organization_name,
        "strategic_priorities": inp.strategic_priorities,
        "it_maturity_level": inp.it_maturity_level,
        "extracted_context": extracted_context_str,
        "budget_context": inp.budget_context,
        "digital_initiatives": inp.digital_initiatives,
        "regulatory_environment": inp.regulatory_environment,
    }

    artifact_contents: list[str] = []

    for stem in SPEC_ARTIFACTS:
        prompt = render_prompt(f"spec_{stem.replace('-', '_')}", **template_vars)
        response = llm.complete(LLMRequest(
            prompt=prompt,
            system=f"You are writing {stem}.md for a CIO team. Return ONLY markdown.",
            temperature=0.2,
        ))
        ctx.cost_tracker.add(Cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usd=response.usd,
        ))
        ctx.writer.write(f"{stem}.md", response.text, kind="spec", stage="spec")
        artifact_contents.append(response.text)

    artifact_snippets: dict[str, str] = {
        stem: content[:200]
        for stem, content in zip(SPEC_ARTIFACTS, artifact_contents)
    }
    consistency_prompt = render_prompt(
        "spec_consistency_check",
        organization_name=inp.organization_name,
        strategic_priorities=inp.strategic_priorities,
        artifact_snippets=artifact_snippets,
    )
    consistency_response = llm.complete(LLMRequest(
        prompt=consistency_prompt,
        system="You are checking 9 CIO artifacts for consistency. Return ONLY JSON.",
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=consistency_response.input_tokens,
        output_tokens=consistency_response.output_tokens,
        usd=consistency_response.usd,
    ))

    try:
        report = json.loads(consistency_response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"consistency check produced invalid JSON: {exc}") from exc

    ctx.writer.write_json("consistency_report.json", report, kind="data", stage="spec")

    critical = [c for c in report.get("mismatches", []) if c.get("severity") == "critical"]
    if critical:
        raise ConsistencyCheckFailed(
            f"{len(critical)} critical consistency failure(s): "
            + "; ".join(c.get("detail", "") for c in critical)
        )

    return state.model_copy(update={"stage": "execute"})
