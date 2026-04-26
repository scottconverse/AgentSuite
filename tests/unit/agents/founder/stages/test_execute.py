"""Unit tests for founder.stages.execute."""
import json
from pathlib import Path

from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.stages.execute import execute_stage
from agentsuite.agents.founder.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import Constraints, RunState


_EXTRACTED = {
    "mission": "ship pfl",
    "audience": {"primary_persona": "independent inventors", "secondary_personas": []},
    "positioning": "patent drafting, local",
    "tone_signals": ["practical", "technical"],
    "visual_signals": ["workshop bench"],
    "recurring_claims": ["runs offline"],
    "recurring_vocabulary": ["draft", "claim"],
    "prohibited_language": ["revolutionize"],
    "gaps": [],
}


def _seed(tmp_path: Path) -> ArtifactWriter:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    writer.write_json("extracted_context.json", _EXTRACTED, kind="data", stage="extract")
    return writer


def _state() -> RunState:
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="ship PatentForgeLocal",
        constraints=Constraints(),
    )
    return RunState(run_id="r1", agent="founder", stage="execute", inputs=inp)


def test_execute_renders_all_eleven_templates(tmp_path):
    writer = _seed(tmp_path)
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={})
    new_state = execute_stage(_state(), ctx)
    assert new_state.stage == "qa"
    for name in TEMPLATE_NAMES:
        assert (writer.run_dir / "brief-template-library" / f"{name}.md").exists()


def test_execute_writes_export_manifest(tmp_path):
    writer = _seed(tmp_path)
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={})
    execute_stage(_state(), ctx)
    manifest_path = writer.run_dir / "export-manifest-template.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "templates" in manifest
    assert len(manifest["templates"]) == 11


def test_execute_substitutes_audience_into_template(tmp_path):
    writer = _seed(tmp_path)
    ctx = StageContext(writer=writer, cost_tracker=CostTracker(), edits={})
    execute_stage(_state(), ctx)
    landing = (writer.run_dir / "brief-template-library" / "landing-hero.md").read_text(encoding="utf-8")
    assert "independent inventors" in landing
    assert "PatentForgeLocal" in landing
