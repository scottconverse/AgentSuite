# ADR-0002: RunState shape and resume contract

**Status:** Accepted
**Date:** 2026-04-28

## Context

Each agent invocation persists a `RunState` to `.agentsuite/runs/<run-id>/_state.json`
so a crashed run can resume from the last completed stage. `RunState.inputs`
is typed as `AgentRequest` (the shared base class). Each agent supplies its
own `*AgentInput` subclass with required fields (e.g. `DesignAgentInput.campaign_goal`).
Through v0.8.x the persisted JSON dropped subclass-specific fields — pydantic's
serializer used the declared base type, not the runtime subclass. Resume
worked envelope-only; subclass fields were silently lost. v0.9.0 makes
serialization subclass-aware and adds a `schema_version` envelope field so
the contract is explicit and testable.

## Decision

`StateStore.save` dumps `inputs` using the runtime instance's schema, not
the declared field type. `StateStore.load` resolves the agent name to its
input subclass via a lazy importlib registry (avoiding circular imports —
the kernel never imports agent packages at import time) and re-validates
the persisted JSON against that subclass. Every saved `_state.json` carries
`schema_version: int` (currently `2`); a missing or older version raises
`RunStateSchemaVersionError` with a message that names the run dir to
delete. No silent migration is shipped — pre-v0.9 has no installed base
to protect, and a one-shot migrator earns its complexity only when it
will be exercised.

## Consequences

- Subclass round-trip is now part of the contract. The parametrised test
  in `tests/unit/kernel/test_state_store.py` verifies all seven agents.
- Bumping `SCHEMA_VERSION` is a deliberate breaking change. The `BREAKING:`
  CHANGELOG line must call it out and the operator's clear guidance is
  "delete the offending run dir and re-run."
- Adding a new agent requires registering its input class path in
  `_INPUTS_BY_AGENT`. Forgetting to do so falls back to base `AgentRequest`
  validation, which loses subclass fields silently — a future hardening
  step would assert at registry-load time that every registered agent has
  an inputs entry.
