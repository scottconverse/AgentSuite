# Executive Audit — AgentSuite v1.0.1 (Post-Ship)

**Date:** 2026-04-30
**Audited tag:** `v1.0.1` at `865e248`
**Scope:** Full — all five roles (Engineering, UX, Documentation, Test, QA)
**Posture:** Balanced
**Writer mode:** Audit-only

---

## Executive Summary

AgentSuite v1.0.1 is a structurally disciplined project with genuine engineering strengths: atomic state writes, typed exception hierarchy, resume idempotency proven end-to-end, and a cost-cap design that treats budget as a first-class invariant. The v1.0.1 sprint closed its stated audit findings honestly and completely. What this post-ship audit reveals is that **three of the five sprint fixes landed at the wrong scope boundary**. The ENG-001 path-traversal validator was applied to the kernel write path and left off the MCP read path — seven agents, dozens of tools, all unvalidated. The DOC-101 "six stages" correction landed in the CHANGELOG and nowhere else — README, landing page, and launch post drafts all still say "six stages." The USER-MANUAL exists in two versions on disk; the landing page links to the stale 652-line one that says Design and Marketing agents "ship in v0.2+." None of these are regressions from v1.0.0. They are blast-radius misses from the v1.0.1 fix pass.

**No Blockers.** Seven Criticals, thirteen Majors, twelve Minors/Nits (deduplicated across roles). Fix the two security Criticals and the three doc-accuracy Criticals before any future tag. The remaining five Criticals and the Majors are workable at v1.0.2 sprint pace.

---

## Severity Roll-Up (Deduplicated Across All Roles)

| Severity | Count | Note |
|---|---|---|
| Blocker | 0 | — |
| Critical | 7 | 2 security, 2 UX, 3 documentation |
| Major | 13 | 3 security/engineering, 3 UX, 4 test, 3 documentation |
| Minor | 9 | Various |
| Nit | 5 | Various |
| **Total** | **34** | |

> Cross-role duplicates merged: ENG-001/QA-201, ENG-002/QA-202, ENG-004/QA-203, ENG-005/QA-206, UX-204/QA-204, UX-205/DOC-204, UX-206/DOC-203 each counted once.

---

## Top 10 Findings

| # | ID(s) | Severity | Role(s) | Title |
|---|---|---|---|---|
| 1 | ENG-001 / QA-201 | Critical | Eng + QA | MCP read-path traversal: all 7 agents' `get_status` and stage-kick tools accept unvalidated `run_id` |
| 2 | ENG-002 / QA-202 | Critical | Eng + QA | `agentsuite_kernel_artifacts` enumerates filesystem with unvalidated `project_slug` |
| 3 | DOC-201 | Critical | Doc | "Six-stage pipeline" claim persists in README, `docs/index.html`, community launch posts |
| 4 | DOC-202 | Critical | Doc | `docs/USER-MANUAL.md` is a stale 652-line duplicate; landing page links resolve to it |
| 5 | UX-201 | Critical | UX | Raw traceback escapes `--debug` gate on schema-version mismatch in `approve --latest` |
| 6 | UX-202 | Critical | UX | No "what next" signal after `run` completes at approval gate (all 7 agents) |
| 7 | TEST-001 | Critical | Test | vcr cassette infrastructure scaffolded but never populated — integration tier is unit in disguise |
| 8 | ENG-003 | Major | Eng | Intake stage reads arbitrary filesystem paths supplied via `inputs_dir`/`brand_docs` without allowlist |
| 9 | ENG-004 / QA-203 | Major | Eng + QA | `RunStateSchemaVersionError` propagates uncaught from `agentsuite_cost_report` — breaks every v1.0.0 upgrade |
| 10 | UX-204 / QA-204 | Major | UX + QA + Doc | USER-MANUAL install step omits provider extra; new-user journey terminates before first run |

---

## Cross-Role Findings

These issues showed up across multiple independent roles. That means they're higher leverage — fix one, several auditors' findings close.

