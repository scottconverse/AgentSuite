# Executive Audit — AgentSuite v1.0.2-dev (Post-Sprint, Inline Five-Role)

**Date:** 2026-04-30  
**Codebase state:** commit 16cebe8 (post-sprint, all 8 v1.0.1 audit punchlist items closed)  
**Audit mode:** Inline — orchestrator personally performed all five roles, no subagents  
**Test suite:** 786 passed, 0 failed, 0 skipped, 3 deselected. ruff clean. mypy --strict clean.

---

## Executive Summary

AgentSuite v1.0.2-dev sits on a solid foundation: 786 passing tests, mypy-strict, atomic state writes, content-addressed artifacts, and a security-aware path validation layer that now centralizes its checks in `agentsuite/agents/_common.py`. The closed sprint genuinely fixed all 8 punchlist items from the post-ship v1.0.1 audit — the engineering, UX, and documentation tiers all measurably improved.

The audit surfaces 5 new Critical findings, all clustered around the same root cause: **blast-radius gaps**. The same pattern that produced ENG-001 in v1.0.0 ("validation added to one path, not all") has now appeared again with `RunStateSchemaVersionError` — caught in `agentsuite_cost_report` (the specific punchlist item) but not in the 9 `list_runs` iteration sites or 14 `get_status` single-run sites that have the same vulnerability. The fix is mechanical and the pattern is already established by the existing fix; what's missing is the discipline to sweep the general pattern, not just the specific finding.

Two of the five Criticals are documentation-tier (USER-MANUAL stuck at v0.9.1; package version not bumped to match CHANGELOG). They block clean release messaging more than runtime function.

The work is not done, but it is not far from done. With the punch list below, v1.0.2 ships clean.

---

## Severity Roll-Up

| Severity | Engineering | UX | Documentation | Test | QA | **Total** |
|----------|:-----------:|:--:|:-------------:|:----:|:--:|:---------:|
| Blocker  | 0 | 0 | 0 | 0 | 0 | **0** |
| Critical | 2 | 0 | 1 | 2 | 2 | **7** (5 unique findings) |
| Major    | 0 | 1 | 2 | 2 | 0 | **5** |
| Minor    | 3 | 2 | 2 | 1 | 2 | **10** |
| Nit      | 1 | 1 | 0 | 0 | 0 | **2** |

Cross-referenced findings (counted once in unique total):
- **QA-301** (RunStateSchemaVersionError in list_runs) — surfaced by Engineering, Test, QA
- **QA-302** (RunStateSchemaVersionError in get_status) — surfaced by Engineering, Test, QA
- **DOC-301** (USER-MANUAL stale version) — Documentation only
- **DOC-302** (version skew) — Documentation, Engineering
- **ENG-102 / DOC-305 / QA-303** (`agentsuite migrate` ghost command) — three roles, one finding
- **DOC-303** (`_common.py` not in CONTRIBUTING) — Documentation only

---

## Top Findings (Ranked)

### 1. QA-301 — `RunStateSchemaVersionError` unhandled in list_runs (Critical)
**Surfaced by:** Engineering, Test Engineer, QA Engineer  
**Impact:** `agentsuite list-runs`, `agentsuite founder list-runs`, and all 7 MCP `{agent}_list_runs` tools crash unhandled if any pre-v0.9 run dir exists in the workspace. Day-1 upgrade failure.  
**Fix path:** Wrap `StateStore.load()` in `try/except RunStateSchemaVersionError` at 9 sites — same pattern already correct in `agentsuite_cost_report`.

### 2. QA-302 — `RunStateSchemaVersionError` unhandled in get_status (Critical)
**Surfaced by:** Engineering, Test Engineer, QA Engineer  
**Impact:** Single-run `get_status` queries against pre-v0.9 dirs propagate raw `RuntimeError` to MCP callers instead of an actionable message.  
**Fix path:** Same pattern, applied to `{agent}_get_status` / `get_run_status` and the extended trust_risk/cio tools.

### 3. DOC-301 — USER-MANUAL.md version 0.9.1 (Critical)
**Surfaced by:** Technical Writer  
**Impact:** Primary non-developer user doc shows a 3-versions-stale badge; readers immediately distrust its content.  
**Fix path:** Update version line; sweep manual for procedures affected by `--force`, `--quiet`, `--latest` flags added since 0.9.1.

