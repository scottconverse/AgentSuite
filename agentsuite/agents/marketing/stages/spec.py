"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.spec import SpecStageConfig, kernel_spec_stage


SPEC_ARTIFACTS: list[str] = [
    "campaign-brief",
    "target-audience-profile",
    "messaging-framework",
    "content-calendar",
    "channel-strategy",
    "seo-keyword-plan",
    "competitive-positioning",
    "launch-plan",
    "measurement-framework",
]


def _build_artifact_prompt(stem: str, extracted: dict[str, Any], state: RunState) -> str:
    inp = cast(MarketingAgentInput, state.inputs)
    template_vars: dict[str, object] = {
        "brand_name": inp.brand_name,
        "campaign_goal": inp.campaign_goal,
        "target_market": inp.target_market,
        "budget_range": inp.budget_range,
        "timeline": inp.timeline,
        "channels": inp.channels,
        "extracted_context": json.dumps(extracted),
    }
    return render_prompt(f"spec_{stem.replace('-', '_')}", **template_vars)


def _artifact_system_msg(stem: str) -> str:
    return f"You are writing {stem}.md for a marketing team. Return ONLY markdown."


def _build_consistency_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    inp = cast(MarketingAgentInput, state.inputs)
    return render_prompt(
        "spec_consistency_check",
        brand_name=inp.brand_name,
        campaign_goal=inp.campaign_goal,
        artifact_snippets=artifact_snippets,
    )


_SPEC_CONFIG = SpecStageConfig(
    spec_artifacts=SPEC_ARTIFACTS,
    build_artifact_prompt_fn=_build_artifact_prompt,
    artifact_system_msg_fn=_artifact_system_msg,
    build_consistency_prompt_fn=_build_consistency_prompt,
    consistency_system_msg="You are checking 9 marketing-agent artifacts for consistency. Return ONLY JSON.",
    artifact_snippet_truncate=500,
    snippet_key_fn=lambda s: s,
)


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any check has critical
    severity. Advances to 'execute' on success.
    """
    return kernel_spec_stage(_SPEC_CONFIG, state, ctx)
