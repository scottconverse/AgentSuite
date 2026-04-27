"""Unit tests for agentsuite.agents.engineering.stages.intake."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput
from agentsuite.agents.engineering.stages.intake import intake_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _make_state(tmp_path: Path, **overrides: object) -> RunState:
    defaults: dict[str, object] = {
        "agent_name": "engineering",
        "role_domain": "engineering",
        "user_request": "design a distributed caching system",
        "system_name": "CacheService",
        "problem_domain": "distributed caching",
        "tech_stack": "Python + Redis + Kubernetes",
        "scale_requirements": "10k RPM, 99.9% uptime",
    }
    defaults.update(overrides)
    inp = EngineeringAgentInput(**defaults)  # type: ignore[arg-type]
    return RunState(run_id="r1", agent="engineering", inputs=inp)


def _make_ctx(tmp_path: Path) -> StageContext:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_intake_creates_manifest_json(tmp_path: Path) -> None:
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    for key in ("system_name", "problem_domain", "tech_stack", "scale_requirements",
                 "security_requirements", "team_size", "sources", "source_count"):
        assert key in data


def test_intake_classifies_codebase_docs(tmp_path: Path) -> None:
    doc = tmp_path / "architecture.md"
    doc.write_text("# Architecture")
    state = _make_state(tmp_path, existing_codebase_docs=[doc])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "codebase-doc" in kinds


def test_intake_classifies_adr_history(tmp_path: Path) -> None:
    adr = tmp_path / "adr-001-use-redis.md"
    adr.write_text("# ADR 001")
    state = _make_state(tmp_path, adr_history=[adr])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "adr" in kinds


def test_intake_advances_to_extract(tmp_path: Path) -> None:
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    result = intake_stage(state, ctx)
    assert result.stage == "extract"


def test_intake_source_count(tmp_path: Path) -> None:
    doc1 = tmp_path / "arch.md"
    doc1.write_text("arch")
    doc2 = tmp_path / "readme.md"
    doc2.write_text("readme")
    adr1 = tmp_path / "adr-001.md"
    adr1.write_text("adr")
    state = _make_state(tmp_path, existing_codebase_docs=[doc1, doc2], adr_history=[adr1])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    assert data["source_count"] == 3
