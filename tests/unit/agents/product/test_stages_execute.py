"""Unit tests for agentsuite.agents.product.stages.execute."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.product.input_schema import ProductAgentInput
from agentsuite.agents.product.stages.execute import execute_stage
from agentsuite.agents.product.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState


_EXTRACTED = {
    "user_pain_points": ["onboarding is too slow", "no offline mode"],
    "competitive_gaps": ["no mobile app", "poor integrations"],
    "opportunity_areas": ["enterprise tier", "API access"],
}


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product",
        user_request="Build a data-entry automation tool for small businesses",
        product_name="Acme App",
        target_users="small business owners",
        core_problem="too much manual data entry",
        timeline_constraint="MVP in 8 weeks",
        success_metric_goals="20% reduction in onboarding time",
    )
    return RunState(run_id="r1", agent="product", stage="execute", inputs=inp)


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
    assert "product_name" in data
    assert "target_users" in data
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
