# ADR-0007: Resume-from-failure idempotency contract

**Status:** Accepted
**Date:** 2026-04-28

## Context

A multi-stage agent run that crashes mid-stage 4 is expensive: stages 1–3
already paid for LLM tokens. When the operator resumes from `_state.json`,
the kernel must guarantee that earlier successful stages are not re-billed
and that the failed stage restarts from a known-clean point rather than
half-way through a partial output. Without an explicit contract, "resume"
becomes a folklore term and operators can't trust the cost report.

## Decision

The kernel's resume contract is **stage-atomic**: a stage either completes
fully (its artifacts written, `RunState.cost_so_far` updated, `_state.json`
saved, `cost_summary.json` saved) or it does not advance at all. On
resume, the pipeline driver finds the saved `state.stage` in
`PIPELINE_ORDER` and starts from that index, re-running the stage from
the beginning. The cost tracker is a fresh in-memory `CostTracker` for
the resumed run — `per_stage` for completed stages is read from the
prior `cost_summary.json` (when implementing the test, see
`tests/integration/test_resume_idempotency.py`), and the resumed stage's
new cost adds to the carried total. Stages 1–3 are NOT re-charged. The
cap budget reflects total cost across both run attempts.

## Consequences

- Stages must be designed to be safely re-run from scratch. If a stage's
  side effects are non-idempotent (e.g. a third-party POST that creates a
  resource), the stage owns the idempotency token. The kernel does not.
- A failure mid-stage costs whatever LLM calls completed inside that
  stage before the exception. The current `_drive()` writes
  `cost_summary.json` best-effort on exception so the operator sees the
  partial spend. There is no per-call rollback — that would require
  transactional LLM APIs, which providers do not offer.
- **The crashed stage re-bills on resume.** "Stages 1–N not re-charged"
  applies to stages that completed before the crashed stage. The crashed
  stage itself runs from the start on resume, so any LLM calls it made
  before the crash are paid AGAIN. This is the price of stage-atomic
  resume; the alternative (in-stage checkpointing) would require the
  kernel to know each agent's internal sub-step shape, breaking the
  abstraction. The cap budget reflects total spend including the
  re-billed crashed stage.
- The integration test for this ADR lives in
  `tests/integration/test_resume_idempotency.py`. Bumping the schema in
  a way that breaks the test means re-litigating this ADR.
