"""Unit tests for agentsuite.agents.product.stages.extract."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.stages.extract import extract_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_VALID_EXTRACT_JSON = json.dumps({
    "user_pain_points": ["Users spend too long on manual tasks"],
    "competitor_gaps": ["Competitor A lacks automation"],
    "market_signals": ["Growing demand"],
    "technical_constraints": ["Must work offline"],
    "assumed_non_goals": ["Mobile app"],
    "open_questions": ["Max file size?"],
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
            "product_name": "TestProduct",
            "sources": sources or [],
        },
        kind="data",
        stage="intake",
    )
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm}), writer


def _make_state() -> RunState:
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product",
        user_request="build a spec",
        product_name="TestProduct",
        target_users="developers",
        core_problem="too much manual work",
    )
    return RunState(run_id="r1", agent="product", stage="extract", inputs=inp)


def test_extract_calls_llm_and_writes_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["user_pain_points"] == ["Users spend too long on manual tasks"]


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
    assert payload["user_pain_points"] == []


def test_extract_buckets_sources_by_kind(tmp_path: Path) -> None:
    sources = [
        {"path": "/docs/research1.md", "kind": "research-doc"},
        {"path": "/docs/competitor1.md", "kind": "competitor-doc"},
        {"path": "/docs/other.md", "kind": "other"},
    ]
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm, sources=sources)
    extract_stage(_make_state(), ctx)
    # Verify stage completed (sources were bucketed without error)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "parse_error" not in payload
