# ADR-0003: LLM retry and timeout policy

**Status:** Accepted
**Date:** 2026-04-28

## Context

LLM provider calls fail in three distinct shapes: (a) transient infra
glitches (rate limits, 5xx, network blips) that are very likely to succeed
on a retry; (b) fatal misconfiguration (`ProviderNotInstalled`, missing
key) that retries cannot fix; (c) user interrupts (`KeyboardInterrupt`,
`SystemExit`) that the application must propagate immediately. Without a
retry layer, a single 503 ends a multi-stage run that already cost real
money in earlier stages.

## Decision

`agentsuite.llm.retry.RetryingLLMProvider` wraps every `LLMProvider`
returned by `resolve_provider()`. It retries `provider.complete()` on any
exception except `ProviderNotInstalled`, `KeyboardInterrupt`, and
`SystemExit`, with `tenacity.stop_any(stop_after_attempt(N),
stop_after_delay(T))` and `wait_exponential` between attempts. `N` and
`T` come from `AGENTSUITE_LLM_MAX_ATTEMPTS` (default 3) and
`AGENTSUITE_LLM_TIMEOUT_SECS` (default 120.0). The wrapper is
default-on; production code never sees a raw provider unless it
constructs one directly.

## Consequences

- Transient failures cost wall-clock time but do not bleed cost across
  stages — the cost tracker only records on successful `complete()`.
- A poisoned input that always fails will burn `N` attempts + `T` seconds
  before surfacing. Future tightening could add a circuit-breaker for
  consecutive failures across stages.
- `RetryingLLMProvider.name` must be a settable instance variable (not a
  `@property`) to satisfy the `LLMProvider` Protocol that mypy enforces.
  Tests pin this; future refactors must preserve the settable shape.