### Cross-1 — MCP Read-Path Traversal [Eng + QA, Critical × 2]
The v1.0.1 ENG-001 fix correctly added `validate_run_id()` inside `ArtifactWriter.__init__` (write path). It was not propagated to the MCP read path. All 7 agents' `mcp_tools.py` files build `run_dir = output_root_fn() / "runs" / run_id` without calling the validator. Same pattern in `agentsuite_kernel_artifacts` for `project_slug`. Two distinct traversal surfaces, same root cause: the blast radius of the original ENG-001 fix was not fully traced. Engineering flagged it (ENG-001/002), QA confirmed it via probe (QA-201/202). Fix: `validate_run_id(run_id)` and `validate_project_slug(project_slug)` as the first line of each affected function. A shared helper `_require_run_dir` in `agentsuite/agents/_common.py` would DRY the pattern.

### Cross-2 — Error Handling Inconsistency at MCP/CLI Boundaries [Eng + UX + QA, Major]
Three independent code paths produce raw Python tracebacks where structured errors should appear: (a) `approve --latest` with a pre-v0.9 run directory raises `RunStateSchemaVersionError` outside the try/except block in cli.py; (b) `agentsuite_cost_report` propagates the same exception uncaught through FastMCP; (c) `CostCap.from_env()` raises a bare `ValueError` on a non-numeric env var. Engineering flagged (b) and (c) as ENG-004/005. UX flagged (a) as UX-201. QA confirmed both (a) and (b) in journey walkthroughs. Pattern fix: a `@mcp_safe` decorator wrapping all MCP tool functions, and moving `_resolve_latest_run_id()` inside the existing try/except in cli.py.

### Cross-3 — USER-MANUAL Onboarding Failure [UX + QA + Doc, Major]
The USER-MANUAL's Quick Start install step omits the provider extra (`pip install agentsuite` instead of `pip install "agentsuite[anthropic] @ git+..."`). The bare install succeeds but the first `agentsuite founder run` fails — with either a provider-not-found error or a raw traceback depending on what's in the environment. UX flagged it as UX-204, QA walked it as QA-204, Documentation flagged the instruction mismatch. Three roles, one fix: update the install step in USER-MANUAL.md and widen the except clause in `_resolve_llm_for_cli` to catch `ProviderNotInstalled` alongside `NoProviderConfigured`.

### Cross-4 — "Six-Stage" Documentation Drift [Doc + UX, Critical]
The v1.0.1 closure audit fixed "six stages" in CHANGELOG. The phrase was not swept from README:15, docs/index.html:55, discussions-seeds.md:15, or launch-posts.md:44/79. The README architecture diagram 200 lines later correctly shows five stages — the same reader sees contradictory information in one scroll. Documentation flagged all four surfaces (DOC-201). UX confirmed the landing page instance. A `grep -r "six-stage"` sweep fixes all instances in one commit; adding a CI grep assertion (DOC-103, v1.0.2 backlog) prevents recurrence.

### Cross-5 — Dual USER-MANUAL / Stale Landing Page Link [Doc + UX, Critical]
`docs/USER-MANUAL.md` (652 lines) is a v0.2-era document that says Design and Marketing "ship in v0.2+." The landing page (`docs/index.html:127`) and README both link to this file. The root `USER-MANUAL.md` (984 lines) is current and covers all seven agents. A user clicking the Documentation link from GitHub Pages lands on the stale document. Documentation flagged this as DOC-202. UX confirmed the journey failure. Fix: delete `docs/USER-MANUAL.md` and update both links to the root file.

---

## What's Working Well

This section is not filler. These are genuine strengths the dev team should preserve.

**Engineering:** Atomic state writes (`mkstemp` + `fsync` + `os.replace`), typed exception hierarchy (`RunStateSchemaVersionError`, `HardCapExceeded`, `ConsistencyCheckFailed`), `CostCap.from_env()` design pattern, `MockLLMProvider` longest-match semantics, and the `_resolve_safe` layered path guard in `ArtifactWriter` are all well-built. The CI pipeline (lint + test + provider-drift + release) is comprehensive for a solo-maintained project.

**UX:** Stderr/stdout stream discipline is correct and executed cleanly. Stage progress format (`[OK] intake complete (12.3s, $0.0234)`) is terse, informative, and pipe-safe. `agentsuite-mcp --help` is hand-authored and surfaces every env var with its default and accepted values — exactly what an integrator needs. Landing page color contrast passes WCAG 2.1 AA at all sampled combinations.

