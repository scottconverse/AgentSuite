# ADR-0001: Rubric dimension count and selection

**Status:** Accepted
**Date:** 2026-04-28

## Context

AgentSuite's QA stage scores each agent's output against a fixed rubric of
quality dimensions. Early in development the rubrics drifted: the Founder
agent shipped with 7 dimensions, the other six agents with 9. An external
audit flagged the asymmetry and proposed expanding Founder to 9 for
uniformity. Closer inspection (see the `feedback_audit_*` notes from
2026-04-28) showed Founder's 7 dimensions already covered the same signal
as the other agents' 9 — the additional two on the longer list were
semantic duplicates of dimensions already on Founder's list under
different names. Symmetry alone is aesthetic; it isn't worth the risk
of rewording prompts and breaking golden tests.

## Decision

Each agent's rubric stays at the dimension count that produces a useful,
non-redundant signal for that agent's domain. Adding or removing a dimension
requires evidence (low-correlation with existing dimensions, real change in
score distribution on a representative run) — not symmetry.

> **2026-04-28 update:** Founder was subsequently expanded to 9 dimensions
> (commit `2b1dda0` added `constraint_adherence` and `completeness`), bringing
> all seven agents to 9 each. The decision stands — the count was driven by
> per-agent signal, not by symmetry. The supporting cross-reference audit is
> at [`docs/rubric-audit.md`](../rubric-audit.md), which confirms each
> dimension on every rubric carries unique domain signal.

## Consequences

- Rubric counts are not standardized across agents. Documentation and
  golden-test fixtures must keep per-agent rubrics in lockstep with code.
- Future audits should not flag the asymmetry as a defect. Instead, they
  should look at each rubric's signal-per-dimension correlation.
- A single QA-result schema is harder to define generically; the kernel
  treats `qa_scores.json` as agent-typed (the agent's rubric class is the
  authority on dimension names and weights).
