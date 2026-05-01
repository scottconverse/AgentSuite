# AgentSuite v1.0.5 — Next-Sprint Watchlist

**Project:** AgentSuite v1.0.5
**Audit date:** 2026-04-30
**Prepared by:** Five-role audit team (Principal Engineer, UX Designer, QA Engineer, Test Engineer, Technical Writer)

---

## Purpose

This document captures structural debt, design decisions, test-culture gaps, and scaling concerns deferred from the v1.0.5 sprint. These are not emergency fixes — they are the investments that prevent the next sprint's emergencies. Nothing here is urgent today; all of it becomes urgent if ignored.

Items are sequenced by priority. Efforts are relative: S = half-day or less, M = 1–2 days, L = 3+ days.

---

## Summary Table

| ID | Priority | Effort | Owner | Title |
|----|----------|--------|-------|-------|
| ENG-003 | **High** | L | Principal Engineer | Eliminate 7× stage-handler duplication |
| TEST-002 | **High** | S | Test Engineer | SequentialMockLLMProvider has zero test coverage |
| TEST-003 | **High** | M | Test Engineer | 4 of 7 agents missing mcp_tools unit tests |
| TEST-004 | **High** | M | Test Engineer | Revision cycle end-to-end never tested |
| ENG-002 | **High** | M | Principal Engineer | AGENTSUITE_LLM_PROVIDER_FACTORY allows arbitrary code execution |
| QA-004 | Medium | S | QA Engineer | Gemini cost model uses request model name, not API-returned model name |
| QA-003 | Medium | S | QA Engineer + Principal Engineer | AGENTSUITE_COST_CAP_USD non-float input raises raw ValueError |
| UX-003 + UX-004 | Medium | S–M | UX Designer + Principal Engineer | CLI progress output uses raw internal stage names |
| ARCH-001 | Medium | L | Principal Engineer | Plan for shared-base-class agent contract before agent count grows |
| DOCS-PROCESS | Medium | S | Technical Writer | Add version-sync check to release process |
| UX-006 | Low | S | UX Designer | project_slug silently ignored in list_runs |
| TEST-005 | Low | S | Test Engineer | VCR cassette infrastructure is dead code |

---

## Expanded Entries

---

### ENG-003 — Eliminate 7× stage-handler duplication

**Priority:** High | **Effort:** L | **Owner:** Principal Engineer

**Description**

The `spec`, `qa`, `consistency_check`, and `approval` stage handlers are copy-pasted across all 7 agents with near-identical logic. This produces a 7× maintenance surface: a bug fix or behavior change must be applied 7 times and tested 7 times. The v1.0.5 sprint already paid this price — the score coercion fix required patching 7 files and re-verifying each one independently.

**Forward plan**

Extract shared base classes or mixins for each stage type. Each agent's stage module becomes a thin subclass that overrides only its prompt and rubric specifics. Estimate: 2–3 days of careful refactoring. The full golden-output suite and the 87-test stress suite must be run after each extraction step to catch behavioral drift early. Do not extract all four stage types in a single pass — one stage type per PR, verified before the next begins.

**Risk if deferred**

Every bug in shared logic multiplies by 7. Every new agent added before this refactor deepens the debt. If the suite grows to 15 agents before ENG-003 is addressed, the refactor cost triples.

---

### TEST-002 — SequentialMockLLMProvider has zero test coverage

**Priority:** High | **Effort:** S | **Owner:** Test Engineer

**Description**

`SequentialMockLLMProvider` was shipped in `agentsuite/llm/mock.py` in v1.0.5 but has no tests of its own. It is the foundation of the entire stress test suite. If its cycling, exhaustion, or reset behavior is subtly wrong, all 87 stress tests are testing against a broken oracle.

**Forward plan**

Write unit tests covering: response cycling (verify responses cycle in order), exhaustion behavior (verify behavior when all responses are consumed), reset behavior (verify `reset()` restores the cycle), and edge cases (empty response list, single-item list). Small effort, high leverage. This work unlocks full trust in the stress suite.

---

### TEST-003 — 4 of 7 agents missing mcp_tools unit tests

**Priority:** High | **Effort:** M | **Owner:** Test Engineer

