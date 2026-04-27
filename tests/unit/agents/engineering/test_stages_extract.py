"""Unit tests for agentsuite.agents.engineering.stages.extract."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.stages.extract import extract_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_VALID_EXTRACT_JSON = json.dumps({
    "existing_patterns": ["Service-oriented architecture"],
    "known_bottlenecks": ["DB connection pool exhaustion under load"],
    "security_risks": ["No rate limiting on public endpoints"],
    "tech_debt_items": ["Synchronous blocking calls in async context"],
    "integration_points": ["Stripe API", "SendGrid"],
    "open_questions": ["What is the expected p99 latency SLO?"],
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
            "system_name": "TestSystem",
            "sources": sources or [],
        },
        kind="data",
        stage="intake",
    )
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm}), writer


def _make_state() -> RunState:
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering",
        user_request="design a spec",
        system_name="TestSystem",
        problem_domain="distributed job scheduling",
        tech_stack="Python + FastAPI + PostgreSQL + Redis",
        scale_requirements="10k RPM, 99.9% uptime, <200ms p99",
    )
    return RunState(run_id="r1", agent="engineering", stage="extract", inputs=inp)


def test_extract_calls_llm_and_writes_json(tmp_path: Path) -> None:
    llm = MockLLMProvider(responses={"extract": _VALID_EXTRACT_JSON})
    ctx, writer = _make_ctx(tmp_path, llm)
    extract_stage(_make_state(), ctx)
    out = writer.run_dir / "extracted_context.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["existing_patterns"] == ["Service-oriented architecture"]


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
    assert payload["existing_patterns"] == []


def test_extract_buckets_sources_by_kind(tmp_path: Path) -> None:
    sources = [
        {"path": "/docs/arch.md", "kind": "codebase-doc"},
        {"path": "/docs/adr-001.md", "kind": "adr"},
        {"path": "/docs/incident-42.md", "kind": "incident-report"},
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
