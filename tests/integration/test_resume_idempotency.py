"""Resume-from-failure idempotency contract — ADR-0007.

A multi-stage agent run that crashes mid-stage 4 must, on resume:

* Not re-bill stages 1–3 (the operator already paid for those tokens; the
  pipeline driver starts at the failed stage's index in PIPELINE_ORDER).
* Carry forward ``state.cost_so_far`` so cap enforcement reflects total
  multi-attempt spend, not just the resumed segment.
* Restore the per-stage breakdown from the prior ``cost_summary.json`` so
  the final report shows the full history.

The contract is documented in ``docs/adr/0007-resume-idempotency.md``;
this test pins it.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.base import LLMRequest, LLMResponse
from agentsuite.llm.mock import MockLLMProvider, _default_mock_for_cli


class _BillableThenCrashThenSucceed(MockLLMProvider):
    """Mock that bills nonzero cost AND fails the Nth call exactly once.

    Wraps the standard CLI mock's responses so canned outputs still match
    real agent prompts. Adds:

    * ``usd_per_call``: every successful response includes this dollar
      amount (default $0.05) so cost accumulation across stages is
      observable in tests.
    * ``crash_at_call``: 1-indexed; on this call the mock raises
      ``RuntimeError`` once. The flag is consumed — subsequent calls
      succeed normally, simulating a transient failure that resume
      should recover from.
    """

    name = "billable-mock"

    def __init__(self, *, usd_per_call: float = 0.05, crash_at_call: int) -> None:
        # Reuse the canned responses from the default CLI mock.
        delegate = _default_mock_for_cli(provider_name="billable-mock")
        super().__init__(
            responses=delegate.responses,
            default_model=delegate.default_model(),
            name="billable-mock",
        )
        self.usd_per_call = usd_per_call
        self._crash_at = crash_at_call
        self._crashed = False

    def complete(self, request: LLMRequest) -> LLMResponse:
        # Track the call BEFORE deciding whether to crash so the count is
        # consistent across the crash + resume seams.
        self.calls.append(request)
        call_index = len(self.calls)
        if not self._crashed and call_index == self._crash_at:
            self._crashed = True
            raise RuntimeError(
                f"Simulated transient provider failure on call #{call_index}"
            )
        # Reuse the parent's response selection logic by walking responses
        # directly (parent's complete() would re-append to self.calls).
        for keyword, text in self.responses.items():
            if keyword in request.prompt or keyword in request.system:
                return LLMResponse(
                    text=text,
                    model=request.model or self.default_model(),
                    input_tokens=max(len(request.prompt.split()), 1),
                    output_tokens=max(len(text.split()), 1),
                    usd=self.usd_per_call,
                )
        raise RuntimeError(
            f"No mock response for prompt: {request.prompt[:80]!r}"
        )


def _founder_input() -> FounderAgentInput:
    return FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="Build creative ops",
        business_goal="Launch v1",
        project_slug="resume-idem",
        constraints=Constraints(),
    )


def test_resume_preserves_prior_stage_costs(tmp_path: Path) -> None:
    """Crash on call N, resume, assert prior-stage costs survive.

    The first attempt's cost_summary.json captures stages that completed
    before the crash. After resume, those stages must still appear in the
    final cost_summary.json with their original costs (i.e. they were not
    re-charged) and the final ``state.cost_so_far`` must equal the sum
    across attempts.
    """
    # Crash partway through the run. The mock crashes on call #5; for the
    # mock-only Founder pipeline that lands inside the spec/execute window,
    # which is exactly where ADR-0007 cares about idempotency.
    crashing_mock = _BillableThenCrashThenSucceed(usd_per_call=0.10, crash_at_call=5)
    agent = FounderAgent(output_root=tmp_path, llm=crashing_mock)
    inp = _founder_input()

    # First run: must crash with the simulated transient.
    with pytest.raises(RuntimeError, match="Simulated transient"):
        agent.run(request=inp, run_id="resume-r1")

    # Persisted state shows where we crashed.
    run_dir = tmp_path / "runs" / "resume-r1"
    state_path = run_dir / "_state.json"
    summary_path = run_dir / "cost_summary.json"
    assert state_path.exists(), "Crashed run must have persisted _state.json"
    assert summary_path.exists(), (
        "Best-effort cost_summary.json must persist on failure (ADR-0005, ADR-0007)"
    )

    state_after_crash = json.loads(state_path.read_text(encoding="utf-8"))
    summary_after_crash = json.loads(summary_path.read_text(encoding="utf-8"))
    crash_total_usd = state_after_crash["cost_so_far"]["usd"]
    crash_stage = state_after_crash["stage"]  # the stage that was running when the crash hit
    assert crash_total_usd > 0, "Stages before the crash must have billed"
    completed_stage_costs_before = {
        row["stage"]: row["cost_usd"] for row in summary_after_crash["stages"]
    }
    # ADR-0007 stage-atomic contract: stages BEFORE the crashed stage must
    # not re-bill on resume. The crashed stage itself legitimately re-runs
    # from a clean start, so its cost may differ between attempts.
    stages_that_must_not_rebill = {
        s for s in completed_stage_costs_before if s != crash_stage
    }
    completed_stages_before_crash = set(completed_stage_costs_before.keys())

    # Resume with a fresh mock (no crash this time). The agent picks up
    # from state.stage and runs to completion.
    resume_mock = _BillableThenCrashThenSucceed(
        usd_per_call=0.10,
        crash_at_call=10**9,  # effectively never
    )
    agent_resume = FounderAgent(output_root=tmp_path, llm=resume_mock)
    final_state = agent_resume.run(request=inp, run_id="resume-r1")
    assert final_state.stage == "approval", "Resume must complete the pipeline"

    # Final cost_summary.json should include the prior stages with their
    # original per-stage costs (no double-billing of stages BEFORE the
    # crashed stage) PLUS any stages that ran after resume.
    final_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    final_stage_costs = {row["stage"]: row["cost_usd"] for row in final_summary["stages"]}
    for stage_name in stages_that_must_not_rebill:
        assert stage_name in final_stage_costs, (
            f"Prior-attempt stage {stage_name} must remain in final summary"
        )
        prior_cost = completed_stage_costs_before[stage_name]
        assert final_stage_costs[stage_name] == pytest.approx(prior_cost), (
            f"Stage {stage_name} was re-billed across resume "
            f"(was {prior_cost}, now {final_stage_costs[stage_name]})"
        )
    # The crashed stage itself is allowed to re-bill on resume per ADR-0007.

    # The carried-forward total must include the prior-attempt cost.
    final_total = final_state.cost_so_far.usd
    assert final_total >= crash_total_usd, (
        "Final total must include carried-forward cost from prior attempt"
    )
    assert final_summary["total_cost_usd"] == pytest.approx(final_total), (
        "cost_summary total_cost_usd must match final state.cost_so_far"
    )

    # Sanity: no stage in completed_stages_before_crash was lost.
    final_stages = set(final_stage_costs.keys())
    assert completed_stages_before_crash.issubset(final_stages), (
        f"Lost stages on resume: "
        f"{completed_stages_before_crash - final_stages}"
    )
