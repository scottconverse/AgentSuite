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


# --- v0.9.0: as_of_date reproducibility ---------------------------------


def _state_with_as_of(as_of_date) -> RunState:
    inp = CIOAgentInput(
        agent_name="cio",
        role_domain="cio-ops",
        user_request="Strategy for Acme",
        organization_name="Acme Corp",
        strategic_priorities="Cloud\nSecurity\nData",
        it_maturity_level="Level 2",
        digital_initiatives="ERP Cloud\nCDP",
        as_of_date=as_of_date,
    )
    return RunState(run_id="r-asof", agent="cio", stage="execute", inputs=inp)


def test_execute_as_of_date_drives_quarter_in_artifacts(tmp_path: Path) -> None:
    """Two runs with different as_of_date produce different quarter strings.

    Q1 2026 run: rendered briefing references "Q1 2026".
    Q4 2026 run: rendered briefing references "Q4 2026".
    Same input set otherwise — the only differing input is as_of_date.
    """
    from datetime import date as _date

    # Run A: Feb 2026 → Q1 2026, FY2026
    writer_a = _seed_run_dir(tmp_path / "a")
    execute_stage(_state_with_as_of(_date(2026, 2, 14)), _make_ctx(writer_a))
    briefing_a = (writer_a.run_dir / "brief-template-library" / "board-technology-briefing.md").read_text(encoding="utf-8")
    assert "Q1 2026" in briefing_a
    assert "FY2026" in briefing_a

    # Run B: Nov 2026 → Q4 2026, FY2026
    writer_b = _seed_run_dir(tmp_path / "b")
    execute_stage(_state_with_as_of(_date(2026, 11, 14)), _make_ctx(writer_b))
    briefing_b = (writer_b.run_dir / "brief-template-library" / "board-technology-briefing.md").read_text(encoding="utf-8")
    assert "Q4 2026" in briefing_b
    assert "FY2026" in briefing_b

    # Different as_of_date → different artifact content.
    assert briefing_a != briefing_b


def test_execute_as_of_date_none_uses_today_utc(tmp_path: Path) -> None:
    """When as_of_date is None, briefing artifacts reflect today's UTC quarter+year."""
    from datetime import datetime as _datetime, timezone as _tz

    writer = _seed_run_dir(tmp_path)
    execute_stage(_state_with_as_of(None), _make_ctx(writer))
    briefing = (writer.run_dir / "brief-template-library" / "board-technology-briefing.md").read_text(encoding="utf-8")
    today = _datetime.now(tz=_tz.utc).date()
    expected_q = (today.month - 1) // 3 + 1
    assert f"Q{expected_q} {today.year}" in briefing
    assert f"FY{today.year}" in briefing


def test_next_quarter_wraps_at_year_boundary() -> None:
    """Q4 → next_quarter rolls forward to Q1 of next year."""
    from datetime import date as _date

    from agentsuite.agents.cio.stages.execute import _next_quarter

    assert _next_quarter(_date(2026, 12, 1)) == "Q1 2027"
    assert _next_quarter(_date(2026, 9, 30)) == "Q4 2026"
    assert _next_quarter(_date(2026, 1, 15)) == "Q2 2026"


def test_resolve_as_of_honors_input_field() -> None:
    """_resolve_as_of returns inp.as_of_date when set, else today UTC."""
    from datetime import date as _date, datetime as _datetime, timezone as _tz

    from agentsuite.agents.cio.stages.execute import _resolve_as_of

    inp_set = CIOAgentInput(
        agent_name="cio", role_domain="cio-ops", user_request="x",
        organization_name="Acme", strategic_priorities="A", it_maturity_level="L1",
        as_of_date=_date(2030, 6, 15),
    )
    assert _resolve_as_of(inp_set) == _date(2030, 6, 15)

    inp_unset = CIOAgentInput(
        agent_name="cio", role_domain="cio-ops", user_request="x",
        organization_name="Acme", strategic_priorities="A", it_maturity_level="L1",
    )
    today = _datetime.now(tz=_tz.utc).date()
    assert _resolve_as_of(inp_unset) == today
