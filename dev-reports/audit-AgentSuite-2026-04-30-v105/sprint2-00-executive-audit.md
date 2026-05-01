# Executive Audit — AgentSuite v1.0.7 Sprint 2

**Audit date:** 2026-04-30
**Audit scope:** Scoped — Sprint 2 changes only (commit eb9c175 vs base 63d844f; 20 Major findings fixed)
**Posture:** Balanced
**Roles engaged:** Principal Engineer, Senior UI/UX Designer, Technical Writer, Test Engineer, QA Engineer

---

## Executive summary

Sprint 2 delivered its stated mandate — 20 Major findings fixed across kernel extraction, security, developer experience, cost reporting, and documentation — and the core fixes are correct. The kernel extraction (ENG-003) is architecturally clean: 14 thin wrappers with zero leaked business logic, and the `QAStageConfig`/`SpecStageConfig` dataclasses are a solid foundation. The developer-experience improvements (cost noise suppressed, `awaiting_approval` status label, actionable error messages) work consistently across all 7 agents. However, Sprint 2 introduced three new issues that need attention: a security gap where `_read_voice_samples` in the Founder agent reads user-supplied paths without calling the newly-added `check_path_confinement()` helper — an MCP-reachable file exfiltration path; a Gemini cost/model reporting mismatch where the cost is calculated with the request model alias but reported under the API-returned version string; and a broken cleanroom script when invoked directly (the ENG-002 production guard fires because `PYTEST_CURRENT_TEST` is only present when the cleanroom is invoked through pytest, not when the script is run standalone). The CIO agent also has two silent filename bugs: `agentsuite_cio_get_qa_scores` reads a file that never exists, and `agentsuite_cio_approve` points to a QA report file the CIO agent explicitly does not write.

---

## Readiness at a glance

| Dimension | Status | Summary |
|---|---|---|
| Architecture & code | Concerns | Kernel extraction is clean; security advisory-only enforcement and CIO filename bugs are live issues |
| UI / UX | Solid | 7-agent consistency achieved; two Majors (silent empty list_runs, CLI/MCP shape mismatch) need next sprint attention |
| Documentation | Concerns | Version sync nearly complete but README missed; DOC-003 fix left ConsistencyCheckFailed in Troubleshooting and Glossary; breaking-change under-documented |
| Test suite | Solid | New test additions are methodical; two Major gaps (no delegation test for 14 thin wrappers, fragile revision cycle key coupling) |
| Runtime QA | Concerns | Cleanroom broken in standalone mode; CIO QA scores and approval path always wrong for completed runs |

---

## Severity roll-up

| Severity | Count | What it means |
|---|---|---|
| Blocker | 0 | No blockers — sprint is not stopped |
| Critical | 3 | Fix this sprint: security gap, cost/model mismatch, cleanroom breakage |
| Major | 12 | Fix this or next sprint |
| Minor | 14 | Batch for hygiene work |
| Nit | 9 | Preference-level; flag once |
| **Total** | **38** | Two findings are confirmed cross-role (counted independently per role) |

---

## Top 10 findings

| # | ID | Severity | Role | Title | Blast |
|---|---|---|---|---|---|
| 1 | ENG-S2-001 | Critical | Engineering | `_read_voice_samples` reads user paths without `check_path_confinement()` | MCP-reachable data exfiltration: any file readable by the AgentSuite process can be sent to the LLM |
| 2 | ENG-S2-002 | Critical | Engineering | Gemini cost uses request model alias, reports API-returned `model_version` | Cost summary shows wrong model identifier; cost cap math may silently miscalculate when API routes to sub-version |
| 3 | QA-S2-001 | Critical | QA | ENG-002 guard breaks cleanroom when script is run directly | Pre-push gate fails with RuntimeError for any dev running `./scripts/run-cleanroom.sh` outside of pytest |
| 4 | ENG-S2-003 / QA-S2-002 | Major | Eng + QA | CIO `get_qa_scores` reads `qa-scores.json` (hyphen); kernel writes `qa_scores.json` (underscore) | Tool always returns "scores not yet available" — CIO QA approval gate defeated |
| 5 | QA-S2-003 | Major | QA | CIO `approve` returns `qa_report_path` pointing to `qa_report.md`, which CIO never writes | Operator cannot find QA feedback after a CIO revision-required response |
| 6 | DOC-S2-002 | Major | Docs | DOC-003 fix incomplete: `ConsistencyCheckFailed` remains in Troubleshooting (§10) and Glossary | Users following Section 10 or the Glossary get wrong recovery instructions |
| 7 | DOC-S2-003 | Major | Docs | Five Sprint 2 behaviors undocumented, including the `awaiting_approval` breaking change | Scripts checking `status == "approval"` break silently on upgrade with no doc warning |
| 8 | DOC-S2-001 | Major | Docs | README.md version badge stuck at v1.0.6 | Integrators checking README may miss the breaking-change status rename |
| 9 | TEST-S2-001 | Major | Test | No test verifies thin-wrapper delegation to kernel stages (14 wrapper files) | Config-construction bug in any of 14 files ships undetected until runtime |
| 10 | UX-A01 | Major | UX | `list_runs` returns silent `[]` when `project_slug` filter matches nothing | Developer cannot distinguish wrong slug from no-runs-yet; discovery friction for new integrators |

