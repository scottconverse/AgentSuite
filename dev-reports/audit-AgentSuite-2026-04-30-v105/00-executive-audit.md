# AgentSuite v1.0.5 — Executive Audit Report

**Audit Date:** 2026-04-30
**Package Version:** v1.0.5
**Audit Package:** `dev-reports/audit-AgentSuite-2026-04-30-v105/`
**Produced by:** Five-role parallel audit team (Principal Engineer · UX Designer · Technical Writer · Test Engineer · QA Engineer)

---

## Executive Summary

AgentSuite v1.0.5 is a structurally sound, 908-test, 7-agent AI pipeline with a clean architecture, solid retry infrastructure, and a functional MCP server. The v1.0.5 release addressed genuine reliability bugs (score coercion, null guards) and the project's test discipline is above average for a project at this stage. However, the audit surfaced 6 Critical findings that should be addressed this sprint: a path traversal vector in two MCP tools, a `RevisionRequired` error dead end with no recovery path, an 87-test stress suite excluded from CI, auth errors that silently retry instead of failing fast, and two documentation surfaces (USER-MANUAL and landing page) with version contradictions that will confuse users. A structural concern — 7× stage-handler duplication across agents — is manageable now but will become the dominant maintenance cost if left unaddressed as the agent count grows.

---

## Severity Roll-Up

**Total findings: 57**

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 6 |
| Major | 20 |
| Minor | 19 |
| Nit | 12 |

**By role:**

| Role | Critical | Major | Minor | Nit |
|---|---|---|---|---|
| Principal Engineer (`01`) | 1 | 7 | 4 | 3 |
| UX Designer (`02`) | 2 | 4 | 3 | 2 |
| Technical Writer (`03`) | 2 | 4 | 5 | 4 |
| Test Engineer (`04`) | 1 | 3 | 4 | 1 |
| QA Engineer (`05`) | 1 | 5 | 4 | 2 |

> Note: 6 cross-role patterns identified where multiple roles independently flagged the same issue. These are the highest-leverage items and are noted in the Top 10 below. Counts are deduplicated — cross-role findings are counted once in the totals.

---

## Top 10 Findings

Sorted by severity. Cross-role findings are noted. Start here — the first four are this sprint's critical path.

---

### 1. ENG-001 — Path Traversal in CIO + trust_risk MCP Tools
**Severity:** Critical | **Category:** Security

The `artifact_name` and `template_name` parameters in `agentsuite/agents/cio/mcp_tools.py` and `agentsuite/agents/trust_risk/mcp_tools.py` are passed directly to `open(run_dir / artifact_name)` with no path containment validation. Any MCP caller can read arbitrary `.md` files on the filesystem outside the run directory.

**Fix path:** Add `pathlib` containment check — resolve the path, assert it is within `run_dir`, raise `ValueError` otherwise. Pattern:
```python
resolved = (run_dir / artifact_name).resolve()
if not str(resolved).startswith(str(run_dir.resolve())):
    raise ValueError(f"Path traversal blocked: {artifact_name}")
```

**Blast radius:** Only affects CIO and `trust_risk` MCP tools. Fix requires updating both files and adding unit tests for the containment check. No migration needed. Audit all MCP callers before releasing — any integration inadvertently reading outside `run_dir` will now receive an error.

---

### 2. UX-002 — RevisionRequired Dead End
**Severity:** Critical | **Category:** UX + Error Handling

When `approval.py` raises `RevisionRequired`, the CLI prints a vague error with no instructions. MCP tools propagate an unhandled exception. Users have no recovery path — they cannot tell what to revise or how to re-run.

**Fix path:** CLI catches `RevisionRequired`, prints revision notes, and prints a clear recovery instruction (e.g., "Re-run with `--revise` to address the feedback above"). MCP catches it and returns structured error JSON with a `revision_notes` field.

**Blast radius:** Changes CLI exit behavior. Update approval-stage unit tests after the fix to cover the new exit path.

---

### 3. TEST-001 — Stress Suite Excluded from CI
**Severity:** Critical | **Category:** Test Coverage

