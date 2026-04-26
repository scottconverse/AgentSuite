"""Unit tests for founder.stages.extract."""
import json
from pathlib import Path

import pytest

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.extract import extract_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import Constraints, RunState
from agentsuite.llm.mock import MockLLMProvider


_VALID_EXTRACT_JSON = json.dumps({
    "mission": "Help inventors draft local patents.",
    "audience": {"primary_persona": "independent inventor", "secondary_personas": ["solo founders"]},
    "positioning": "Local patent drafting tool that runs offline.",
    "tone_signals": ["practical", "technical", "no-hype"],
    "visual_signals": ["workshop bench"],
    "recurring_claims": ["runs offline"],
    "recurring_vocabulary": ["draft", "claim"],
    "prohibited_language": ["revolutionize"],
    "gaps": ["no pricing data"],
})


def _ctx(tmp_path: Path, llm: MockLLMProvider) -> tuple[StageContext, ArtifactWriter]:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json(
        "inputs_manifest.json",
        {"business_goal": "ship pfl", "current_state": "pre-launch", "sources": []},
        kind="data",
        stage="intake",
    )
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={"llm": llm}), writer


def _state() -> RunState:
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship pfl",
        constraints=Constraints(),
    )
    return RunState(run_id="r1", agent="founder", stage="extract", inputs=inp)


def test_extract_writes_extracted_context_json(tmp_path):
    llm = MockLLMProvider(responses={"extracting": _VALID_EXTRACT_JSON})
    ctx, writer = _ctx(tmp_path, llm)
    new_state = extract_stage(_state(), ctx)
    assert new_state.stage == "spec"
    payload = json.loads((writer.run_dir / "extracted_context.json").read_text(encoding="utf-8"))
    assert payload["mission"].startswith("Help inventors")


def test_extract_records_open_questions_from_gaps(tmp_path):
    llm = MockLLMProvider(responses={"extracting": _VALID_EXTRACT_JSON})
    ctx, writer = _ctx(tmp_path, llm)
    new_state = extract_stage(_state(), ctx)
    assert "no pricing data" in new_state.open_questions


def test_extract_raises_on_invalid_json(tmp_path):
    llm = MockLLMProvider(responses={"extracting": "this is not json"})
    ctx, writer = _ctx(tmp_path, llm)
    with pytest.raises(ValueError, match="extract stage produced invalid JSON"):
        extract_stage(_state(), ctx)


def test_extract_tracks_cost(tmp_path):
    llm = MockLLMProvider(responses={"extracting": _VALID_EXTRACT_JSON})
    ctx, writer = _ctx(tmp_path, llm)
    extract_stage(_state(), ctx)
    assert ctx.cost_tracker.total.input_tokens > 0