---

## Cross-role findings

### Cross-1 — CIO qa_scores.json filename mismatch
- **Surfaced in:** ENG-S2-003 (Major, Engineering), QA-S2-002 (Major, QA)
- **What it is:** The kernel writes `qa_scores.json` (underscore, `kernel/stages/qa.py:121`). The CIO MCP tool `agentsuite_cio_get_qa_scores` reads `qa-scores.json` (hyphen, `cio/mcp_tools.py:198`). The same bug exists in `trust_risk/mcp_tools.py:194`. Both files are always missing, so both tools always return "scores not yet available."
- **Why this matters most:** MCP clients use this tool to decide whether to approve a run. It silently lies for every completed run.
- **Blast radius:** Fix two files (`cio/mcp_tools.py` line 198, `trust_risk/mcp_tools.py` line 194). No schema changes needed. Update any tests that assert the "not yet available" response for completed runs.
- **Recommended approach:** Fix both files in a single commit. Add a test that completes a run and calls `get_qa_scores`, asserting non-null scores.

### Cross-2 — CIO agent behavior divergence has no structural contract
- **Surfaced in:** ENG-S2-003 (Major, Engineering), QA-S2-002 (Major, QA), QA-S2-003 (Major, QA), TEST-S2-004 (Minor, Test)
- **What it is:** The CIO agent has genuinely different behavior from the other six: `write_qa_report=False`, bare-stem artifact keys, 10 MCP tools vs 5, and a different QA output shape. The MCP tools were written without checking what files CIO actually writes. Three findings trace to this root cause.
- **Why this matters most:** The CIO agent is the most complex and the one most likely to have more divergence added. Each new sprint will re-encounter this problem without a shared contract.
- **Recommended approach:** Add a per-agent `WRITTEN_FILES` contract (either a constant list or an agent capability flag) that MCP tools and test helpers consult when constructing file paths and error messages. This prevents the next sprint from introducing a fourth CIO divergence.

### Cross-3 — `_stage_to_status()` duplication without single source of truth
- **Surfaced in:** UX-A04 (Minor, UX), QA-S2-006 (Nit, QA)
- **What it is:** The 4-line `_stage_to_status()` function is identically duplicated across all 7 `agent.py` files. Sprint 2 added a new stage mapping — if the next sprint adds another, it requires touching 7 files. One agent getting missed produces user-visible status inconsistency.
- **Recommended approach:** Move to `agentsuite/kernel/base_agent.py` and import in each agent module (7 one-line import changes). See UX-A04 fix path.

### Cross-4 — Path confinement advisory-only enforcement
- **Surfaced in:** ENG-S2-001 (Critical, Engineering — voice_samples gap), ENG-S2-004 (Major, Engineering — systemic enforcement), TEST-S2-003 (Minor, Test — symlink not tested)
- **What it is:** `check_path_confinement()` was introduced in Sprint 2 with a "must call this" docstring. Within Sprint 2 itself, the function was not called in `_read_voice_samples` — the one spec-stage location where user paths are read directly to the LLM. The structural fix (enforce at intake, not at read) would close all current and future gaps by construction.
- **Recommended approach:** Add `check_path_confinement` calls at each agent's intake stage when paths are first accepted, so the manifest contains only pre-validated paths. The immediate fix (ENG-S2-001) is to call it in `_read_voice_samples`. The systemic fix (ENG-S2-004) is to move enforcement to intake.