`.github/workflows/test.yml` runs only `tests/unit tests/integration tests/golden`. The 87-test stress suite (`tests/stress/`) never gates a PR. Stress regressions are invisible in CI. The v1.0.5 reliability fixes (score coercion, null guards) were caught by the stress suite — but only because the suite was run manually.

**Fix path:** Add `tests/stress` to the pytest invocation in the workflow file. One-line change.

**Blast radius:** CI runtime will increase (87 parametrized tests). Verify the full stress suite passes cleanly before merging. If any stress tests are currently flaky, they will now gate PRs — investigate and fix flakiness before merging.

---

### 4. QA-001 — Auth Errors Silently Retried 3×
**Severity:** Critical | **Category:** Reliability

`RetryingLLMProvider._NO_RETRY_EXCEPTIONS` does not include provider authentication error types. A bad API key triggers the full retry loop (3 attempts, ~3 seconds) before the real error surfaces. Confirmed with `sk-fake` key test.

**Fix path:** Add `anthropic.AuthenticationError`, `openai.AuthenticationError`, and Gemini auth error types to `_NO_RETRY_EXCEPTIONS` in `agentsuite/llm/retrying.py`.

**Blast radius:** Narrowly scoped — only changes behavior for auth error types. Transient errors still retry normally. Run the full retry unit test suite after this fix to confirm no regression.

---

### 5. DOC-002 — USER-MANUAL Version Contradiction
**Severity:** Critical | **Category:** Documentation

`USER-MANUAL.md` has "v0.9.1" in the footer and "v1.0.2" in the version header. Both are wrong (actual: v1.0.5). A user reading the manual cannot trust which version of the product it describes — and on a support interaction, this version confusion wastes everyone's time.

**Fix path:** Apply the patch at `doc-rewrites/USER-MANUAL-version-patch.md`. Find-replace all version strings to "v1.0.5".

**Blast radius:** Doc-only change.

---

### 6. UX-001 + DOC-005 — Landing Page Stale [CROSS-ROLE: UX Designer + Technical Writer]
**Severity:** Critical | **Category:** UX + Documentation

`docs/index.html` shows a v1.0.1 badge. The roadmap section lists features that have already shipped as "coming soon." The first impression for any new user or evaluator is a product that appears unmaintained.

**Fix path:** Apply the patch at `doc-rewrites/index.html-version-roadmap-patch.html`. Update badge to v1.0.5. Move shipped items to a "Shipped" section.

**Blast radius:** Doc-only change.

---

### 7. ENG-003 — 7× Stage-Handler Duplication [CROSS-ROLE: Principal Engineer + Test Engineer]
**Severity:** Major | **Category:** Architecture

The `spec`, `qa`, `consistency_check`, and `approval` stage handlers are copy-pasted across all 7 agents. v1.0.5 already paid the duplication tax: the score coercion fix required patching 7 files. Future bugs and behavior changes will multiply the same way. This is manageable now; it becomes the dominant maintenance cost if left unaddressed as agent count grows.

**Fix path:** Extract shared base classes or mixins per stage type. Each agent subclasses with only its prompt/rubric specifics. Deferred to next sprint (L effort).

**Blast radius:** Touches all 7 agents' stage modules. Run golden + stress suite after each extraction step. Do not merge partial extractions — each step must leave the suite passing.

---

### 8. ENG-005 + UX-005 — Cost Soft-Warn Never Surfaced [CROSS-ROLE: Principal Engineer + UX Designer]
**Severity:** Major | **Category:** Operational Feedback

`CostTracker.warned` is set correctly when spend exceeds `soft_warn_usd`, but no message is emitted to stderr. Operators get zero real-time cost signal until the hard cap is hit. On a long pipeline run, this means the first signal is an abrupt stop, not a warning.

**Fix path:** Emit a `stderr` line when `warned` is first set. Two lines of code in `agentsuite/core/cost.py`.

**Blast radius:** Minor. Add a unit test asserting the stderr emission.

---