### 4. DOC-302 / ENG-103 — Version skew between CHANGELOG and package (Major→Critical class)
**Surfaced by:** Documentation, Engineering  
**Impact:** CHANGELOG declares `[1.0.2] - Unreleased` while `pyproject.toml`, `__version__.py`, and README all say 1.0.1. The package self-reports a contradiction.  
**Fix path:** Bump all three to 1.0.2 in the same commit as the fixes.

### 5. UX-301 — Next-step hint placeholders break copy-paste (Major)
**Surfaced by:** UX Designer  
**Impact:** The new approve hint says `--approver <your-name> --project-slug <slug>`. Users copy-pasting get a CLI error on their first interaction with `approve`.  
**Fix path:** Replace `<your-name>` and `<slug>` with `YOUR_NAME` and `YOUR_SLUG` (uppercase, shell-safe).

### 6. DOC-303 — `_common.py` undocumented in CONTRIBUTING.md (Major)
**Surfaced by:** Technical Writer  
**Impact:** New contributors will repeat the unsafe raw path construction pattern.  
**Fix path:** Add "Security: path validation" section to CONTRIBUTING.md.

### 7. TEST-301 / TEST-302 — No tests for the QA-301 / QA-302 fixes (Critical)
**Surfaced by:** Test Engineer  
**Impact:** Without tests, the QA-301/QA-302 fixes are not verifiable. A future refactor could re-introduce the bug without detection.  
**Fix path:** Mirror the test pattern used in `test_cost_report_skips_schema_version_mismatch_dirs`.

### 8. ENG-102 / DOC-305 / QA-303 — `agentsuite migrate` ghost command (Minor, but concentrated)
**Surfaced by:** Engineering, Documentation, QA  
**Impact:** Warning at `mcp_server.py:133` directs users to a nonexistent command at exactly the moment they're already in a degraded state.  
**Fix path:** Replace with "delete {run_dir} and re-run" — already the language used by the underlying `RunStateSchemaVersionError`.

### 9. TEST-303 — No dedicated `test_common.py` (Major)
**Surfaced by:** Test Engineer  
**Impact:** The `_common.py` helpers are tested only indirectly via `test_mcp_server.py`. Edge cases (boundary lengths, single-char IDs, dot-in-middle) untested.  
**Fix path:** Create `tests/unit/agents/test_common.py` with parametrized boundary tests.

### 10. ENG-101 / QA-304 — `{agent}_run` result path bypasses `require_run_dir` (Minor)
**Surfaced by:** Engineering, QA  
**Impact:** Safe today (`ArtifactWriter` validates first) but inconsistent pattern. Future copy-paste risks an unvalidated path.  
**Fix path:** Standardize to `run_dir = require_run_dir(output_root_fn, run_id)` after `agent.run()`.

---

## What's Working Well

- **Sprint discipline.** All 8 punchlist items from the v1.0.1 post-ship audit were closed correctly — verified by tests, ruff, mypy, and code path tracing. The fixes themselves are sound; the gaps are in scope-of-sweep, not in correctness of the applied fix.
- **`_common.py` is exemplary.** Small (41 lines), single-purpose, well-documented, and already wired into all 7 agents' get_status/resume/approve/stage tools. The module docstring explicitly states the invariant ("validate before path construction") so future maintainers can reason about its purpose without inferring intent.
- **Test architecture.** Four tiers (unit, integration, golden, cross-cutting). Mock-based pipeline tests + golden snapshots + mypy integration test + traversal probes + schema version probes. 786 tests with 0 skips is real, not theatrical.
- **Type discipline.** mypy --strict on 121 source files passes clean. The `Callable` typing fix that the UX-202 wrapper required was non-trivial but solved correctly via factory function.
- **Provider-agnostic LLM layer.** Anthropic / OpenAI / Gemini / Ollama all routed through a common Protocol. `RetryingLLMProvider` wraps each. `ProviderNotInstalled` gives an actionable install command.
- **Atomic state persistence.** `StateStore.save()` uses tempfile + fsync + os.replace. Crashed mid-write never corrupts existing state.
- **CHANGELOG quality.** The `[1.0.2] - Unreleased` entry is detailed, categorized, and explains the *why* of each fix — not just the what.

---

## This-Sprint Punch List