**Documentation:** CHANGELOG v1.0.1 entry is honest, cites every finding ID, and distinguishes "closed" from "deferred." The seven ADRs are current and directly useful. Root `USER-MANUAL.md` (984 lines) is comprehensive with per-agent CLI sections and a 40-term glossary. SECURITY.md covers a real disclosure SLA, not boilerplate. `docs/troubleshooting.md` explicitly flags `trust_risk` underscore as a common mistake — the right information in the right place.

**Tests:** Zero unconditional skips (Hard Rule 4a satisfied, documented, and backed up in code). Resume idempotency tested end-to-end with a custom crash-and-recover mock. Golden tier covers all seven agents with `assert_artifact_exact` / `assert_qa_within_tolerance` helper split — numeric tolerance for floats, exact match for text. Drift traps (`test_mcp_tool_names_documented.py`, `test_readme_cli_invocations.py`) gate on live doc content, not just code. Downstream consumer type-check is an uncommon and valuable gate.

**QA:** Primary CLI journey passes cleanly for an experienced developer. Kernel error behavior is typed and consistent on the happy path. The `_BillableThenCrashThenSucceed` integration test is the most sophisticated test in the suite.

---

## This-Sprint Punch List

Fix these before v1.0.2 tag. All are S or M in effort.

| Priority | ID(s) | Severity | Effort | What to do |
|---|---|---|---|---|
| 1 | ENG-001/QA-201 | Critical | S | Add `validate_run_id(run_id)` as first line of each `get_status` and stage-kick function in all 7 agents' `mcp_tools.py`. Add test in `test_mcp_server.py` for traversal probe. |
| 2 | ENG-002/QA-202 | Critical | S | Add `validate_project_slug(project_slug)` as first line of `agentsuite_kernel_artifacts` in `mcp_server.py`. Add test. |
| 3 | DOC-201 | Critical | S | `grep -r "six-stage" .` and replace all instances with "five-stage ... plus a kernel-managed approval step". Sweep README:15, docs/index.html:55, discussions-seeds.md:15, launch-posts.md:44/79. |
| 4 | DOC-202 | Critical | S | Delete `docs/USER-MANUAL.md`. Update links in `docs/index.html:127` and `README.md:277` to root `USER-MANUAL.md`. |
| 5 | UX-201 | Critical | S | Move `_resolve_latest_run_id(...)` inside the existing `try/except Exception` block in `cli.py:_make_approve_fn`. |
| 6 | UX-202 | Critical | M | Add `next_step_hint` field to `AgentCLISpec`. Emit to stderr after JSON output in `cli.py:_register_agents()`. Set hint per-agent. |
| 7 | ENG-004/QA-203 | Major | S | Wrap `store.load()` in `agentsuite_cost_report` with `try/except RunStateSchemaVersionError: log.warning; continue`. Add test for v1.0.0 schema dirs. |
| 8 | UX-204/QA-204 | Major | S | Fix USER-MANUAL install step. Widen `except` in `_resolve_llm_for_cli` to catch `ProviderNotInstalled`. |

---

## Next-Sprint Watchlist

For v1.0.2 sprint planning. Effort estimates are rough.