### 9. ENG-006 + QA-007 — extract_json rfind Fallback Broken [CROSS-ROLE: Principal Engineer + QA Engineer]
**Severity:** Major | **Category:** Reliability

`extract_json()` fallback uses `find('{')` + `rfind('}')`. When LLM prose contains `{` before the real JSON object, the slice is wrong and parsing fails silently. This affects all 7 agents on any LLM response with prose containing braces — a common pattern in model output.

**Fix path:** Replace fallback with `re.findall(r'\{.*\}', text, re.DOTALL)` scanning for the last valid JSON object.

**Blast radius:** Affects the JSON extraction path used by all 7 agents on every LLM call. Run the full golden suite after this fix to verify no regressions in any agent's output parsing.

---

### 10. ENG-004 + TEST-003 — Missing mcp_tools Tests [CROSS-ROLE: Principal Engineer + Test Engineer]
**Severity:** Major | **Category:** Security + Coverage

Four of seven agents (engineering, marketing, trust_risk, cio) have no unit tests for their `mcp_tools.py` modules. The path traversal bug (ENG-001) would have been caught by tests. The two concerns are linked: test coverage is what catches containment gaps.

**Fix path:** Add `mcp_tools` unit tests for the four untested agents. Follow the existing test pattern from the `product` and `design` agent test suites.

**Blast radius:** Test-only additions. No production code changes.

---

## What's Working Well

This section is not padding. These are genuine strengths — and they matter for prioritization, because they represent bets that have already paid off.

- **Test quantity and discipline.** 908 tests + 87 stress tests + 1 cleanroom E2E is excellent coverage for a project at this stage. The test-first mindset is visible in the architecture. The stress suite catching the v1.0.5 reliability regressions is a direct return on that investment.

- **RetryingLLMProvider.** Exponential backoff, configurable retry limits, and the `_NO_RETRY_EXCEPTIONS` design pattern are all correct. The auth-error gap is an omission, not a design flaw — the pattern is right and the fix is small.

- **Cost tracking architecture.** `CostTracker` + cap + warn is fundamentally sound. The soft-warn gap is a missing wire, not a design gap.

- **Agent pipeline contract.** The 5-stage pipeline (spec → qa → consistency_check → approval → artifact) is clean, consistent, and gives each agent a predictable shape. New agents can be scaffolded against a clear contract.

- **MCP server architecture.** Well-structured, cleanly separated from CLI, correct tool naming conventions.

- **v1.0.5 reliability fixes.** Score type coercion and `parsed["scores"]` null guards resolved real runtime failures. Good triage and fast resolution.

- **Provider abstraction.** Supporting Anthropic, OpenAI, Gemini, and Ollama through a clean provider interface is non-trivial and well-executed.

---

## This-Sprint Punch List (Summary)

Full detail — including exact file paths, line numbers, and test requirements — in `sprint-punchlist.md`. 11 items, all S or M effort. Start at the top and work down; items are ordered by priority.

| Priority | ID | Size | Title |
|---|---|---|---|
| 1 | TEST-001 | S | Add stress suite to CI |
| 2 | ENG-001 | M | Path traversal fix in CIO + trust_risk MCP tools |
| 3 | UX-002 | M | RevisionRequired recovery path |
| 4 | QA-001 | S | Auth errors to `_NO_RETRY_EXCEPTIONS` |
| 5 | DOC-002 | S | USER-MANUAL version contradiction |
| 6 | UX-001+DOC-005 | S | Landing page version + roadmap |
| 7 | ENG-005+UX-005 | S | Wire cost soft-warn to stderr |
| 8 | ENG-006+QA-007 | S | Fix `extract_json` rfind fallback |
| 9 | QA-005 | S | `AGENTSUITE_ENABLED_AGENTS` guard |
| 10 | DOC-004 | S | CHANGELOG footer comparison links |
| 11 | DOC-001+QA-002 | S | README badge to v1.0.5 |

---

## Next-Sprint Watchlist (Summary)

Full detail in `next-sprint-watchlist.md`. 12 items. These are real issues, not nice-to-haves — they are deferred because they require L-effort refactors or have lower blast-radius risk than this sprint's critical items.