**Description**

The `engineering`, `marketing`, `trust_risk`, and `cio` agents have no unit tests for their `mcp_tools.py` modules. These modules are the primary integration surface for the MCP server — the path through which callers interact with each agent. The path traversal bug caught in the v1.0.5 audit (ENG-001) would have been caught by unit tests.

**Forward plan**

Add one test module per agent following the pattern of the existing mcp_tools tests in the `product` and `design` agents. Each test module should cover: the happy path for each tool function, missing `run_dir`, invalid `artifact_name`, and any agent-specific edge cases. Aim for full statement coverage of each `mcp_tools.py`.

---

### TEST-004 — Revision cycle end-to-end never tested

**Priority:** High | **Effort:** M | **Owner:** Test Engineer

**Description**

The `approval → RevisionRequired → re-run` path is completely untested. No test in the suite exercises the multi-turn revision loop. This is a core product feature — agents improve output through revision — and it has zero automated coverage.

**Forward plan**

Add an integration test that runs a full pipeline using a `SequentialMockLLMProvider` configured to return a score below the approval threshold on the first pass, trigger a revision, and return a passing score on the second pass. Verify that: (1) the revision was triggered, (2) the final artifact reflects the revised content, and (3) `cost_summary.json` accounts for both passes. This is the most important missing integration test in the suite.

---

### ENG-002 — AGENTSUITE_LLM_PROVIDER_FACTORY allows arbitrary code execution

**Priority:** High | **Effort:** M | **Owner:** Principal Engineer

**Description**

The `AGENTSUITE_LLM_PROVIDER_FACTORY` environment variable is evaluated or dynamically imported without restriction. This is an arbitrary code execution vector in any multi-tenant or shared-environment deployment where untrusted input can influence environment variables.

**Forward plan**

Replace dynamic evaluation with an explicit whitelist of known provider classes, keyed by string identifier. The environment variable should accept exactly one of: `anthropic`, `openai`, `gemini`, `ollama`, `mock`. Any other value should raise a `ConfigurationError` with a clear message listing the accepted values.

**Risk if deferred**

Acceptable for local single-user deployments today. Unacceptable if AgentSuite is ever deployed as a shared service, used in CI pipelines with externally supplied environment variables, or wrapped in a multi-tenant API layer.

---

### QA-004 — Gemini cost model uses request model name, not API-returned model name

**Priority:** Medium | **Effort:** S | **Owner:** QA Engineer

**Description**

For Gemini API calls, `cost_summary.json` records the model name from the request parameters, not the model name returned in the API response. If the Gemini API substitutes a different model version than requested — a known behavior with some Gemini model aliases — costs are attributed to the wrong model, making cost tracking unreliable.

**Forward plan**

Update the Gemini provider to capture the model name from the API response object when available. Compare it against the request name and log a warning if they differ. This is a small targeted change with meaningful impact on cost reporting accuracy.

---

### QA-003 — AGENTSUITE_COST_CAP_USD non-float input raises raw ValueError

**Priority:** Medium | **Effort:** S | **Owner:** QA Engineer + Principal Engineer

**Description**

If `AGENTSUITE_COST_CAP_USD` is set to a non-numeric string — for example `"$5.00"` (a natural user mistake when typing a dollar amount) or `"five"` — the type cast fails with a raw `ValueError` stack trace. There is no user-facing guidance on what went wrong or how to fix it.

**Forward plan**

Add validation in the config loading path. Parse and validate the value before use. On failure, raise `ConfigurationError("AGENTSUITE_COST_CAP_USD must be a numeric value, e.g. '5.00'; got: '<invalid_value>'")` including the actual invalid value in the message. This follows the actionable-error-message standard applied to other config validations in v1.0.5.

---

### UX-003 + UX-004 — CLI progress output uses raw internal stage names

**Priority:** Medium | **Effort:** S–M | **Owner:** UX Designer + Principal Engineer

**Description**

The CLI emits stage names like `"approval"`, `"consistency_check"`, and `"qa"` as status fields in progress output. These are internal implementation identifiers, not user-facing labels. Operators reading logs or piping output to dashboards see machine-internal state rather than human-readable progress descriptions.

**Forward plan**

