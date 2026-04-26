"""Stage 3 — spec: generate the 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMProvider, LLMRequest


SPEC_ARTIFACTS: list[str] = [
    "brand-system",
    "founder-voice-guide",
    "product-positioning",
    "audience-map",
    "claims-and-proof-library",
    "visual-style-guide",
    "campaign-production-workflow",
    "asset-qa-checklist",
    "reusable-prompt-library",
]


_PROMPT_BY_ARTIFACT: dict[str, str] = {
    "brand-system": "spec_brand_system",
    "founder-voice-guide": "spec_voice_guide",
    "product-positioning": "spec_positioning",
    "audience-map": "spec_audience_map",
    "claims-and-proof-library": "spec_claims_library",
    "visual-style-guide": "spec_visual_guide",
    "campaign-production-workflow": "spec_workflow",
    "asset-qa-checklist": "spec_qa_checklist",
    "reusable-prompt-library": "spec_prompt_library",
}


class ConsistencyCheckFailed(RuntimeError):
    """Raised when the cross-artifact consistency check finds critical mismatches."""


def _read_voice_samples(inp: FounderAgentInput) -> str:
    """Concatenate the founder's voice-sample files into a single string for prompting."""
    if not inp.founder_voice_samples:
        return ""
    parts: list[str] = []
    for path in inp.founder_voice_samples:
        try:
            parts.append(Path(path).read_text(encoding="utf-8", errors="replace")[:5000])
        except OSError:
            continue
    return "\n---\n".join(parts)


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + run consistency check.

    Sequentially calls the LLM once per SPEC_ARTIFACTS entry, writing each result
    as ``<stem>.md`` in the run dir. After all 9 land, runs a consistency-check
    LLM call across the bodies, writes ``consistency_report.json``, and raises
    ``ConsistencyCheckFailed`` if any mismatch has severity == "critical".
    Advances stage to "execute" on success.
    """
    inp = cast(FounderAgentInput, state.inputs)
    llm: LLMProvider = ctx.edits["llm"]

    extracted = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )
    voice_samples = _read_voice_samples(inp)

    artifact_bodies: dict[str, str] = {}

    for stem in SPEC_ARTIFACTS:
        prompt_name = _PROMPT_BY_ARTIFACT[stem]
        prompt = render_prompt(
            prompt_name,
            business_goal=inp.business_goal,
            extracted_context_json=json.dumps(extracted, indent=2),
            voice_samples=voice_samples,
        )
        # System line includes the artifact filename so MockLLMProvider keying works in tests
        response = llm.complete(LLMRequest(
            prompt=prompt,
            system=f"You are writing {stem}.md for a founder/operator. Return ONLY markdown.",
            temperature=0.2,
        ))
        ctx.cost_tracker.add(Cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usd=response.usd,
        ))
        ctx.writer.write(f"{stem}.md", response.text, kind="spec", stage="spec")
        artifact_bodies[f"{stem}.md"] = response.text

    consistency_prompt = render_prompt("consistency_check", artifacts=artifact_bodies)
    consistency_response = llm.complete(LLMRequest(
        prompt=consistency_prompt,
        system="You are checking 9 artifacts for cross-document consistency. Return ONLY JSON.",
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

    critical = [m for m in report.get("mismatches", []) if m.get("severity") == "critical"]
    if critical:
        raise ConsistencyCheckFailed(
            f"{len(critical)} critical mismatch(es): "
            + "; ".join(m.get("details", "") for m in critical)
        )

    return state.model_copy(update={"stage": "execute"})
