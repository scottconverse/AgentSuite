"""Unit tests for founder.stages.intake."""
import json
from pathlib import Path

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.intake import intake_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import Constraints, RunState


def _ctx(tmp_path: Path) -> tuple[StageContext, ArtifactWriter]:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits={}), writer


def _state(inp: FounderAgentInput) -> RunState:
    return RunState(run_id="r1", agent="founder", inputs=inp)


def test_intake_writes_inputs_manifest(tmp_path):
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship pfl",
        constraints=Constraints(),
    )
    ctx, writer = _ctx(tmp_path)
    new_state = intake_stage(_state(inp), ctx)
    assert new_state.stage == "extract"
    manifest = json.loads((writer.run_dir / "inputs_manifest.json").read_text(encoding="utf-8"))
    assert "sources" in manifest
    assert manifest["business_goal"] == "ship pfl"


def test_intake_indexes_files_in_inputs_dir(tmp_path):
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "README.md").write_text("# Readme content", encoding="utf-8")
    (inputs_dir / "voice.txt").write_text("sample voice", encoding="utf-8")
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship",
        inputs_dir=inputs_dir,
        constraints=Constraints(),
    )
    ctx, writer = _ctx(tmp_path)
    intake_stage(_state(inp), ctx)
    manifest = json.loads((writer.run_dir / "inputs_manifest.json").read_text(encoding="utf-8"))
    paths = [s["path"] for s in manifest["sources"]]
    assert any("README.md" in p for p in paths)
    assert any("voice.txt" in p for p in paths)


def test_intake_classifies_voice_samples_explicitly(tmp_path):
    sample = tmp_path / "founder.txt"
    sample.write_text("voice sample", encoding="utf-8")
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship",
        founder_voice_samples=[sample],
        constraints=Constraints(),
    )
    ctx, writer = _ctx(tmp_path)
    intake_stage(_state(inp), ctx)
    manifest = json.loads((writer.run_dir / "inputs_manifest.json").read_text(encoding="utf-8"))
    voice = [s for s in manifest["sources"] if s["kind"] == "voice-sample"]
    assert len(voice) == 1


def test_intake_records_repo_and_web_urls(tmp_path):
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship",
        repo_urls=["https://github.com/scottconverse/PatentForgeLocal"],
        web_urls=["https://patentforgelocal.example.com"],
        constraints=Constraints(),
    )
    ctx, writer = _ctx(tmp_path)
    intake_stage(_state(inp), ctx)
    manifest = json.loads((writer.run_dir / "inputs_manifest.json").read_text(encoding="utf-8"))
    repo_sources = [s for s in manifest["sources"] if s["kind"] == "repo"]
    web_sources = [s for s in manifest["sources"] if s["kind"] == "other"]
    assert len(repo_sources) == 1
    assert len(web_sources) == 1