| ID(s) | Severity | Effort | Category | What to watch |
|---|---|---|---|---|
| ENG-003 | Major | L | Security | Intake reads arbitrary paths from `inputs_dir`/`brand_docs`/`screenshots` without allowlist. Add `AGENTSUITE_INPUT_ROOT` env var or CWD-relative allowlist. |
| ENG-005/QA-206 | Minor | S | Engineering | `CostCap.from_env()` raises raw `ValueError` on bad env var. Catch and re-raise with actionable message. |
| ENG-006 | Minor | S | Engineering | `OpenAIProvider.default_model()` returns `"gpt-5.4"` — verify this model ID exists in OpenAI's production API. |
| ENG-007 | Minor | S | Security | Secrets scan regex `sk-[A-Za-z0-9]{20,}` misses Anthropic key format. Fix to `sk-[A-Za-z0-9_-]{20,}` or adopt `gitleaks`. |
| UX-203 | Major | S | UX | Approve output missing promoted artifact paths. Add `kernel_dir` + `promoted_count` to JSON. |
| UX-205/DOC-204 | Major | S | Doc/UX | Standardize `trust_risk` (underscore) everywhere — README MCP config blocks use hyphen form. |
| UX-206/DOC-203 | Major | S | Doc/UX | Replace stale "v0.8 Next Agent" roadmap card with v1.0.2/v1.1.x items from CHANGELOG `[Unreleased]`. Update README Status section. |
| UX-207 | Minor | S | UX | `--quiet` help text leaks internal audit IDs (`UX-006/QA-005`). |
| UX-208 | Minor | S | UX | `list-runs` only available on `trust_risk` and `cio`; set `has_list_runs=True` for all seven agents. |
| UX-209 | Minor | S | UX | Founder and Design agent subcommand help text is generic; add descriptive one-liners. |
| UX-210 | Minor | S | UX | Sample-output README references internal dev-report paths and audit vocabulary. |
| TEST-001 | Critical | M | Test | Decide: commit cassettes against real providers OR remove dead vcr scaffolding (11 skipifs + conftest.py fixture + vcrpy dev dependency). Either choice is honest; limbo is not. |
| TEST-002 | Major | L | Test | Add one live test per remaining six agents following `test_founder_live.py` pattern. |
| TEST-003 | Major | S | Test | Update `CONTRIBUTING.md` and `docs/test-coverage.md` test count to 782/785. Consider CI-generated badge. |
| TEST-004 | Major | S | Test | Measure current coverage floor, then add `--cov-fail-under=<floor>` to CI. Close the "will be considered for rc1" note in `docs/test-coverage.md`. |
| TEST-005 | Major | M | Test | SVG extractor in `test_readme_cli_invocations.py` is rich-format-specific with no unit tests. Add synthetic SVG fixture test. |
| DOC-205 | Major | S | Doc | Three documents have three different test counts. Update CONTRIBUTING and test-coverage.md to 782/785. |
| DOC-206 | Minor | S | Doc | Add `--quiet`, `AGENTSUITE_LLM_MAX_ATTEMPTS`, `AGENTSUITE_LLM_TIMEOUT_SECS` to README and USER-MANUAL config tables. |
| QA-207 | Minor | S | QA | Add `windows-latest` to test matrix so Windows backslash traversal tests run in CI. |
| ENG-008 | Nit | S | Engineering | Move inline `import os/sys/time` in `base_agent.py` to module top level. |

---

## Blast-Radius Alerts

Changes in v1.0.2 that will touch shared code — flag for regression testing:

1. **`validate_run_id` propagation to MCP tools** — touches all 7 agents' `mcp_tools.py`. Run full `pytest tests/unit/agents/` after. Add a shared helper in `agentsuite/agents/_common.py` to avoid 7-way copy-paste of the validation call.

2. **`_make_approve_fn` refactor (UX-201 fix)** — shared closure used by all 7 agents' approve commands. A logic error here breaks every agent's approval workflow. Test all seven agents' approval paths after.

3. **Delete `docs/USER-MANUAL.md`** (DOC-202) — updating inbound links in `docs/index.html` and `README.md`. Verify GitHub Pages serves the replacement link correctly after push. Check for any other files that link to `docs/USER-MANUAL.md`.

4. **AgentCLISpec `next_step_hint` field** (UX-202) — adds a new field to the shared data class. Any test that asserts `AgentCLISpec` structure will need updating. Check `tests/unit/test_cli.py` and `tests/unit/agents/*/test_agent.py` for spec assertions.

5. **Coverage floor gate** (TEST-004) — adding `--cov-fail-under` to CI will block if any PR drops below the floor. Establish the floor from the current measured value, not a guess.

---

## Honest Disclosure

This post-ship audit found more issues than the pre-ship closure audit. That's expected and correct: the closure audit asked "did the sprint fix what it said it fixed?" — this audit asked "what does the shipped product look like from the outside?" Different questions produce different findings. The pre-ship closure audit ran against a candidate build; this audit ran against the shipped tag with fresh eyes in each role.

The security findings (ENG-001/002) are the most important output of this audit. They do not represent new vulnerabilities introduced in v1.0.1 — they represent the blast radius of the original ENG-001 fix not being fully traced. The fix was correct at the kernel layer. The MCP layer just wasn't included in the sweep.

The test infrastructure finding (TEST-001) is the most structurally interesting: the suite is honest, disciplined, and well-organized, but the "integration" label implies capabilities (real HTTP replay) that don't exist. The team should make a deliberate architectural decision rather than leaving the scaffolding in place as an implied promise.
