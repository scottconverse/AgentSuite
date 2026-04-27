"""Unit tests for agentsuite.agents.engineering.stages.execute."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.stages.execute import execute_stage
from agentsuite.agents.engineering.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState


_EXTRACTED = {
    "known_bottlenecks": ["database query latency", "cache eviction storms"],
    "architecture_patterns": ["microservices", "event-driven"],
    "risk_areas": ["single point of failure at API gateway"],
}


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering",
        user_request="Design a high-throughput order processing system",
        system_name="OrderFlow",
        problem_domain="order processing at scale",
        tech_stack="Python + FastAPI + PostgreSQL + Redis",
        scale_requirements="10k RPM, 99.9% uptime, <200ms p99",
        team_size="4 engineers, 1 SRE",
    )
    return RunState(run_id="r1", agent="engineering", stage="execute", inputs=inp)


def _make_ctx(writer: ArtifactWriter) -> StageContext:
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_execute_renders_all_eight_templates(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    for name in TEMPLATE_NAMES:
        assert (writer.run_dir / "brief-template-library" / f"{name}.md").exists(), (
            f"Missing brief-template-library/{name}.md"
        )


def test_execute_writes_export_manifest(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    manifest_path = writer.run_dir / "export-manifest-template.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "system_name" in data
    assert "tech_stack" in data
    assert "brief_templates" in data
    assert "spec_artifacts" in data
    assert len(data["brief_templates"]) == 8


def test_execute_advances_to_qa(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    result = execute_stage(_make_state(), _make_ctx(writer))
    assert result.stage == "qa"


def test_execute_no_llm_call(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    ctx = _make_ctx(writer)
    execute_stage(_make_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens == 0
