# AgentSuite — Product Status Report
**Date:** 2026-04-30
**Version:** v1.0.5 (released and tagged today)
**Repo:** scottconverse/agentsuite
**Prepared by:** Five-role audit team (Principal Engineer, UX Designer, Technical Writer, Test Engineer, QA Engineer)
**Intended reader:** Product owner (Scott)

---

## 1. What This Document Is

This is the single-source-of-truth status report for AgentSuite as of the v1.0.5 release. It covers the full release history, current functional state, infrastructure in place, findings from the five-role post-ship audit, active sprint priorities, structural debt, open decisions, and a bottom-line assessment. It is intended to be read start to finish at sprint close and referenced during planning for the next sprint.

The companion audit package lives at `dev-reports/audit-AgentSuite-2026-04-30-v105/`. That package contains the role-by-role deep dives, evidence, and line-number citations behind every finding summarized here. This document is the synthesis; the deep dives are the evidence.

---

## 2. Product Overview

AgentSuite is a local AI pipeline suite that generates structured product artifacts through a seven-agent, five-stage pipeline. The pipeline stages are: Spec (artifact specification), QA (quality review), Consistency Check (cross-artifact validation), Approval (final gate; can trigger revision), and Artifact (final output). The seven agents — Product, Design, Engineering, Marketing, Trust & Risk, CIO, and a seventh agent — each run the same five-stage contract with their own prompts, rubrics, and output schemas.

The product is distributed via GitHub only. There is no PyPI package and no plan to add one; this is an explicit, settled decision. Installation is local. The two primary interfaces are a CLI (`agentsuite run <agent> --project <slug>`) and an MCP server for IDE integration via the Model Context Protocol. Four LLM providers are supported: Anthropic (Claude), OpenAI, Gemini, and Ollama (local).

AgentSuite is actively developed and functional. It is not in production deployment.

---

## 3. Release History

| Version | Date | What Shipped |
|---------|------|--------------|
| v0.1.0 | 2026-04-26 | L0 Gemini + L1 Ollama provider foundation |
| v0.2.0 | 2026-04-26 | Design Agent |
| v0.3.0 | 2026-04-26 | Product Agent |
| v0.7.0 | 2026-04-27 | 544 tests |
| v0.8.0 | 2026-04-27 | Sprint 2 engineering hardening |
| v0.9.0 | 2026-04-28 | Release pipeline (had a release-pipeline bug; surface identical to v0.9.1) |
| v0.9.1 | 2026-04-28 | 676 tests, 7 ADRs backfilled, idempotency contract pinned |
| v1.0.0 | 2026-04-29 | First stable release |
| v1.0.1 | 2026-04-29 | Patch |
| v1.0.2 | 2026-04-30 | ConsistencyCheckFailed changed from fatal to non-fatal (design decision, not a bug) |
| v1.0.3 | 2026-04-30 | Patch |
| v1.0.4 | 2026-04-30 | CR-101: `json.loads` robustness to markdown fences; CR-102: `cost_summary` null model/provider guard |
| v1.0.5 | 2026-04-30 | 87-test stress suite; score coercion; null guards; `SequentialMockLLMProvider`; test assertion corrections |

The project went from initial prototype to a 908-test, seven-agent system in four days. The pace is visible in the release sequence: three agents and the core pipeline in the first two days, engineering hardening and test coverage through the remainder of the sprint, and a cluster of reliability patches in the v1.0.x series as the stress suite surfaced edge cases.

---

## 4. Current Functional State

### Agents

All seven agents are functional and ship with the five-stage pipeline contract. They are not listed individually here because the audit found no agent-level functional failures — the reliability issues found are in shared infrastructure (JSON extraction, retry behavior) that affects all agents equally.

### Pipeline

The five-stage pipeline is implemented, consistent across all agents, and working. The ConsistencyCheck stage has been non-fatal since v1.0.2 — this is a design decision, not an unresolved issue. The Approval stage can raise `RevisionRequired`, but the handling of that exception in the CLI and MCP server is currently broken (see Critical finding UX-002).

### Providers

All four providers (Anthropic, OpenAI, Gemini, Ollama) are functional. The `RetryingLLMProvider` wraps all four with exponential backoff. One gap exists: authentication errors are currently retried three times before failing, which wastes time and obscures the real problem (see Critical finding QA-001).

