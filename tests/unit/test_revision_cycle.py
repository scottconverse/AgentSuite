"""TEST-004: Revision cycle integration test.

Exercises the full revision loop:
  1. Run the Founder agent pipeline with a mock LLM that returns failing QA scores.
  2. Verify that attempting to approve raises RevisionRequired.
  3. Resume from the QA stage with passing QA scores (same SequentialMockLLMProvider).
  4. Verify that approving returns a completed ApprovalResult.
  5. Verify that cost accounting accumulates across both pipeline legs.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
from agentsuite.kernel.approval import RevisionRequired
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.mock import SequentialMockLLMProvider


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

_ALL_FOUNDER_DIMS = [d.name for d in FOUNDER_RUBRIC.dimensions]

_FAILING_QA_RESPONSE = json.dumps({
    "scores": {d: 5.0 for d in _ALL_FOUNDER_DIMS},
    "revision_instructions": ["Strengthen brand voice consistency across all artifacts."],
})

_PASSING_QA_RESPONSE = json.dumps({
    "scores": {d: 8.5 for d in _ALL_FOUNDER_DIMS},
    "revision_instructions": [],
})


def _build_sequences() -> dict[str, list[str]]:
    """Build the SequentialMockLLMProvider sequences for a two-leg revision cycle.

    All structural calls (extract, consistency check, spec artifacts, etc.) use
    static single-item sequences (repeat indefinitely).  Only the QA scoring key
    carries two entries: failing first, then passing.
    """
    import json as _json

    extracted = {
        "mission": "Build the best tool",
        "audience": {"primary_persona": "developers", "secondary_personas": []},
        "positioning": "developer-first",
        "tone_signals": ["practical"],
        "visual_signals": [],
        "recurring_claims": [],
        "recurring_vocabulary": [],
        "prohibited_language": [],
        "gaps": [],
    }

    sequences: dict[str, list[str]] = {
        # Extract stage
        "extracting": [_json.dumps(extracted)],
        # Consistency check stage
        "checking 9 artifacts": [_json.dumps({"mismatches": []})],
        # QA scoring — failing first, passing second
        # Key must match system_msg fragment "scoring 9 founder" (longest-match-first).
        "You are scoring 9 founder-agent artifacts. Return ONLY JSON.": [
            _FAILING_QA_RESPONSE,
            _PASSING_QA_RESPONSE,
        ],
    }

    # Add spec artifact generation — all static
    for stem in SPEC_ARTIFACTS:
        key = f"writing {stem}.md"
        sequences[key] = [f"# {stem}\n\nRevision cycle mock content."]

    return sequences


def _build_agent(tmp_path: Path, sequences: dict[str, list[str]]) -> FounderAgent:
    llm = SequentialMockLLMProvider(sequences=sequences)
    return FounderAgent(output_root=tmp_path, llm=llm)


def _founder_input() -> FounderAgentInput:
    return FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="run founder pipeline for revision-cycle test",
        business_goal="Launch test product v1",
        project_slug="test-proj",
        constraints=Constraints(),
    )


# ---------------------------------------------------------------------------
# Test 1: First pass — QA fails → RevisionRequired raised on approve
# ---------------------------------------------------------------------------

def test_revision_cycle_first_pass_qa_fails(tmp_path: Path) -> None:
    """First pass through the pipeline must produce requires_revision=True."""
    sequences = _build_sequences()
    agent = _build_agent(tmp_path, sequences)

    state = agent.run(request=_founder_input(), run_id="rev-cycle-r1")

    assert state.stage == "approval", f"Expected 'approval', got {state.stage!r}"
    assert state.requires_revision is True, (
        "First QA pass used failing scores — requires_revision must be True"
    )


def test_revision_cycle_approve_raises_revision_required_on_first_pass(tmp_path: Path) -> None:
    """Calling approve() after a failing QA pass must raise RevisionRequired."""
    sequences = _build_sequences()
    agent = _build_agent(tmp_path, sequences)

    agent.run(request=_founder_input(), run_id="rev-cycle-r2")

    with pytest.raises(RevisionRequired):
        agent.approve(run_id="rev-cycle-r2", approver="scott", project_slug="test-proj")


# ---------------------------------------------------------------------------
# Test 2: Second pass — QA passes → approve returns done RunState
# ---------------------------------------------------------------------------

def test_revision_cycle_second_pass_qa_passes(tmp_path: Path) -> None:
    """Resuming from QA stage after a revision must produce requires_revision=False."""
    sequences = _build_sequences()
    agent = _build_agent(tmp_path, sequences)

    # Leg 1: failing QA
    agent.run(request=_founder_input(), run_id="rev-cycle-r3")

    # Leg 2: resume from QA stage — now the sequential provider returns passing scores
    state2 = agent.resume(run_id="rev-cycle-r3", stage="qa", edits={})

    assert state2.stage == "approval"
    assert state2.requires_revision is False, (
        "Second QA pass used passing scores — requires_revision must be False"
    )


def test_revision_cycle_approve_succeeds_after_passing_qa(tmp_path: Path) -> None:
    """Calling approve() after passing QA must return a RunState with stage='done'."""
    sequences = _build_sequences()
    agent = _build_agent(tmp_path, sequences)

    agent.run(request=_founder_input(), run_id="rev-cycle-r4")
    agent.resume(run_id="rev-cycle-r4", stage="qa", edits={})
    final_state = agent.approve(
        run_id="rev-cycle-r4", approver="scott", project_slug="test-proj"
    )

    assert final_state.stage == "done"
    assert final_state.approved_by == "scott"
    assert final_state.approved_at is not None


# ---------------------------------------------------------------------------
# Test 3: Cost accounting covers both legs
# ---------------------------------------------------------------------------

def test_revision_cycle_cost_accumulates_across_both_legs(tmp_path: Path) -> None:
    """cost_so_far in the final state must reflect LLM calls from BOTH pipeline legs.

    The mock provider returns usd=0.0 for every call, but input/output token counts
    are > 0 based on prompt/response word counts.  After two full QA runs (intake +
    extract + spec + execute + qa × 2) the aggregate token counts must be strictly
    greater than after a single-leg run.
    """
    run_id_one_leg = "cost-one-leg"
    run_id_two_legs = "cost-two-legs"

    # One-leg run (single QA pass, but sequences exhaust to repeating the last item,
    # so we need a provider that fails first, passes second for two-leg)
    seq_one = _build_sequences()
    # Force the one-leg run to use passing QA immediately (to reach approval)
    seq_one["You are scoring 9 founder-agent artifacts. Return ONLY JSON."] = [_PASSING_QA_RESPONSE]
    agent_one = FounderAgent(
        output_root=tmp_path / "one",
        llm=SequentialMockLLMProvider(sequences=seq_one),
    )
    state_one = agent_one.run(request=_founder_input(), run_id=run_id_one_leg)
    one_leg_tokens = state_one.cost_so_far.input_tokens + state_one.cost_so_far.output_tokens

    # Two-leg run (QA fails first, passes on resume)
    seq_two = _build_sequences()
    agent_two = FounderAgent(
        output_root=tmp_path / "two",
        llm=SequentialMockLLMProvider(sequences=seq_two),
    )
    agent_two.run(request=_founder_input(), run_id=run_id_two_legs)
    state_two = agent_two.resume(run_id=run_id_two_legs, stage="qa", edits={})
    two_leg_tokens = state_two.cost_so_far.input_tokens + state_two.cost_so_far.output_tokens

    assert two_leg_tokens > one_leg_tokens, (
        f"Two-leg cost ({two_leg_tokens} tokens) must exceed one-leg cost ({one_leg_tokens} tokens). "
        "Cost accumulation across revision cycles appears broken."
    )


def test_revision_cycle_qa_report_written_on_both_passes(tmp_path: Path) -> None:
    """qa_report.md must be written to the run directory on both QA passes."""
    sequences = _build_sequences()
    agent = _build_agent(tmp_path, sequences)

    agent.run(request=_founder_input(), run_id="rev-cycle-qa-report")
    run_dir = tmp_path / "runs" / "rev-cycle-qa-report"
    assert (run_dir / "qa_report.md").exists(), "qa_report.md must exist after first QA pass"
    assert (run_dir / "qa_scores.json").exists(), "qa_scores.json must exist after first QA pass"

    # Verify the first-pass scores are failing
    scores = json.loads((run_dir / "qa_scores.json").read_text())
    assert scores["passed"] is False, "First QA pass scores must produce passed=False"

    # Resume for second pass
    agent.resume(run_id="rev-cycle-qa-report", stage="qa", edits={})
    scores2 = json.loads((run_dir / "qa_scores.json").read_text())
    assert scores2["passed"] is True, "Second QA pass scores must produce passed=True"


def test_revision_cycle_artifacts_promoted_after_approval(tmp_path: Path) -> None:
    """Primary brand-system.md must be promoted to _kernel/ after a successful approve."""
    sequences = _build_sequences()
    agent = _build_agent(tmp_path, sequences)

    agent.run(request=_founder_input(), run_id="rev-cycle-promote")
    agent.resume(run_id="rev-cycle-promote", stage="qa", edits={})
    agent.approve(run_id="rev-cycle-promote", approver="scott", project_slug="test-proj")

    kernel_brand = tmp_path / "_kernel" / "test-proj" / "brand-system.md"
    assert kernel_brand.exists(), f"brand-system.md must be promoted to {kernel_brand}"