---

## What's working

- **Engineering — Kernel extraction (ENG-003) is clean.** All 14 agent stage files are genuine thin wrappers with zero business logic leaked. `QAStageConfig` and `SpecStageConfig` cover all behavioral variation without inheritance. Import direction is clean — no cycles. This is the sprint's most significant architectural win.
- **Engineering — `check_path_confinement()` itself is correct.** The function calls `path.resolve()` before `is_relative_to(project_dir.resolve())`, which handles `..` traversal, absolute paths, and symlinks correctly. The CIO MCP `get_artifact` tool demonstrates correct usage (line 171). The fix is called in the right shape — it just needs to be called in more places.
- **UX — 7-agent consistency achieved.** The `awaiting_approval` rename, `project_slug` filter, `$0.0000` suppression, and UnknownAgent error messages are consistently applied across all 7 agents with identical code. No agent diverged.
- **Documentation — DOC-003 error tables are fully updated.** All 7 per-agent error tables correctly redirect users to `consistency_report.json`. The fix is clean and consistent in phrasing across all chapters.
- **Tests — TEST-002 SequentialMockLLMProvider coverage is comprehensive.** 25 tests cover the full behavioral contract: sequential ordering, repeat-last, reinstantiation reset, longest-match-first, system-field matching. Zero skipped tests found across all Sprint 2 test files.
- **Tests — TEST-004 revision cycle tests are genuine integrations.** The 7 revision cycle tests exercise the full FounderAgent pipeline (real stage wiring, mock LLM only) and assert on cost accumulation, file promotion, and QA report content at the right checkpoints.
- **Runtime QA — Cost and error paths behave correctly.** `QA-003` `ValueError` propagates before any LLM call. `QA-004` `getattr` fallback is correct. `QA-005` exits cleanly with code 1 and a useful message. `UX-004` `_stage_to_status()` handles all current `Stage` literal values correctly.

---

## This-sprint punch list (summary)

**Must-fix (all Criticals):** 3 items
1. **ENG-S2-001** — Call `check_path_confinement()` before `read_text()` in `founder/stages/spec.py:_read_voice_samples`
2. **ENG-S2-002** — Use same model value for both `LLMResponse.model` and `_cost_usd()` in `gemini.py`
3. **QA-S2-001** — Add `AGENTSUITE_ALLOW_MOCK_FACTORY=1` guard to `cli.py` and export it in `run-cleanroom.sh` mocked block (or export `PYTEST_CURRENT_TEST` in the script)

**Should-fix (high-leverage Majors):** 6 items
4. **ENG-S2-003/QA-S2-002** — Change `qa-scores.json` → `qa_scores.json` in `cio/mcp_tools.py:198` and `trust_risk/mcp_tools.py:194`
5. **QA-S2-003** — Update CIO `agentsuite_cio_approve` RevisionRequired response to reference `qa_scores.json` instead of `qa_report.md`
6. **DOC-S2-001** — Update README.md version badge from v1.0.6 to v1.0.7
7. **DOC-S2-002** — Fix `ConsistencyCheckFailed` in USER-MANUAL.md §10 (Troubleshooting) and Glossary
8. **DOC-S2-003** — Document `awaiting_approval` breaking change and new AGENTSUITE_COST_CAP_USD error in USER-MANUAL.md + troubleshooting.md
9. **DOC-S2-004** — Merge duplicate `### Fixed` sections in CHANGELOG [1.0.7]; add `### ⚠ BREAKING` header for the status rename

Full detail in `sprint2-sprint-punchlist.md`.

---

## Next-sprint watchlist (summary)

- **ENG-S2-004** — Path confinement structural enforcement at intake (fix all current + future gaps by construction)
- **TEST-S2-001** — Add thin-wrapper delegation tests for 14 kernel stage wrapper files
- **TEST-S2-002** — Decouple revision cycle test key from hardcoded QA system_msg string
- **UX-A01** — Add context envelope to `list_runs` response when `project_slug` filter matches nothing
- **UX-A02** — Add `started_at` to CLI `list-runs` output to match MCP `RunSummary` shape
- **UX-A04 / QA-S2-006** — Consolidate `_stage_to_status()` into kernel shared module
- **QA-S2-002 blast radius** — Establish a CIO/trust_risk file-path contract to prevent future filename divergence
- **ENG-S2-008** — Add `frozen=True` to `QAStageConfig` and `SpecStageConfig` dataclasses

