"""Unit tests for agentsuite.agents.product.stages.intake."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.stages.intake import intake_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _make_state(tmp_path: Path, **overrides: object) -> RunState:
    defaults: dict[str, object] = {
        "agent_name": "product",
        "role_domain": "product",
        "user_request": "build a product spec",
        "product_name": "TestProduct",
        "target_users": "developers",
        "core_problem": "too much toil",
    }
    defaults.update(overrides)
    inp = ProductAgentInput(**defaults)  # type: ignore[arg-type]
    return RunState(run_id="r1", agent="product", inputs=inp)


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
    for key in ("product_name", "target_users", "core_problem", "sources", "source_count"):
        assert key in data


def test_intake_classifies_research_docs(tmp_path: Path) -> None:
    research = tmp_path / "interviews.pdf"
    research.write_bytes(b"%PDF")
    state = _make_state(tmp_path, research_docs=[research])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "research-doc" in kinds


def test_intake_classifies_competitor_docs(tmp_path: Path) -> None:
    competitor = tmp_path / "teardown.md"
    competitor.write_text("competitor analysis")
    state = _make_state(tmp_path, competitor_docs=[competitor])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "competitor-doc" in kinds


def test_intake_advances_to_extract(tmp_path: Path) -> None:
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    result = intake_stage(state, ctx)
    assert result.stage == "extract"


def test_intake_source_count(tmp_path: Path) -> None:
    r1 = tmp_path / "r1.pdf"
    r1.write_bytes(b"%PDF")
    r2 = tmp_path / "r2.txt"
    r2.write_text("survey")
    c1 = tmp_path / "comp.json"
    c1.write_text("{}")
    state = _make_state(tmp_path, research_docs=[r1, r2], competitor_docs=[c1])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    assert data["source_count"] == 3
