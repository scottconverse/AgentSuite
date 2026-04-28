# ADR-0005: Cost cap vs. cost telemetry split

**Status:** Accepted
**Date:** 2026-04-28

## Context

The kernel's `CostTracker` enforces a hard kill cap (`AGENTSUITE_COST_CAP_USD`,
default $5.00) that aborts a run once accumulated LLM spend exceeds it.
The cap is necessary — without it, a runaway prompt or a misconfigured
loop can spend orders of magnitude more than the operator intended. But
the cap on its own is opaque: the operator only learns "cap exceeded"
after the fact, never "what did this stage cost?" before approving.
Telemetry (per-stage breakdown, model name, total cost) is a different
concern from enforcement (cap kill).

## Decision

The cap stays minimal and load-bearing: a single hard-kill threshold and
a soft-warn flag. Telemetry is layered on top as a separate concern:
`CostTracker` accumulates `per_stage: dict[Stage, Cost]` when the
pipeline driver sets `current_stage` before each handler call, and
writes a `cost_summary.json` to the run directory after every successful
stage (and best-effort on failure). The summary names the run, agent,
provider, model, per-stage tokens + dollars, total, cap, and remaining
budget. Operators see the cost before they approve. The cap and the
summary stay independently tunable.

## Consequences

- `cost_summary.json` is a stable contract — its schema is documented in
  `CostTracker.summary()` and pinned by `test_summary_schema_keys`.
  Bumping the schema in a way consumers can't ignore needs an ADR.
- The cap default is intentionally generous ($5) so first-time users
  don't trip it on a normal Founder run. Operators with tighter budgets
  set `AGENTSUITE_COST_CAP_USD` to something lower.
- Per-day caps, per-month caps, or provider-specific caps are explicitly
  out of scope at v1.0 — operators handle those externally. Re-open
  this ADR if there's evidence the per-run cap is insufficient.