Full detail in `sprint2-next-sprint-watchlist.md`.

---

## Blast-radius callouts

- **ENG-S2-001** — Adding `check_path_confinement()` to `_read_voice_samples` is additive; existing legitimate calls unaffected. Tests that supply out-of-project paths will need to supply valid project-relative ones.
- **ENG-S2-002** — The `_cost_usd()` fix in `gemini.py` may surface a KeyError if the pricing table doesn't cover API-returned sub-version strings (e.g., `gemini-2.5-flash-preview-04-17`). Confirm `GEMINI_PRICING` keys cover these before shipping.
- **QA-S2-001** — The `AGENTSUITE_ALLOW_MOCK_FACTORY` approach adds a new env var to the public interface. If Option B (export `PYTEST_CURRENT_TEST` in the script) is chosen instead, no new env var is needed — but check that the cleanroom's bash subprocess correctly inherits the value across all platforms.
- **ENG-S2-003/QA-S2-002** — Any existing test that asserts `get_qa_scores` returns "not yet available" for a completed run is asserting the broken behavior. Those tests must be updated to expect real scores.
- **DOC-S2-003** — The `awaiting_approval` breaking change documentation should include a migration snippet for scripts: `if status in ("approval", "awaiting_approval"):` as a transitional check.

---

## What we couldn't assess

- **Live Gemini API `model_version` attribute shape** — All five roles confirmed the `getattr` fallback is safe, but whether the Gemini SDK actually populates `model_version` on live responses requires a live API call. The fix for ENG-S2-002 should be verified against a real Gemini run.
- **Runtime cleanroom on direct script invocation** — QA's finding (QA-S2-001) is based on static analysis. The session context confirms the cleanroom ran GREEN via `pytest -m cleanroom` (where `PYTEST_CURRENT_TEST` is inherited). The finding is that running `./scripts/run-cleanroom.sh` directly (without pytest) fails. This was not live-verified in this audit pass.
- **Symlink traversal behavior on Windows NTFS** — `check_path_confinement()` uses `path.resolve()` which follows symlinks on POSIX. Windows junction points may behave differently on some Python versions. Test on Windows before declaring the path confinement fix complete for cross-platform use.
- **CI run history / flakiness** — Test pass/fail is inferred from reading test bodies. No CI run logs were accessed.

---

## Recommended next actions

1. **Fix the three Criticals this sprint** — ENG-S2-001 (voice_samples path confinement gap) and QA-S2-001 (cleanroom breakage) are the highest-priority. ENG-S2-002 (Gemini cost/model mismatch) requires confirming the pricing table covers API-version strings first.
2. **Fix the CIO dual filename bugs in a single commit** — ENG-S2-003/QA-S2-002 (qa_scores.json) and QA-S2-003 (approve qa_report_path) are both CIO-only, trivial to fix, and high-impact. Do them together.
3. **Complete the documentation sweep before the next push** — DOC-S2-001/002/003/004 are all < 1 hour of work total. The breaking-change documentation (DOC-S2-003) is the highest risk for downstream integrators.
4. **Plan the kernel delegation tests (TEST-S2-001) for Sprint 3** — 14 thin wrapper files have no delegation test. This is a structural gap that will hide config-construction bugs as the kernel evolves.
5. **Design the CIO/trust_risk file-path contract** — The three CIO-divergence findings in this audit all trace to the same root cause. A one-time design of a per-agent `WRITTEN_FILES` or capability manifest closes this class of bug permanently.

---

## Reference — role deep-dives

- `sprint2-01-engineering-deepdive.md` — Principal Engineer
- `sprint2-02-uiux-deepdive.md` — Senior UI/UX Designer
- `sprint2-03-documentation-deepdive.md` — Technical Writer
- `sprint2-04-test-deepdive.md` — Test Engineer
- `sprint2-05-qa-deepdive.md` — QA Engineer

---

*Audit conducted by the audit-team skill on 2026-04-30. Scope: Sprint 2 changes only (eb9c175 vs 63d844f). Findings are balanced and evidence-based. All Criticals include reproduction details and blast-radius entries in the deep-dives.*