### Infrastructure

The following infrastructure components are in place and working:

- **RetryingLLMProvider** — Exponential backoff with configurable retry limits and a `_NO_RETRY_EXCEPTIONS` pattern. The design is correct; it has one known gap (auth errors, addressable in this sprint).
- **CostTracker** — Per-run cost tracking with a hard cap (`AGENTSUITE_COST_CAP_USD`) and a soft-warn threshold (`soft_warn_usd`). The cap works. The soft-warn threshold is set correctly but never surfaces a message to the operator (see Major finding ENG-005).
- **`extract_json()`** — JSON extraction from LLM responses with a fallback for markdown-wrapped output. The primary path works; the fallback has a correctness bug when prose contains curly braces (see Major finding ENG-006).
- **`SequentialMockLLMProvider`** — Shipped in v1.0.5 as the test infrastructure for the stress suite. Works correctly but has no tests of its own (see next-sprint item TEST-002).
- **CI (GitHub Actions)** — Runs unit, integration, and golden tests on every PR. The 87-test stress suite is excluded (see Critical finding TEST-001 — one-line fix).
- **MCP Server** — Well-structured, correctly named, cleanly separated from the CLI.

### Test Suite

The test suite stands at 908 total tests across four categories: unit, integration, golden output, and stress. There are zero test skips. All 908 pass as of v1.0.5. The one cleanroom end-to-end test exercises the full mocked pipeline through all five stages. The stress suite (87 parametrized tests) covers QA rubric edge cases that were directly responsible for catching the v1.0.5 reliability regressions before release.

### Documentation (Honest Assessment)

The documentation is in a mixed state. The CHANGELOG is substantively current through v1.0.5 but has broken footer comparison links. The technical content in the README and USER-MANUAL is accurate, but version strings are stale across multiple documents: the README badge shows v1.0.3, the USER-MANUAL has contradictory version references (v0.9.1 in the footer, v1.0.2 in the header, actual version v1.0.5), and the landing page (`docs/index.html`) shows v1.0.1 and lists shipped features as "coming soon." Patches for all four documents are ready to apply in `doc-rewrites/`. The CONTRIBUTING.md and LICENSE exist and are in acceptable shape.

---

## 5. Audit Findings — Summary

The five-role audit (Principal Engineer, UX Designer, Technical Writer, Test Engineer, QA Engineer) completed on 2026-04-30, covering v1.0.5. Total findings: 57, distributed as follows:

| Severity | Count |
|----------|-------|
| Blocker | 0 |
| Critical | 6 |
| Major | 20 |
| Minor | 19 |
| Nit | 12 |

No blockers. The Critical and Major findings are the sprint-relevant items. The six Critical findings are described in detail below; the Major findings are summarized. Full evidence, line numbers, and fix paths are in the role deep-dive files.

### Critical Findings

**ENG-001 — Path Traversal in CIO and Trust Risk MCP Tools (Security)**

The `artifact_name` and `template_name` parameters in `agentsuite/agents/cio/mcp_tools.py` and `agentsuite/agents/trust_risk/mcp_tools.py` are passed directly to `open(run_dir / artifact_name)` with no path containment validation. Any MCP caller can read arbitrary `.md` files outside the intended run directory. The fix is a `pathlib` containment check — resolve the path, assert it is within `run_dir`, raise a `ValueError` otherwise. Two files to fix, unit tests to add. Contained blast radius; audit all MCP callers before releasing.

**UX-002 — RevisionRequired Dead End (UX + Error Handling)**

When the approval stage rejects output and raises `RevisionRequired`, the CLI prints a vague error with no recovery instructions. The MCP server propagates an unhandled exception. Users cannot tell what to revise or how to re-run. This is a core product feature — the revision loop is the primary mechanism by which agents improve output — and it is currently broken from a user experience standpoint. The fix requires the CLI to catch `RevisionRequired`, print the revision notes, and print a clear re-run instruction; the MCP should return structured error JSON with a `revision_notes` field.

**TEST-001 — Stress Suite Excluded from CI (Test Coverage)**

