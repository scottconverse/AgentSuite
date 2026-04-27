"""Unit tests for agentsuite.agents.design.stages.extract."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.stages.extract import extract_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_VALID_EXTRACT_JSON = json.dumps({
    "audience_profile": {
        "primary_persona": "senior designer",
        "demographics": "25-45, design-savvy",
        "psychographics": "quality-driven",
        "visual_sophistication": "high",
    },
    "brand_voice": {
        "tone_words": ["confident", "clean"],
        "writing_style": "terse",
        "forbidden_tones": ["gimmicky"],
    },
    "visual_signals": ["bold typography", "white space"],
    "typography_signals": {
        "heading_style": "sans-serif large",
        "body_style": "regular weight",
        "weight_preference": "medium",
        "observed_typefaces": ["Inter"],
    },
    "color_palette_observed": [{"hex_approx": "#0052CC", "role": "primary", "usage_context": "CTAs"}],
    "craft_anti_patterns": ["stock photography", "drop shadows"],
    "gaps": ["no logo files provided"],
})


def _make_ctx(tmp_path: Path, llm: MockLLMProvider) -> tuple[StageContext, ArtifactWriter]:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json(
        "inputs_manifest.json",
        {"target_audience": "devs", "campaign_goal": "launch", "channel": "web", "sources": []},
        kind="data",
        stage="intake",
    )
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm}), writer


def _make_state() -> RunState:
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="marketing",
        user_request="make a banner",
        target_audience="developers",
        campaign_goal="drive signups",
    )
    return RunState(run_id="r1", agent="design", stage="extract", inputs=inp)


def test_extract_advances_to_spec(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, _ = _make_ctx(tmp_path, llm)
    result = extract_stage(_make_state(), ctx)
    assert result.stage == "spec"


def test_extract_writes_extracted_context_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["brand_voice"]["tone_words"] == ["confident", "clean"]


def test_extract_surfaces_gaps_as_open_questions(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, _ = _make_ctx(tmp_path, llm)
    result = extract_stage(_make_state(), ctx)
    assert "no logo files provided" in result.open_questions


def test_extract_raises_on_invalid_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": "not valid json"})
    ctx, _ = _make_ctx(tmp_path, llm)
    with pytest.raises(ValueError, match="extract stage produced invalid JSON"):
        extract_stage(_make_state(), ctx)


def test_extract_tracks_cost(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, _ = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens > 0
