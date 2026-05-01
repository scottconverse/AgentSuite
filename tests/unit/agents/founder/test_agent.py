"""Unit tests for FounderAgent end-to-end (mocked LLM)."""
import json

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.agents.founder.template_loader import TEMPLATE_NAMES
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.mock import MockLLMProvider


_EXTRACT = {
    "mission": "Help inventors draft local patents.",
    "audience": {"primary_persona": "independent inventor", "secondary_personas": []},
    "positioning": "Local patent drafting tool that runs offline.",
    "tone_signals": ["practical", "technical", "no-hype"],
    "visual_signals": ["workshop bench"],
    "recurring_claims": ["runs offline"],
    "recurring_vocabulary": ["draft", "claim"],
    "prohibited_language": ["revolutionize"],
    "gaps": ["no pricing data"],
}


def _all_responses() -> dict[str, str]:
    responses: dict[str, str] = {
        "extracting": json.dumps(_EXTRACT),
        "checking 9 artifacts": json.dumps({"mismatches": []}),
        "scoring 9 founder": json.dumps({
            "scores": {d.name: 8.0 for d in FOUNDER_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
    }
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\n\nReal content."
    return responses


def _request() -> FounderAgentInput:
    return FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="build a brand system for patentforgelocal",
        business_goal="Launch PatentForgeLocal v1",
        project_slug="pfl",
        constraints=Constraints(),
    )


def test_founder_agent_run_to_approval_gate(tmp_path):
    agent = FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    state = agent.run(request=_request(), run_id="r1")
    assert state.stage == "approval"


def test_founder_agent_produces_all_required_artifacts(tmp_path):
    agent = FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    agent.run(request=_request(), run_id="r1")
    run_dir = tmp_path / "runs" / "r1"
    expected_files = [
        "_state.json",
        "inputs_manifest.json",
        "extracted_context.json",
        "consistency_report.json",
        "export-manifest-template.json",
        "qa_report.md",
        "qa_scores.json",
    ] + [f"{s}.md" for s in SPEC_ARTIFACTS]
    for name in expected_files:
        assert (run_dir / name).exists(), f"missing {name}"
    for tmpl in TEMPLATE_NAMES:
        assert (run_dir / "brief-template-library" / f"{tmpl}.md").exists()


def test_founder_agent_approve_promotes_to_kernel(tmp_path):
    agent = FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    agent.run(request=_request(), run_id="r1")
    final = agent.approve(run_id="r1", approver="scott", project_slug="pfl")
    assert final.stage == "done"
    assert (tmp_path / "_kernel" / "pfl" / "brand-system.md").exists()
    assert (tmp_path / "_kernel" / "pfl" / "brief-template-library" / "landing-hero.md").exists()


def test_founder_agent_resume_from_qa(tmp_path):
    agent = FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    agent.run(request=_request(), run_id="r1")
    state = agent.resume(run_id="r1", stage="qa", edits={})
    assert state.stage == "approval"


def test_founder_agent_has_correct_class_attributes(tmp_path):
    """Verify FounderAgent exposes name and qa_rubric."""
    agent = FounderAgent(output_root=tmp_path, llm=MockLLMProvider(responses=_all_responses()))
    assert agent.name == "founder"
    assert agent.qa_rubric is FOUNDER_RUBRIC


# ---------------------------------------------------------------------------
# UX-004 — _stage_to_status maps "approval" → "awaiting_approval"
# ---------------------------------------------------------------------------

def test_stage_to_status_approval_maps_to_awaiting_approval():
    """CLI JSON status: 'approval' stage must emit 'awaiting_approval'."""
    from agentsuite.kernel.base_agent import stage_to_status as _stage_to_status
    assert _stage_to_status("approval") == "awaiting_approval"


def test_stage_to_status_done_passes_through():
    """CLI JSON status: 'done' stage must emit 'done' unchanged."""
    from agentsuite.kernel.base_agent import stage_to_status as _stage_to_status
    assert _stage_to_status("done") == "done"


def test_stage_to_status_other_stages_pass_through():
    """CLI JSON status: intermediate stages pass through unchanged."""
    from agentsuite.kernel.base_agent import stage_to_status as _stage_to_status
    for stage in ("intake", "extract", "spec", "execute", "qa"):
        assert _stage_to_status(stage) == stage


def test_founder_registered_in_global_registry(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_ENABLED_AGENTS", "founder")
    from agentsuite.agents.registry import default_registry

    reg = default_registry()
    cls = reg.get_class("founder")
    assert cls is FounderAgent