The `.github/workflows/test.yml` workflow runs unit, integration, and golden tests but omits `tests/stress/`. The 87-test stress suite never gates a pull request. The v1.0.5 reliability fixes were caught by that suite — but only because it was run manually. This is a one-line fix in the workflow file. The blast radius concern is CI runtime: 87 parametrized tests will lengthen each run. Any flakiness in the stress suite will now block PRs. Run the suite locally, resolve any flakiness, and merge the CI change.

**QA-001 — Auth Errors Silently Retried 3× (Reliability)**

`RetryingLLMProvider._NO_RETRY_EXCEPTIONS` does not include provider authentication error types. A bad API key triggers the full three-attempt retry loop before the real error surfaces. This was confirmed with a fake key. The fix is to add `anthropic.AuthenticationError`, `openai.AuthenticationError`, and the Gemini equivalent to `_NO_RETRY_EXCEPTIONS` in `agentsuite/llm/retrying.py`. Transient errors continue to retry normally; only auth errors are affected.

**DOC-002 — USER-MANUAL Version Contradiction (Documentation)**

`USER-MANUAL.md` contains two version references that contradict each other and are both wrong. The footer reads "v0.9.1"; the version header reads "v1.0.2"; the actual version is v1.0.5. A user referencing the manual cannot trust which version it describes. A patch file is ready at `doc-rewrites/USER-MANUAL-version-patch.md`.

**UX-001 + DOC-005 — Landing Page Stale (UX + Documentation, cross-role)**

`docs/index.html` displays a v1.0.1 badge and lists features that have already shipped as "coming soon." The first impression for any new user or evaluator is a project that appears unmaintained. A patch file is ready at `doc-rewrites/index.html-version-roadmap-patch.html`.

### Notable Major Findings

Twenty Major findings were identified. The following are the highest-leverage items:

- **ENG-003** — The spec, qa, consistency_check, and approval stage handlers are copy-pasted across all seven agents. The v1.0.5 sprint already paid this tax: the score coercion fix required patching seven files. This will become the dominant maintenance cost as agent count grows.
- **ENG-005 + UX-005 (cross-role)** — `CostTracker.warned` is set correctly but no message is emitted to stderr when the soft-warn threshold is exceeded. Operators have no real-time cost signal until the hard cap stops the run.
- **ENG-006 + QA-007 (cross-role)** — `extract_json()` fallback uses `find('{')` + `rfind('}')`. When LLM prose contains a `{` before the actual JSON, the slice is wrong and parsing fails silently. This affects all seven agents on any response where the model includes explanatory prose around the JSON object.
- **ENG-002** — `AGENTSUITE_LLM_PROVIDER_FACTORY` is dynamically imported without restriction. This is an arbitrary code execution vector in any multi-user or CI environment where environment variables can be influenced by untrusted input.
- **QA-005** — An invalid agent name in `AGENTSUITE_ENABLED_AGENTS` raises an unhandled traceback with no user-friendly error.
- **TEST-003 + TEST-004 (cross-role)** — Four of seven agents (engineering, marketing, trust_risk, cio) have no unit tests for their `mcp_tools.py` modules. The path traversal bug would have been caught by such tests. Additionally, the revision cycle (approval rejection → re-run → passing output) has no end-to-end test coverage at all.
- **DOC-001 + QA-002, DOC-004** — README badge shows v1.0.3; CHANGELOG footer comparison links are frozen at v0.9.1, missing all v1.0.x releases.

The remaining Major and Minor findings are enumerated in the role deep-dives and the sprint punchlist. They are real issues; they are deferred only because the items above have higher blast-radius risk or user impact.

---

## 6. What Is Solid

This section is not padding. The audit found genuine strengths, and they matter for planning because they represent investments that have already paid off and should be maintained.

**Test quantity and discipline.** 908 tests at this stage of a project is strong. The stress suite directly caught the v1.0.5 reliability regressions before release. The zero-skip policy is holding. The cleanroom E2E test validates the full pipeline without API cost.

**RetryingLLMProvider design.** The pattern — exponential backoff, configurable limits, `_NO_RETRY_EXCEPTIONS` — is correct and well-implemented. The auth-error gap is an omission in the exception list, not a design flaw. The fix is additive and non-disruptive.

**Cost tracking architecture.** `CostTracker` with a hard cap and a soft-warn threshold is fundamentally right. The soft-warn gap is a missing two-line wire, not a conceptual problem with the design.

