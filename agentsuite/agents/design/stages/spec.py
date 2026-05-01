"""Stage 3 — spec: generate 9 markdown spec artifacts + consistency check."""
from __future__ import annotations

import json
from typing import Any, cast

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.prompt_loader import render_prompt
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState
from agentsuite.kernel.stages.spec import SpecStageConfig, kernel_spec_stage


SPEC_ARTIFACTS: list[str] = [
    "visual-direction",
    "design-brief",
    "mood-board-spec",
    "brand-rules-extracted",
    "image-generation-prompt",
    "revision-instructions",
    "design-qa-report",
    "accessibility-audit-template",
    "final-asset-acceptance-checklist",
]


_PROMPT_BY_ARTIFACT: dict[str, str] = {
    "visual-direction": "spec_visual_direction",
    "design-brief": "spec_design_brief",
    "mood-board-spec": "spec_mood_board_spec",
    "brand-rules-extracted": "spec_brand_rules_extracted",
    "image-generation-prompt": "spec_image_generation_prompt",
    "revision-instructions": "spec_revision_instructions",
    "design-qa-report": "spec_design_qa_report",
    "accessibility-audit-template": "spec_accessibility_audit_template",
    "final-asset-acceptance-checklist": "spec_final_asset_acceptance_checklist",
}


_CHANNEL_DELIVERABLES: dict[str, str] = {
    "web": "web banner, landing page hero",
    "social": "social post graphic, story card",
    "email": "email header, hero image",
    "print": "print flyer, poster",
    "video": "video thumbnail, end card",
    "deck": "presentation slide, title card",
    "other": "primary campaign asset",
}

_CHANNEL_DIMENSIONS: dict[str, str] = {
    "web": "728x90, 300x250, 160x600",
    "social": "1080x1080, 1200x630",
    "email": "600px wide",
    "print": "8.5x11in 300dpi, A4 300dpi",
    "video": "1280x720, 1920x1080",
    "deck": "1920x1080 (16:9)",
    "other": "as specified by client",
}

_CHANNEL_FORMAT: dict[str, str] = {
    "web": "PNG/SVG optimized for web",
    "social": "JPG/PNG, platform-native specs",
    "email": "JPG/PNG inline, <150KB",
    "print": "PDF/TIFF 300dpi CMYK",
    "video": "MP4/PNG sequence",
    "deck": "PPTX/PDF/PNG",
    "other": "TBD per brief",
}


def _build_artifact_prompt(stem: str, extracted: dict[str, Any], state: RunState) -> str:
    inp = cast(DesignAgentInput, state.inputs)
    brand_voice = extracted.get("brand_voice", {})
    brand_voice_str = (
        json.dumps(brand_voice, indent=2) if isinstance(brand_voice, dict) else str(brand_voice)
    )
    visual_signals = extracted.get("visual_signals", [])
    visual_concept = visual_signals[0] if visual_signals else "TBD"
    channel = inp.channel

    template_vars: dict[str, object] = {
        "campaign_goal": inp.campaign_goal,
        "target_audience": inp.target_audience,
        "brand_voice": brand_voice_str,
        "extracted_context": json.dumps(extracted, indent=2),
        "deliverables": _CHANNEL_DELIVERABLES.get(channel, "primary campaign asset"),
        "visual_concept_name": visual_concept,
        "visual_direction_summary": "(see visual-direction.md)",
        "deliverable_name": f"{channel} asset",
        "dimensions": _CHANNEL_DIMENSIONS.get(channel, "as specified"),
        "qa_findings": "(to be completed per deliverable during execute stage)",
        "stakeholder_feedback": "(to be completed per deliverable)",
        "specs_summary": "(refer to visual-direction.md and design-brief.md)",
        "design_description": "(to be provided per deliverable)",
        "platform": channel,
        "delivery_format": _CHANNEL_FORMAT.get(channel, "TBD"),
        "platform_targets": channel,
    }
    return render_prompt(_PROMPT_BY_ARTIFACT[stem], **template_vars)


def _artifact_system_msg(stem: str) -> str:
    return f"You are writing {stem}.md for a designer. Return ONLY markdown."


def _build_consistency_prompt(artifact_snippets: dict[str, str], state: RunState) -> str:
    # Design passes full artifact bodies (not snippets) keyed as {stem.md: content}
    # artifact_snippets has {f"{stem}.md": content} due to snippet_key_fn below
    return render_prompt("consistency_check", artifacts=artifact_snippets)


_SPEC_CONFIG = SpecStageConfig(
    spec_artifacts=SPEC_ARTIFACTS,
    build_artifact_prompt_fn=_build_artifact_prompt,
    artifact_system_msg_fn=_artifact_system_msg,
    build_consistency_prompt_fn=_build_consistency_prompt,
    consistency_system_msg="You are checking 9 artifacts for design consistency. Return ONLY JSON.",
    artifact_snippet_truncate=10_000_000,  # full content — original passes complete bodies
    snippet_key_fn=lambda s: f"{s}.md",
)


def spec_stage(state: RunState, ctx: StageContext) -> RunState:
    """Stage 3 handler: generate 9 spec markdown artifacts + consistency check.

    Reads extracted_context.json, calls LLM once per artifact, then runs a
    consistency check. Raises ConsistencyCheckFailed if any mismatch is critical.
    Advances to 'execute' on success.
    """
    return kernel_spec_stage(_SPEC_CONFIG, state, ctx)
