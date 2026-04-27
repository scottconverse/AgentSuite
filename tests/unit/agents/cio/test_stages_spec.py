"""Unit tests for agentsuite.agents.cio.stages.spec."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.stages.spec import (
    SPEC_ARTIFACTS,
    ConsistencyCheckFailed,
    spec_stage,
)
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "technology_pain_points": ["Legacy ERP system causing integration bottlenecks"],
    "strategic_gaps": ["No cloud migration roadmap", "Absent data governance policy"],
    "vendor_landscape": ["Oracle ERP", "Microsoft 365", "AWS (partial)"],
    "digital_maturity_signals": ["Manual approval workflows still dominant"],
    "budget_signals": ["Flat IT budget for FY2026"],
    "open_questions": ["What is the timeline for the cloud-first initiative?"],
}

_CONSISTENCY_OK = json.dumps({
    "checks": [
        {
            "dimension": "strategic_alignment",
            "status": "ok",
            "severity": "ok",
            "detail": "No issues found.",
        }
    ]
})

_CONSISTENCY_CRITICAL = json.dumps({
    "checks": [
        {
            "dimension": "budget_roadmap_alignment",
            "status": "mismatch",
            "severity": "critical",
            "detail": "Budget allocation model contradicts technology roadmap priorities",
        }
    ]
})

_CONSISTENCY_WARNING = json.dumps({
    "checks": [
        {
            "dimension": "vendor_governance",
            "status": "mismatch",
            "severity": "warning",
            "detail": "Vendor portfolio references frameworks not in governance document",
        }
    ]
})


def _seed_run_dir(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _make_state() -> RunState:
    inp = CIOAgentInput(
        agent_name="cio",
        role_domain="cio-ops",
        user_request="develop IT strategy and technology roadmap for our organization",
        organization_name="Acme Corp",
        strategic_priorities="Cloud-first, data-driven decision making, operational efficiency",
        it_maturity_level="Level 2 – Repeatable",
        budget_context="$5M annual IT capex, flat opex",
        digital_initiatives="ERP modernization, cloud migration phase 1",
        regulatory_environment="SOX, HIPAA",
    )
    return RunState(run_id="r1", agent="cio", stage="spec", inputs=inp)


def _spec_responses(consistency_json: str = _CONSISTENCY_OK) -> dict[str, str]:
    responses: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md for a CIO team"] = (
            f"# {stem.replace('-', ' ').title()}\n\nContent here"
        )
    responses["checking 9 CIO artifacts"] = consistency_json
    return responses


def test_spec_writes_all_artifacts(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    for stem in SPEC_ARTIFACTS:
        assert (writer.run_dir / f"{stem}.md").exists(), f"missing {stem}.md"


def test_spec_advances_stage(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.stage == "execute"


def test_spec_artifact_count(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    md_files = list(writer.run_dir.glob("*.md"))
    assert len(md_files) == 9


def test_spec_calls_consistency_check(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    # 9 artifact calls + 1 consistency call = 10
    assert len(llm.calls) == 10
    consistency_call = llm.calls[-1]
    assert "checking 9 CIO artifacts" in consistency_call.system


def test_spec_consistency_failure_raises(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses(consistency_json=_CONSISTENCY_CRITICAL))
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    with pytest.raises(ConsistencyCheckFailed, match="critical"):
        spec_stage(_make_state(), ctx)


def test_spec_primary_artifact_non_empty(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    content = (writer.run_dir / "it-strategy.md").read_text(encoding="utf-8")
    assert len(content) > 0


def test_spec_all_artifact_names_correct(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    expected = {f"{stem}.md" for stem in SPEC_ARTIFACTS}
    written = {f.name for f in writer.run_dir.glob("*.md")}
    assert expected == written