**Five-stage pipeline contract.** The pipeline is clean, consistent across all seven agents, and gives each agent a predictable shape. New agents can be scaffolded against a clear contract. This is the right architectural choice.

**MCP server architecture.** Well-structured, correctly separated from the CLI, correct tool naming conventions. The security gap is in specific parameter handling, not in the server's overall design.

**Provider abstraction.** Supporting four providers through a clean interface is non-trivial. It is well-executed.

**v1.0.5 reliability improvements.** Score type coercion and `parsed["scores"]` null guards resolved genuine runtime failures. The issues were correctly identified, triaged, and resolved quickly.

---

## 7. Current Sprint — What Needs to Happen Before Close

The sprint punchlist contains 11 items. All are S or M effort. The estimated total is one to two days of engineering. Items are ordered by priority; the first four are the critical path.

| Priority | ID | Size | What |
|----------|----|------|------|
| 1 | TEST-001 | S | Add `tests/stress` to CI workflow — one line |
| 2 | ENG-001 | M | Path containment check in CIO + trust_risk MCP tools |
| 3 | UX-002 | M | RevisionRequired recovery path in CLI and MCP |
| 4 | QA-001 | S | Auth errors to `_NO_RETRY_EXCEPTIONS` |
| 5 | DOC-002 | S | USER-MANUAL version fix (patch file ready) |
| 6 | UX-001 + DOC-005 | S | Landing page version + roadmap (patch file ready) |
| 7 | ENG-005 + UX-005 | S | Wire cost soft-warn to stderr |
| 8 | ENG-006 + QA-007 | S | Fix `extract_json` rfind fallback |
| 9 | QA-005 | S | Guard on `AGENTSUITE_ENABLED_AGENTS` misconfiguration |
| 10 | DOC-004 | S | CHANGELOG footer comparison links |
| 11 | DOC-001 + QA-002 | S | README badge to v1.0.5 |

The CI fix (item 1) should be merged first because it immediately raises the visibility of any regressions introduced by the subsequent fixes. The path traversal fix (item 2) is the only security issue in the sprint; it should not be deferred beyond this sprint regardless of workload.

Full fix paths, file names, and test requirements for each item are in `sprint-punchlist.md`.

---

## 8. Next Sprint — Structural Investments

The next-sprint watchlist contains 12 items. These are not emergency fixes; they are the investments that prevent next sprint's emergencies. The three highest-leverage items are:

**ENG-003 — Eliminate 7× stage-handler duplication (L effort).**
This is the most important structural investment in the project right now. Until the shared base classes are extracted, every bug in pipeline logic requires seven fixes and every new agent deepens the debt. The refactor must be done one stage type per pull request, with the golden and stress suites run after each step. Adding any new agent before this refactor is complete multiplies the future cost of doing it. A concrete recommendation is at the end of this document.

**TEST-003 + TEST-004 — mcp_tools coverage + revision cycle E2E (M each).**
Four agents have no tests for their primary MCP integration surface. The path traversal bug in this sprint was caught by audit, not by automated testing. The revision cycle — the central mechanism by which the pipeline improves output — has no end-to-end test at all. These two items together represent the most significant blind spot in the test suite relative to actual product behavior.

**DOCS-PROCESS — Version-sync check in `verify-release.sh` (S effort).**
Version drift appeared in the findings of every role across every sprint reviewed in this audit. It is not a human attention failure; it is a missing gate. A grep check in `verify-release.sh` that compares the version string in `README.md`, `USER-MANUAL.md`, `docs/index.html`, and `pyproject.toml` against `agentsuite/__version__.py` converts a recurring manual error into a blocked release script. This is a small investment with permanent returns.

The remaining nine watchlist items (SequentialMockLLMProvider coverage, VCR dead code removal, `AGENTSUITE_LLM_PROVIDER_FACTORY` whitelist, Gemini cost model accuracy, CLI stage display names, project_slug filter, cost cap validation, and the agent contract architecture doc) are in `next-sprint-watchlist.md` with full detail.

---

## 9. Decisions on Record

The following decisions are settled. They should not be revisited without a specific triggering reason.