See [`sprint-punchlist.md`](sprint-punchlist.md) for the actionable list. Summary:

| # | Item | Type | Severity |
|---|------|------|:--------:|
| 1 | Wrap `list_runs` `StateStore.load()` in try/except (9 sites) | ENG/QA | Critical |
| 2 | Catch `RunStateSchemaVersionError` in `get_status` (14 sites) | ENG/QA | Critical |
| 3 | Add tests for QA-301 / QA-302 | TEST | Critical |
| 4 | Bump version 1.0.1 → 1.0.2 in all 3 files | DOC/ENG | Major |
| 5 | Fix next-step hint placeholders | UX | Major |
| 6 | Replace `agentsuite migrate` ghost reference | DOC/ENG/QA | Minor |
| 7 | Update USER-MANUAL.md version + flags | DOC | Critical |
| 8 | Document `_common.py` in CONTRIBUTING.md | DOC | Major |
| 9 | Create `tests/unit/agents/test_common.py` | TEST | Major |

---

## Next-Sprint Watch List

See [`next-sprint-watchlist.md`](next-sprint-watchlist.md). Headline items:

- **W-01: Blast-radius discipline.** Three consecutive sprints have shipped fixes scoped to the specific finding rather than the general pattern. This is the systemic issue. Adopt a "grep for the pattern" sprint-closure step.
- **W-08: Per-agent `mcp_tools.py` duplication.** 90% of code in 7 files is identical. Extracting `register_standard_tools()` reduces 7-fold maintenance to 1-fold and makes blast-radius sweeps mechanical.
- **W-09: SECURITY.md.** Three path-traversal fixes shipped; no responsible-disclosure policy exists yet.
- **W-04: Windows promote() atomicity.** Latent bug; not a runtime failure today, but real on disk.

---

## Blast-Radius Notes (Critical for the Dev Team)

**The QA-301 / QA-302 fixes have an interlock with the test additions.** Do not land the code fixes without the corresponding tests, or the next sprint will be unable to detect a regression. The pattern is:

1. Add the `try/except RunStateSchemaVersionError` to the 9 + 14 sites
2. Add a parametrized test that creates a pre-v0.9 state file and invokes each affected entry point
3. Verify the new tests fail before the code fix and pass after

This is not optional. The audit explicitly identified the test gap (TEST-301, TEST-302) for this exact reason.

**The version bump (DOC-302, ENG-103) must touch all three sources in one commit:** `pyproject.toml`, `agentsuite/__version__.py`, `README.md`. Don't split across commits — the package self-reports inconsistency between the bump commits.

**The next-step hint fix (UX-301) is in 7 files** — `agentsuite/agents/*/agent.py`. Same string format in each. Sweep all 7, not just one.

---

## Auditor's Honest Assessment

The codebase is in a strong place. The team executed an 8-item sprint correctly, with verifiable evidence (tests, lint, type checks). What this audit reveals is not poor work — it's a recurring pattern in *how* the work is scoped: fixes are landing on the specific finding while the general pattern continues to hide in adjacent call sites. This pattern was visible in v1.0.0 → v1.0.1 (ENG-001 blast-radius miss). It's now visible again in v1.0.1 → v1.0.2 (RunStateSchemaVersionError). The same root cause that the user explicitly asked about — "Why wasn't it fully swept?" — is the same root cause this audit surfaces in different code.

The mechanical fix for the next round is small. The behavioral fix (sweep the pattern, not just the finding) is what makes v1.0.3 the last sprint that has this class of finding.

The bar from the audit-team commitment: every Critical/Major finding has evidence (file paths, line numbers, code excerpts), blast radius, and a concrete fix path. The dev team can pick up any finding and start working immediately. Confirmed.

---

## Files in This Audit Package

- `00-executive-audit.md` — this file
- `01-engineering-deepdive.md` — Principal Engineer findings (ENG, QA-301/302)
- `02-uiux-deepdive.md` — UI/UX Designer findings (UX)
- `03-documentation-deepdive.md` — Technical Writer findings (DOC)
- `04-test-deepdive.md` — Test Engineer findings (TEST)
- `05-qa-deepdive.md` — QA Engineer findings (QA)
- `sprint-punchlist.md` — Actionable items for this sprint
- `next-sprint-watchlist.md` — Forward-looking architectural items