Create a display-name mapping and apply it in the progress output formatter:

```
"spec"              → "Writing spec"
"qa"                → "Quality review"
"consistency_check" → "Consistency check"
"approval"          → "Final approval"
```

The internal stage names remain unchanged throughout the codebase; only the display layer is affected. This is a contained change with meaningful operator experience improvement.

---

### ARCH-001 — Plan for shared-base-class agent contract before agent count grows

**Priority:** Medium | **Effort:** L | **Owner:** Principal Engineer

**Description**

The current 7-agent suite already demonstrates the duplication tax (see ENG-003). At 15+ agents, the ENG-003 refactor becomes substantially more expensive — more files, more behavioral drift risk, more test surface to verify. The architecture needs a documented agent contract before the next agent is added.

**Forward plan**

Tie this directly to the ENG-003 refactor. Once the shared base classes are extracted, document the agent contract in `ARCHITECTURE.md`: what the 5-stage pipeline requires, which methods are required overrides, and which are optional. Make the base class design a prerequisite for merging any PR that adds a new agent. The documentation investment here is as important as the code investment.

---

### DOCS-PROCESS — Add version-sync check to release process

**Priority:** Medium | **Effort:** S | **Owner:** Technical Writer

**Description**

Version drift occurred in every release cycle audited: README showing v1.0.3, USER-MANUAL showing v0.9.1, landing page showing v1.0.1, while the actual release was v1.0.5. This happens because the release process relies on human memory to update each document. Memory fails consistently.

**Forward plan**

Add a step to `scripts/verify-release.sh` that greps for the version string across `README.md`, `USER-MANUAL.md`, `docs/index.html`, and `pyproject.toml` and fails with a clear error message if any don't match the version in `agentsuite/__version__.py`. This is a small script addition that mechanically prevents a class of bugs that appeared in every release audit.

---

### UX-006 — project_slug silently ignored in list_runs

**Priority:** Low | **Effort:** S | **Owner:** UX Designer

**Description**

The `list_runs` MCP tool accepts a `project_slug` parameter that is documented as a filter. The implementation ignores the parameter entirely and returns all runs regardless of value. A caller passing `project_slug` to narrow results receives unfiltered output with no indication that the filter was not applied.

**Forward plan**

Either implement the filter (match run directories whose `run_metadata.json` contains the slug) or remove the parameter from the tool definition and update the documentation. Silently ignoring a documented filter parameter is worse user experience than not offering the filter at all.

---

### TEST-005 — VCR cassette infrastructure is dead code

**Priority:** Low | **Effort:** S | **Owner:** Test Engineer

**Description**

The project ships VCR cassette infrastructure — conftest fixtures, possibly a `cassettes/` directory — with zero cassettes recorded. It adds setup noise and contributor confusion without providing test value. Future contributors will spend time understanding the VCR setup before discovering it does nothing.

**Forward plan**

Either record actual cassettes for integration tests (converting them to lightweight deterministic replay tests, which would be a genuine improvement), or remove the VCR infrastructure entirely. Dead infrastructure that misleads contributors is worse than infrastructure that was never added.

---

## Design Debt Summary

The most structurally important investment in the next sprint is **ENG-003** (7× stage-handler duplication). Until the shared base classes are extracted, every bug in pipeline logic requires 7 fixes and every new agent adds 7 new copies of the same patterns. ENG-003 sets the foundation for the entire maintainability trajectory of the project — and **ARCH-001** is its documentation counterpart, establishing the agent contract that makes the base class usable without tribal knowledge.

The most important test-culture investment is the **TEST-003 + TEST-004** pairing: mcp_tools coverage across the 4 uncovered agents closes the gap on the primary MCP integration surface, and the revision cycle end-to-end test covers the single most important user-facing pipeline feature that currently has no automated verification. Together these two items represent the largest blind spot in the suite relative to product behavior.

The most important process investment is **DOCS-PROCESS** (version-sync check in `verify-release.sh`). Version drift appeared in every role's findings across every sprint reviewed in this audit cycle. It is not a human attention failure — it is a missing gate. Adding a mechanical check to the release script converts a recurring human error into a blocked CI step. Small effort, permanent fix.
