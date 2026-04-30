"""Unit tests for agentsuite.agents.design.stages.spec."""
from __future__ import annotations

import json
from pathlib import Path

from agentsuite.agents.design.input_schema import DesignAgentInput
from agentsuite.agents.design.stages.spec import (
    SPEC_ARTIFACTS,
    spec_stage,
)
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState
from agentsuite.llm.mock import MockLLMProvider


_EXTRACTED = {
    "audience_profile": {"primary_persona": "senior designer"},
    "brand_voice": {"tone_words": ["confident"], "writing_style": "terse", "forbidden_tones": []},
    "visual_signals": ["bold typography"],
    "typography_signals": {"heading_style": "sans-serif"},
    "color_palette_observed": [],
    "craft_anti_patterns": [],
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
        user_request="campaign",
        target_audience="developers",
        campaign_goal="drive signups",
        channel="web",
    )
    return RunState(run_id="r1", agent="design", stage="spec", inputs=inp)


def _spec_responses() -> dict[str, str]:
    responses: dict[str, str] = {}
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\n\nSpec content."
    responses["checking 9 artifacts"] = json.dumps({"mismatches": []})
    return responses


def test_spec_writes_all_nine_artifacts(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.stage == "execute"
    for stem in SPEC_ARTIFACTS:
        assert (writer.run_dir / f"{stem}.md").exists()


def test_spec_writes_consistency_report(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    report_path = writer.run_dir / "consistency_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "mismatches" in report


def test_spec_raises_on_critical_mismatch(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    critical_response = json.dumps({
        "mismatches": [{
            "field": "color",
            "files": ["visual-direction.md", "design-brief.md"],
            "details": "color values conflict",
            "severity": "critical",
        }]
    })
    responses = _spec_responses()
    responses["checking 9 artifacts"] = critical_response
    llm = MockLLMProvider(responses=responses)
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.requires_revision is True
    assert new_state.stage == "execute"


def test_spec_warning_mismatch_does_not_raise(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    warning_response = json.dumps({
        "mismatches": [{
            "field": "typography",
            "files": ["design-brief.md"],
            "details": "minor weight inconsistency",
            "severity": "warning",
        }]
    })
    responses = _spec_responses()
    responses["checking 9 artifacts"] = warning_response
    llm = MockLLMProvider(responses=responses)
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    new_state = spec_stage(_make_state(), ctx)
    assert new_state.stage == "execute"


def test_spec_tracks_cost(tmp_path: Path) -> None:
    writer = _seed_run_dir(tmp_path)
    llm = MockLLMProvider(responses=_spec_responses())
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm})
    spec_stage(_make_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens > 0


def test_spec_nine_artifact_count() -> None:
    assert len(SPEC_ARTIFACTS) == 9
