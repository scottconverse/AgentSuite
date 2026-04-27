"""Unit tests for agentsuite.agents.design.stages.execute."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.stages.execute import execute_stage
from agentsuite.agents.design.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState


_EXTRACTED = {
    "audience_profile": {"primary_persona": "senior designer"},
    "brand_voice": {"tone_words": ["confident", "clean"], "writing_style": "terse", "forbidden_tones": ["gimmicky"]},
    "visual_signals": ["bold typography", "white space"],
    "typography_signals": {"heading_style": "sans-serif"},
    "color_palette_observed": [],
    "craft_anti_patterns": ["stock photography"],
    "gaps": [],
}


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="marketing",
        user_request="launch campaign",
        target_audience="developers",
        campaign_goal="drive signups",
        channel="social",
    )
    return RunState(run_id="r1", agent="design", stage="execute", inputs=inp)


def _make_ctx(writer: ArtifactWriter) -> StageContext:
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_execute_advances_to_qa(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    result = execute_stage(_make_state(), _make_ctx(writer))
    assert result.stage == "qa"


def test_execute_writes_eight_brief_templates(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    for name in TEMPLATE_NAMES:
        assert (writer.run_dir / "brief-template-library" / f"{name}.md").exists()


def test_execute_writes_export_manifest(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    manifest_path = writer.run_dir / "export-manifest-template.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "templates" in data
    assert len(data["templates"]) == 8


def test_execute_no_llm_call(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    ctx = _make_ctx(writer)
    execute_stage(_make_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens == 0


def test_execute_values_contain_tone_from_extracted(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    # Check one rendered template contains "confident" from tone_words
    banner = writer.run_dir / "brief-template-library" / "banner-ad.md"
    assert banner.exists()
    body = banner.read_text(encoding="utf-8")
    assert "confident" in body
