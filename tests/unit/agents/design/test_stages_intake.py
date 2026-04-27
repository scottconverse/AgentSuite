"""Unit tests for agentsuite.agents.design.stages.intake."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.stages.intake import _classify_path, _walk, intake_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _make_state(tmp_path: Path, **overrides: object) -> RunState:
    defaults: dict[str, object] = {
        "agent_name": "design",
        "role_domain": "marketing",
        "user_request": "make a banner",
        "target_audience": "developers",
        "campaign_goal": "drive signups",
    }
    defaults.update(overrides)
    inp = DesignAgentInput(**defaults)  # type: ignore[arg-type]
    return RunState(run_id="r1", agent="design", inputs=inp)


def _make_ctx(tmp_path: Path) -> StageContext:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_intake_advances_to_extract(tmp_path: Path) -> None:
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    result = intake_stage(state, ctx)
    assert result.stage == "extract"


def test_intake_writes_manifest(tmp_path: Path) -> None:
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    assert manifest_path.exists()


def test_intake_manifest_contains_goal(tmp_path: Path) -> None:
    state = _make_state(tmp_path, campaign_goal="boost retention")
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    assert data["campaign_goal"] == "boost retention"


def test_intake_indexes_brand_docs(tmp_path: Path) -> None:
    brand = tmp_path / "brand.pdf"
    brand.write_text("brand")
    state = _make_state(tmp_path, brand_docs=[brand])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "brand-doc" in kinds


def test_intake_indexes_reference_assets(tmp_path: Path) -> None:
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG")
    state = _make_state(tmp_path, reference_assets=[ref])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "reference-asset" in kinds


def test_intake_indexes_anti_examples(tmp_path: Path) -> None:
    anti = tmp_path / "bad.jpg"
    anti.write_bytes(b"JFIF")
    state = _make_state(tmp_path, anti_examples=[anti])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "anti-example" in kinds


def test_classify_path_image() -> None:
    assert _classify_path(Path("hero.png")) == "image"
    assert _classify_path(Path("icon.svg")) == "image"


def test_classify_path_doc() -> None:
    assert _classify_path(Path("brand.md")) == "doc"


def test_classify_path_pdf() -> None:
    assert _classify_path(Path("guidelines.pdf")) == "pdf"


def test_classify_path_other() -> None:
    assert _classify_path(Path("data.xlsx")) == "other"


def test_walk_empty_dir(tmp_path: Path) -> None:
    assert _walk(tmp_path / "nonexistent") == []


def test_walk_skips_hidden_files(tmp_path: Path) -> None:
    (tmp_path / ".DS_Store").write_text("x")
    (tmp_path / "visible.md").write_text("y")
    result = _walk(tmp_path)
    names = [p.name for p in result]
    assert ".DS_Store" not in names
    assert "visible.md" in names
