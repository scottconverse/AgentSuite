"""Stage 3 — spec: generate the 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.spec import SpecStageConfig, kernel_spec_stage


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


def _build_artifact_prompt(stem: str, extracted: dict[str, Any], state: RunState) -> str:
    inp = cast(FounderAgentInput, state.inputs)
    voice_samples = _read_voice_samples(inp)
    return render_prompt(
        _PROMPT_BY_ARTIFACT[stem],
        business_goal=inp.business_goal,
        extracted_context_json=json.dumps(extracted, indent=2),
        voice_samples=voice_samples,
    )


def _artifact_system_msg(stem: str) -> str:
    # System line includes the artifact filename so MockLLMProvider keying works in tests
    return f"You are writing {stem}.md for a founder/operator. Return ONLY markdown."


def _build_consistency_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    # founder passes full bodies (not snippets) as {f"{stem}.md": content}
    # convert from bare stem keys back to "{stem}.md" keys for the render_prompt call
    bodies_with_ext = {f"{k}.md": v for k, v in artifact_snippets.items()}
    return render_prompt("consistency_check", artifacts=bodies_with_ext)


_SPEC_CONFIG = SpecStageConfig(
    spec_artifacts=SPEC_ARTIFACTS,
    build_artifact_prompt_fn=_build_artifact_prompt,
    artifact_system_msg_fn=_artifact_system_msg,
    build_consistency_prompt_fn=_build_consistency_prompt,
    consistency_system_msg="You are checking 9 artifacts for cross-document consistency. Return ONLY JSON.",
    # Use full artifact bodies for consistency check (no truncation)
    artifact_snippet_truncate=10_000_000,  # effectively unlimited
    snippet_key_fn=lambda s: s,
)


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + run consistency check.

    Sequentially calls the LLM once per SPEC_ARTIFACTS entry, writing each result
    as ``<stem>.md`` in the run dir. After all 9 land, runs a consistency-check
    LLM call across the bodies, writes ``consistency_report.json``, and raises
    ``ConsistencyCheckFailed`` if any mismatch has severity == "critical".
    Advances stage to "execute" on success.
    """
    return kernel_spec_stage(_SPEC_CONFIG, state, ctx)
