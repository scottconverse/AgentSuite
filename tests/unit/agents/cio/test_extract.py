"""Unit tests for agentsuite.agents.cio.stages.extract."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.stages.extract import extract_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_VALID_EXTRACT_JSON = json.dumps({
    "technology_pain_points": ["Legacy ERP system causing integration bottlenecks"],
    "strategic_gaps": ["No cloud migration roadmap", "Absent data governance policy"],
    "vendor_landscape": ["Oracle ERP", "Microsoft 365", "AWS (partial)"],
    "digital_maturity_signals": ["Manual approval workflows still dominant"],
    "budget_signals": ["Flat IT budget for FY2026", "Capex limited to $2M"],
    "open_questions": ["What is the timeline for the cloud-first initiative?"],
})

# keyword that will match the system string in extract_stage
_MOCK_KEYWORD = "extracting structured IT and technology context"


def _make_ctx(
    tmp_path: Path,
    llm: MockLLMProvider,
    sources: list[dict] | None = None,
) -> tuple[StageContext, ArtifactWriter]:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json(
        "inputs_manifest.json",
        {
            "organization_name": "Acme Corp",
            "sources": sources or [],
        },
        kind="data",
        stage="intake",
    )
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm}), writer


def _make_state() -> RunState:
    inp = CIOAgentInput(
        agent_name="cio",
        role_domain="cio-ops",
        user_request="assess IT strategy",
        organization_name="Acme Corp",
        strategic_priorities="Cloud-first, data-driven decision making",
        it_maturity_level="Level 2 – Repeatable",
    )
    return RunState(run_id="r1", agent="cio", stage="extract", inputs=inp)


def test_extract_writes_extracted_context(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={_MOCK_KEYWORD: _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()


def test_extract_advances_stage(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={_MOCK_KEYWORD: _VALID_EXTRACT_JSON})
    ctx, _ = _make_ctx(tmp_path, llm)
    result = extract_stage(_make_state(), ctx)
    assert result.stage == "spec"


def test_extract_fallback_on_invalid_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={_MOCK_KEYWORD: "not valid json"})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("parse_error") is True
    assert payload["technology_pain_points"] == []


def test_extract_parses_valid_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={_MOCK_KEYWORD: _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["technology_pain_points"] == ["Legacy ERP system causing integration bottlenecks"]
    assert "parse_error" not in payload
