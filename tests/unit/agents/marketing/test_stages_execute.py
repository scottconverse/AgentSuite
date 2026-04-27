"""Unit tests for agentsuite.agents.marketing.stages.execute."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.marketing.input_schema import MarketingAgentInput
from agentsuite.agents.marketing.stages.execute import execute_stage
from agentsuite.agents.marketing.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState


_EXTRACTED = {
    "brand_signals": ["award-winning ergonomic design", "sustainability certified"],
    "audience_insights": ["remote professionals aged 28-45", "health-conscious commuters"],
    "channel_signals": ["Shop Now", "Get 20% Off"],
    "budget_signals": ["10% CTR", "5x ROAS"],
}


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="Launch our Q2 product campaign across social and email",
        brand_name="LumaGear",
        campaign_goal="Drive 20% increase in Q2 revenue through targeted digital campaigns",
        target_market="Remote professionals aged 28-45 seeking ergonomic home office gear",
        budget_range="$75k–$120k over 3 months",
        timeline="Q2 2026, April–June",
        channels="paid social, email, content marketing",
    )
    return RunState(run_id="r1", agent="marketing", stage="execute", inputs=inp)


def _make_ctx(writer: ArtifactWriter) -> StageContext:
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_execute_advances_to_qa(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    result = execute_stage(_make_state(), _make_ctx(writer))
    assert result.stage == "qa"


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
    assert "brand_name" in data
    assert "campaign_goal" in data
    assert "brief_templates" in data
    assert "spec_artifacts" in data
    assert len(data["brief_templates"]) == 8


def test_execute_no_llm_call(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    ctx = _make_ctx(writer)
    execute_stage(_make_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens == 0
