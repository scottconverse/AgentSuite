"""Unit tests for agentsuite.agents.marketing.stages.extract."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.stages.extract import extract_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_VALID_EXTRACT_JSON = json.dumps({
    "audience_insights": ["Millennial urban professionals aged 25-40"],
    "competitor_gaps": ["Competitors lack localized content strategy"],
    "brand_signals": ["10-year track record with enterprise clients"],
    "channel_signals": ["High LinkedIn engagement among target audience"],
    "budget_signals": ["Typical CPL in this vertical is $45-$80"],
    "open_questions": ["What is the expected CAC payback period?"],
})


def _make_ctx(
    tmp_path: Path,
    llm: MockLLMProvider,
    sources: list[dict] | None = None,
) -> tuple[StageContext, ArtifactWriter]:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json(
        "inputs_manifest.json",
        {
            "brand_name": "TestBrand",
            "sources": sources or [],
        },
        kind="data",
        stage="intake",
    )
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm}), writer


def _make_state() -> RunState:
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="build a campaign",
        brand_name="TestBrand",
        campaign_goal="increase brand awareness by 30% in Q3",
        target_market="millennial professionals in urban markets",
    )
    return RunState(run_id="r1", agent="marketing", stage="extract", inputs=inp)


def test_extract_calls_llm_and_writes_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["audience_insights"] == ["Millennial urban professionals aged 25-40"]


def test_extract_advances_to_spec(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, _ = _make_ctx(tmp_path, llm)
    result = extract_stage(_make_state(), ctx)
    assert result.stage == "spec"


def test_extract_handles_invalid_json_gracefully(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": "not json"})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("parse_error") is True
    assert payload["audience_insights"] == []


def test_extract_buckets_sources_by_kind(tmp_path: Path) -> None:
    sources = [
        {"path": "/docs/brand-guidelines.pdf", "kind": "brand-doc"},
        {"path": "/docs/brand-voice.pdf", "kind": "brand-doc"},
        {"path": "/docs/competitor-analysis.pdf", "kind": "competitor-doc"},
        {"path": "/docs/other-doc.pdf", "kind": "other"},
    ]
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm, sources=sources)
    extract_stage(_make_state(), ctx)
    # Verify stage completed (sources were bucketed without error)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "parse_error" not in payload