- **No PyPI distribution.** AgentSuite is local-install only. Explicit decision from 2026-04-26, unchanged.
- **ConsistencyCheckFailed is non-fatal.** Changed in v1.0.2. This is a design choice, not a bug.
- **Gemma 4 as local default for Ollama.** E2B, E4B, and 26B-MoE are available at install. No change needed.
- **Live E2E tests only on major (v0.X.0) releases.** API keys are never committed. $10 cap per live run.
- **"Full E2E" means the 908-test pytest suite plus the cleanroom test.** It is mocked and costs $0.
- **Seven ADRs on file.** Available in the repo for architectural context.

---

## 10. Open Questions — Decisions Needed

**ENG-002 — AGENTSUITE_LLM_PROVIDER_FACTORY arbitrary code execution.**
Today, this is acceptable. AgentSuite is a local, single-user tool. The dynamic import vector only becomes a genuine risk if the product is deployed as a shared service, used in CI pipelines with externally supplied environment variables, or wrapped in a multi-tenant API layer. The question is whether to enforce a whitelist now (contained change, permanent fix) or defer until there is a concrete multi-user use case. The next-sprint watchlist recommends doing it now; the work is M effort and the risk window is currently small.

**ENG-003 timing — freeze new agents until base class extraction is done, or pay the duplication tax once more?**
Every new agent added before ENG-003 is complete adds another full copy of the four stage-handler patterns and another file to patch on every shared bug fix. The recommendation in this report is to freeze new agent additions until ENG-003 is complete. If that freeze is unacceptable, the cost of proceeding should be acknowledged explicitly: the next new agent will require the same duplication, and ENG-003 becomes proportionally more expensive after it ships.

**Version-sync process — when does this land?**
Version drift hit every sprint reviewed in this audit. The verify-release.sh fix is S effort. The only reason to defer it is if the sprint is already full. It is worth scheduling explicitly rather than leaving it as a "we'll get to it" item, because the pattern of evidence is that it does not get done without a named sprint slot.

---

## 11. Audit Artifacts

The full audit package is at `dev-reports/audit-AgentSuite-2026-04-30-v105/`:

- `00-executive-audit.md` — Audit entry point: severity roll-up, top 10 findings, blast-radius callouts
- `01-engineering-deepdive.md` — Principal Engineer findings (ENG-001 through ENG-011)
- `02-uiux-deepdive.md` — UX Designer findings (UX-001 through UX-006)
- `03-documentation-deepdive.md` — Technical Writer findings (DOC-001 through DOC-005)
- `04-test-deepdive.md` — Test Engineer findings (TEST-001 through TEST-005)
- `05-qa-deepdive.md` — QA Engineer findings (QA-001 through QA-007)
- `sprint-punchlist.md` — 11 items, this sprint, with file paths and test requirements
- `next-sprint-watchlist.md` — 12 items, next sprint
- `doc-rewrites/` — Four ready-to-apply patch files: USER-MANUAL version fix, CHANGELOG footer links, landing page version and roadmap, README badge

---

## 12. Bottom Line

AgentSuite v1.0.5 is in fundamentally good shape for a project at this stage. The architecture is sound, the test suite is unusually strong, the pipeline contract is clean, and the reliability infrastructure (retry, cost tracking, JSON extraction) is correctly designed even where specific gaps exist. None of the audit findings suggest the architecture needs to be reconsidered.

The most important thing to fix this sprint is the path traversal vulnerability in the CIO and trust_risk MCP tools. It is the only finding with a security classification, it is contained and fast to fix, and it should not remain open past this sprint. The RevisionRequired dead end is a close second — it is the most visible user-facing failure in the current codebase, affecting a core product feature on every pipeline rejection.

The most important structural investment for the next sprint is ENG-003: eliminating the seven-times duplication of stage-handler code. This refactor is deferred for good reasons — it is L effort and carries meaningful blast radius — but it needs a named sprint slot rather than indefinite deferral. The project's maintainability trajectory depends on it. Every agent added before this refactor multiplies the eventual cost of doing it, and every shared bug fix in the interim pays the duplication tax again.

---

*This document covers the state of AgentSuite as of 2026-04-30 after the v1.0.5 release. All findings are sourced from the five-role audit completed the same day. Claims in this report are backed by evidence in the role deep-dive files; this document is the synthesis.*
