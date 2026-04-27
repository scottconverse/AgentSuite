"""Unit tests for agentsuite.agents.cio.stages.execute."""
from __future__ import annotations

from pathlib import Path

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.stages.execute import execute_stage
from agentsuite.agents.cio.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState


_EXTRACTED = {
    "technology_pain_points": ["Legacy ERP system", "fragmented data warehouse"],
    "strategic_gaps": ["cloud adoption lag", "cybersecurity maturity"],
    "vendor_landscape": ["SAP", "Microsoft Azure", "Snowflake"],
    "digital_maturity_signals": ["ad-hoc reporting", "manual workflows"],
    "budget_signals": ["flat IT budget", "capex constraints"],
    "open_questions": ["cloud-first strategy timeline"],
}


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = CIOAgentInput(
        agent_name="cio",
        role_domain="cio-ops",
        user_request="Develop a comprehensive IT strategy for Acme Corp Q2 2026",
        organization_name="Acme Corp",
        strategic_priorities="Cloud Modernization\nCybersecurity Uplift\nData & Analytics Platform",
        it_maturity_level="Level 2 – Repeatable",
        budget_context="$12M annual IT capex",
        digital_initiatives="ERP Cloud Migration\nCustomer Data Platform",
        regulatory_environment="SOX, HIPAA",
    )
    return RunState(run_id="r1", agent="cio", stage="execute", inputs=inp)


def _make_ctx(writer: ArtifactWriter) -> StageContext:
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={})


def test_execute_writes_all_brief_templates(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    for name in TEMPLATE_NAMES:
        assert (writer.run_dir / "brief-template-library" / f"{name}.md").exists(), (
            f"Missing brief-template-library/{name}.md"
        )


def test_execute_advances_stage(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    result = execute_stage(_make_state(), _make_ctx(writer))
    assert result.stage == "qa"


def test_execute_brief_template_count(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    lib_dir = writer.run_dir / "brief-template-library"
    written = list(lib_dir.glob("*.md"))
    assert len(written) == 8


def test_execute_templates_non_empty(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    execute_stage(_make_state(), _make_ctx(writer))
    for name in TEMPLATE_NAMES:
        path = writer.run_dir / "brief-template-library" / f"{name}.md"
        assert path.stat().st_size > 0, f"{name}.md is empty"
