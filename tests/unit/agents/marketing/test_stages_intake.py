"""Unit tests for agentsuite.agents.marketing.stages.intake."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.stages.intake import intake_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import RunState


def _make_state(tmp_path: Path, **overrides: object) -> RunState:
    defaults: dict[str, object] = {
        "agent_name": "marketing",
        "role_domain": "marketing-ops",
        "user_request": "launch a Q3 brand awareness campaign",
        "brand_name": "AcmeBrand",
        "campaign_goal": "increase brand awareness by 30%",
        "target_market": "millennials in urban areas",
    }
    defaults.update(overrides)
    inp = MarketingAgentInput(**defaults)  # type: ignore[arg-type]
    return RunState(run_id="r1", agent="marketing", inputs=inp)


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
    for key in ("brand_name", "campaign_goal", "target_market", "budget_range",
                 "timeline", "channels", "sources", "source_count"):
        assert key in data


def test_intake_classifies_brand_docs(tmp_path: Path) -> None:
    doc = tmp_path / "brand-guidelines.pdf"
    doc.write_text("brand guidelines")
    state = _make_state(tmp_path, existing_brand_docs=[doc])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    kinds = [s["kind"] for s in data["sources"]]
    assert "brand-doc" in kinds


def test_intake_classifies_competitor_docs(tmp_path: Path) -> None:
    doc = tmp_path / "competitor-analysis.docx"
    doc.write_text("competitor analysis")
    state = _make_state(tmp_path, competitor_docs=[doc])
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
    brand1 = tmp_path / "brand-guide.pdf"
    brand1.write_text("brand")
    brand2 = tmp_path / "style-guide.md"
    brand2.write_text("style")
    comp1 = tmp_path / "competitor.txt"
    comp1.write_text("competitor")
    state = _make_state(
        tmp_path,
        existing_brand_docs=[brand1, brand2],
        competitor_docs=[comp1],
    )
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    manifest_path = tmp_path / "runs" / "r1" / "inputs_manifest.json"
    data = json.loads(manifest_path.read_text())
    assert data["source_count"] == 3