**Three highest-leverage investments:**

1. **ENG-003** (L) — Eliminate 7× stage-handler duplication before agent count grows. Every new agent added without this fix deepens the maintenance hole.
2. **TEST-003 + TEST-004** (M each) — `mcp_tools` unit tests for the four untested agents + revision cycle E2E test.
3. **DOCS-PROCESS** (S) — Add a version-sync check to `verify-release.sh` so version drift (DOC-001, DOC-002, DOC-005) cannot recur silently on the next push.

Remaining watchlist items: `SequentialMockLLMProvider` coverage, VCR dead code removal, `AGENTSUITE_LLM_PROVIDER_FACTORY` whitelist, Gemini cost model accuracy, CLI progress display names, `project_slug` filter fix, `AGENTSUITE_COST_CAP_USD` validation on startup, and the shared-base-class architectural plan.

---

## Blast-Radius Callouts

These are the fixes most likely to break adjacent code. Read this section before ordering sprint work — some fixes require sequencing.

**1. ENG-001 path traversal fix.**
Changes what CIO and `trust_risk` MCP tools will accept. Any integration that was reading files outside `run_dir` — whether intentionally or by accident — will now receive a `ValueError`. Audit all MCP callers before releasing. Run mcp_tools unit tests (when written per TEST-003) against the fixed code before merging.

**2. ENG-003 duplication refactor (next sprint).**
Highest blast-radius change in the watchlist. Touches all 7 agents' stage modules. The rule: run golden + stress suite after every individual extraction step. Never merge a partial extraction that leaves the suite in a broken state.

**3. QA-001 auth retry fix.**
Narrowly scoped. Only changes behavior for auth error types — transient errors still retry normally. Run the full retry unit test suite after this fix. Verify the `sk-fake` key path now fast-fails before declaring done.

**4. ENG-006 + QA-007 extract_json fix.**
Affects the JSON extraction path used by all 7 agents on every LLM call. Run the full golden suite after this fix. Any agent whose output parsing depended on the broken fallback behavior (possible if a golden fixture contained brace-laden prose) will surface here.

**5. TEST-001 CI fix.**
Adds 87 parametrized tests to every PR check. CI runtime increases. If any stress tests are currently flaky, they will block PRs immediately after this lands. Do a dry run of the stress suite locally first and resolve any flakiness before merging the CI change.

---

## Appendix: Finding Cross-Reference Index

| Finding ID | Role(s) | Severity | File(s) | Deep-Dive |
|---|---|---|---|---|
| ENG-001 | ENG + TEST | Critical | `agents/cio/mcp_tools.py`, `agents/trust_risk/mcp_tools.py` | `01`, `04` |
| UX-002 | UX + QA | Critical | `cli/main.py`, `approval.py` | `02`, `05` |
| TEST-001 | TEST | Critical | `.github/workflows/test.yml` | `04` |
| QA-001 | QA + ENG | Critical | `llm/retrying.py` | `05`, `01` |
| DOC-002 | DOC | Critical | `USER-MANUAL.md` | `03` |
| UX-001+DOC-005 | UX + DOC | Critical | `docs/index.html` | `02`, `03` |
| ENG-003 | ENG + TEST | Major | All 7 agent stage modules | `01`, `04` |
| ENG-005+UX-005 | ENG + UX | Major | `core/cost.py` | `01`, `02` |
| ENG-006+QA-007 | ENG + QA | Major | `core/json_utils.py` | `01`, `05` |
| ENG-004+TEST-003 | ENG + TEST | Major | `agents/*/mcp_tools.py` (4 agents) | `01`, `04` |

For full evidence, line numbers, and fix paths for every finding in the audit, see the individual deep-dive files listed above.

---

*Audit package: `dev-reports/audit-AgentSuite-2026-04-30-v105/` — 2026-04-30. Each deep-dive file (`01` through `05`) contains full evidence, line-number citations, and fix paths for every finding assigned to that role. The `sprint-punchlist.md` and `next-sprint-watchlist.md` files are the actionable outputs; this document is the entry point.*
