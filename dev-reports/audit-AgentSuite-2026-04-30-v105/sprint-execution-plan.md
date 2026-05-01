# Sprint Execution Plan — AgentSuite Audit Remediation
**Date:** 2026-04-30  
**Scope:** All 57 findings from the five-role audit of v1.0.5  
**Structure:** 4 sprints (Critical → Major → Minor → Nit)  
**Loop per sprint:** implement → e2e mock tests → audit-lite → fix if needed → commit/push → /audit-team → fix → commit/push → next sprint

---

## Cross-Dependency Analysis

Before touching anything, these ordering constraints must hold.

### Hard ordering constraints (violating these creates cascading breakage)

**1. ENG-003 before ENG-004 (within Sprint 2)**  
ENG-003 extracts the 7x duplicated stage handlers into shared kernel helpers. ENG-004 (unconfined file reads in extract/spec stages) requires touching those same 7×2 files. If ENG-003 runs first, ENG-004 becomes a single-file kernel fix instead of a 14-file sweep. If we reverse the order, the ENG-004 fix has to be applied 7 times and then immediately moved during the ENG-003 refactor. Always: ENG-003 → ENG-004.

**2. ENG-003 must run SEQUENTIALLY (not parallel) — it is the anchor of Sprint 2**  
Every other Sprint 2 item can go parallel. ENG-003 cannot, because it restructures the files that almost everything else in Sprint 2 touches. The Sprint 2 plan is: ENG-003 first (sequential, verified), then everything else (parallel second wave).

**3. TEST-002 before TEST-004 (within Sprint 2)**  
TEST-004 (revision cycle E2E) uses `SequentialMockLLMProvider` as its test harness. TEST-002 (SequentialMockLLMProvider coverage) must be written and passing before TEST-004 is built on top of it. These can be in the same Sprint 2 second wave, but TEST-002 must complete before TEST-004 starts.

**4. UX-004 is a breaking change — CHANGELOG entry required**  
Changing `"status": "approval"` → `"status": "awaiting_approval"` in CLI JSON output breaks any shell scripts or CI pipelines that parse AgentSuite's stdout. This must include a CHANGELOG entry with explicit migration note. The fix itself is Sprint 2, but it must be flagged as a breaking change in the commit.

### Blast-radius zero strategy

**Sprint 1 (Criticals) — all independent, full parallelism safe:**
- ENG-001 only touches `cio/mcp_tools.py` + `trust_risk/mcp_tools.py`
- UX-002 touches `kernel/approval.py` + `cli.py` + all 7 agents' `mcp_tools.py` (approval handler only)
- QA-001 touches `llm/retrying.py` only
- TEST-001 touches `.github/workflows/test.yml` only
- DOC-002 touches `USER-MANUAL.md` only
- UX-001/DOC-005 touches `docs/index.html` only

No Sprint 1 fix touches the same file as another. Full parallelism, zero cascade risk.

**Sprint 2 (Majors) — one sequential gate, then parallel:**
The ENG-003 refactor is the only ordering constraint. After it lands and tests pass, all remaining Sprint 2 items are disjoint:
- ENG-002 → `cli.py` only
- ENG-004 → kernel (after ENG-003 extracts it)
- ENG-005 → `kernel/base_agent.py` + `kernel/cost.py`
- UX-003 → `kernel/base_agent.py` (same file as ENG-005 — coordinate or sequence)
- UX-004 → all 7 `agents/*/agent.py` (run_cmd output only)
- UX-006 → all 7 `agents/*/mcp_tools.py` (list_runs handler only)
- DOC-003 → `USER-MANUAL.md` (different section from Sprint 1's DOC-002 fix)
- DOC-004 → `CHANGELOG.md` (footer links only)
- TEST-002/003/004 → new test files only
- QA-003 → `kernel/cost.py`
- QA-004 → `llm/gemini.py`
- QA-005 → `cli.py` + `mcp_server.py`

**Coordination note for ENG-005 + UX-003:** Both touch `kernel/base_agent.py`. They must be sequenced or handled by a single subagent. Assign both to the same subagent in Sprint 2.

**Sprint 3/4 (Minor/Nit) — almost entirely independent.**
ENG-006/QA-007 are cross-role (same bug found twice). Fix once in `llm/json_extract.py`, counted once.

---

## Sprint 1 — Criticals

**Goal:** Fix all 6 Critical findings. Zero ordering constraints between them.

### Parallel streams (3 subagents, dispatched simultaneously):

**Stream A — Security (ENG-001)**  
Files: `agentsuite/agents/cio/mcp_tools.py`, `agentsuite/agents/trust_risk/mcp_tools.py`  
Work: Add allowlist or `pathlib` containment check for `artifact_name` / `template_name`. Add unit tests.  
Test gate: existing cio + trust_risk mcp_tools tests must pass; new traversal-rejection tests must pass.

**Stream B — Error Handling (UX-002 + QA-001)**  
Files: `agentsuite/kernel/approval.py`, `agentsuite/cli.py`, all 7 `agents/*/mcp_tools.py` (approve handler), `agentsuite/llm/retrying.py`  
Work:  
- UX-002: `cli.py` dedicated `except RevisionRequired` with qa_report path + re-run hint; each agent's `_approve` MCP tool catches and returns structured error JSON  
- QA-001: Add `anthropic.AuthenticationError`, `openai.AuthenticationError`, Gemini auth errors to `_NO_RETRY_EXCEPTIONS` using lazy imports  
Test gate: approval + retry unit tests pass; new auth-error-no-retry test passes.

**Stream C — CI + Docs (TEST-001 + DOC-002 + UX-001/DOC-005)**  
Files: `.github/workflows/test.yml`, `USER-MANUAL.md`, `docs/index.html`  
Work:  
- TEST-001: Add `tests/stress` to pytest invocation in CI yml  
- DOC-002: Fix USER-MANUAL version header (→ v1.0.5) and footer (→ v1.0.5)  
- UX-001/DOC-005: Update landing page badge (→ v1.0.5), replace stale roadmap section  
Test gate: CI yml syntax valid; version strings consistent.

### Sprint 1 test loop:
```
pytest --tb=short -q                    # full 908+ tests
pytest -m cleanroom                     # full mock pipeline E2E
# audit-lite (inline AUDITOR-RUN across Sprint 1 changes)
# fix if needed → commit → push
# /audit-team Sprint 1 scope
# fix if needed → commit → push
```

---

## Sprint 2 — Majors

**Goal:** Fix all 20 Major findings. One sequential gate (ENG-003), then parallel.

### Phase 2a — Sequential gate (must complete and pass tests before Phase 2b):

**ENG-003 — 7× Duplication Refactor**  
Files: `agentsuite/kernel/` (new shared helpers), all 7 `agents/*/stages/qa.py`, all 7 `agents/*/stages/spec.py`, all 7 `agents/*/stages/consistency_check.py` (if exists separately)  
Work: Extract shared `kernel_qa_stage()`, `kernel_spec_stage()` helpers. Each agent's stage becomes a thin wrapper.  
Test gate: **Full golden suite + full stress suite must pass before Phase 2b starts.** This is non-negotiable — any behavioral drift from the refactor must be caught here, not after 12 more parallel changes land.

### Phase 2b — Parallel (dispatched simultaneously after Phase 2a passes):

**Stream A — Security + Kernel (ENG-002 + ENG-004 + ENG-005 + UX-003 + QA-003)**  
ENG-005 and UX-003 both touch `base_agent.py` — assign to same subagent.  
- ENG-002: Add docstring warning + pytest-context guard to `AGENTSUITE_LLM_PROVIDER_FACTORY` in `cli.py`  
- ENG-004: Add path confinement check to kernel extract/spec helpers (post-ENG-003)  
- ENG-005/UX-003: Wire soft-warn to stderr in `base_agent._drive()`; clean up stage progress format  
- QA-003: Wrap `float(raw)` in `CostCap.from_env()` with actionable error message

**Stream B — CLI/MCP surface (UX-004 + UX-006 + QA-005 + ENG-002)**  
- UX-004: Add `_stage_to_status()` helper in shared `_common.py`; apply in all 7 `run_cmd` functions. CHANGELOG breaking change entry.  
- UX-006: Either implement `project_slug` filter (add field to `RunState`, filter at list time) OR remove the parameter and document. Lean toward implement — it's the right thing and `run_metadata.json` already has slug.  
- QA-005: Catch `UnknownAgent` in `cli.py:agents_cmd()` and `mcp_server.py:main()`; emit clean error.

**Stream C — Provider fixes (QA-004 + QA-001 retry tests)**  
- QA-004: In `llm/gemini.py`, use `getattr(result, 'model_version', None) or model` for LLMResponse model field  
- QA-001 new tests: Add retry unit tests for auth-error-no-retry (complement the Sprint 1 fix)

**Stream D — Documentation (DOC-003 + DOC-004)**  
- DOC-003: Replace `ConsistencyCheckFailed` entries in all 7 agent chapters of USER-MANUAL with correct v1.0.3+ behavior  
- DOC-004: Apply CHANGELOG footer links patch (patch file already in doc-rewrites/)

**Stream E — Test coverage (TEST-002 + TEST-003 + TEST-004)**  
Sequence within this stream: TEST-002 → TEST-004  
- TEST-002: Unit tests for `SequentialMockLLMProvider` (cycle, exhaust, reset, edge cases)  
- TEST-003: Create `test_mcp_tools.py` for engineering, marketing, trust_risk, cio  
- TEST-004: Integration test for revision cycle using SequentialMockLLMProvider

### Sprint 2 test loop:
```
pytest --tb=short -q                    # must hit 920+ tests (new tests added)
pytest -m cleanroom                     # full pipeline E2E
# audit-lite
# fix if needed → commit → push
# /audit-team Sprint 2 scope
# fix if needed → commit → push
```

---

## Sprint 3 — Minors

**Goal:** Fix all 19 Minor findings. Almost entirely independent.

### Parallel streams (4 subagents):

**Stream A — Kernel/LLM code fixes**  
- ENG-006/QA-007: Fix `extract_json` rfind fallback (cross-role, fix once in `llm/json_extract.py`)  
- ENG-007: Add validation for zero/negative `hard_kill_usd` in `CostCap.from_env`  
- ENG-008: Clean up `AgentRegistry.get_class` dead guard + env re-read  
- ENG-009: Remove `httpx` from `pyproject.toml` dependencies  
- ENG-010: Refactor `_default_mock_for_cli` into lazy per-agent builder pattern  
- ENG-011: Fix `qa-scores.json` → `qa_scores.json` typo in cio mcp_tools (hyphen → underscore)  
- QA-006: Add `min_length=1` to `business_goal` + other required free-text fields  
- QA-008: Include `qa_report.md` path in `RevisionRequired` exception message

**Stream B — CLI/UX copy fixes**  
- UX-007: Fix CLI help string to use Unicode `→` and em-dash  
- UX-008: Add `AGENTSUITE_COST_CAP_USD` to `agentsuite-mcp --help` env var table  
- UX-009: Add `[WARN]` / `[SKIP]` prefix to pre-v0.9 run dir skip messages  
- UX-010: Rename `all_registered` → `registered` in `agentsuite agents` JSON output + MCP (minor breaking change, note in CHANGELOG)

**Stream C — Doc fixes**  
- DOC-006: Update CONTRIBUTING.md test count (688 → 892; 691 → 895)  
- DOC-007: Update README Status/Roadmap section to reflect v1.0.5  
- DOC-008: Fix `--design-brief` → `--campaign-goal` in Design Agent error table  
- DOC-010: Standardize `trust_risk` vs `trust-risk` across all docs (decide canonical form)  
- DOC-011: Fix landing page MCP install snippet to use `[mcp]` extra form

**Stream D — Test improvements**  
- TEST-005: Remove VCR cassette infrastructure OR record one cassette (prefer: record one for founder to deliver original intent)  
- TEST-006: Add one live test per remaining 6 agents (gated behind `RUN_LIVE_TESTS=1`)  
- TEST-007: Add scope comment to `tests/golden/_helpers.py` clarifying mock-LLM vs real-LLM scope

### Sprint 3 test loop: same pattern as above.

---

## Sprint 4 — Nits

**Goal:** Fix all 12 Nit findings.

### Parallel streams (3 subagents):

**Stream A — Code hygiene**  
- ENG-012: Move lazy stdlib imports to module top in `base_agent.py`  
- ENG-013: Annotate `DEFAULT_ENABLED` as comma-separated or convert to list  
- ENG-014: Update stale "frozen for v0.9.0" comment in `cost.py`  
- TEST-009: Add longest-match-first test to `test_mock.py`

**Stream B — Makefile + CI**  
- TEST-008: Add `test-stress` target to Makefile, include in default `test` target

**Stream C — Help text + doc nits**  
- DOC-009: No action (CHANGELOG historical entry — do not retroactively edit)  
- QA-009: Standardize `trust-risk` form in `agentsuite-mcp --help`  
- QA-010: Improve `--project-slug` help text to explain `_kernel/` path

### Sprint 4 test loop: same pattern.

---

## Visibility protocol (applies every sprint)

To maintain clear view without losing control:

1. **Announce every dispatch** with a one-line summary of what each subagent will do and which files it will touch.
2. **Narrate every return** — what the subagent did, whether tests pass, any surprises.
3. **No wave 2 dispatches until wave 1 results are read and narrated.**
4. **Phase 2a (ENG-003) is a hard synchronization point** — no parallel work starts until the golden+stress suite passes on the refactored code.
5. **If a subagent returns a test failure, stop the sprint and fix before proceeding.**

---

## Audit-lite definition

"/audit-lite" = inline AUDITOR-RUN (not the full 5-role skill ceremony). After each sprint's fixes:
- Review the changed files against the sprint's target findings
- Run `grep` passes to verify fixes are complete and consistent
- Check for regressions in adjacent code
- Produce a short "fixed / not fixed / new issues" list
- If anything is not fixed or a new issue is introduced, fix before the `/audit-team` run

The full `/audit-team` (5-role) runs after the audit-lite confirms clean, before commit+push.

---

## Version management

After each sprint that changes user-visible behavior, bump the patch version:
- Sprint 1 complete → v1.0.6
- Sprint 2 complete → v1.0.7
- Sprint 3 complete → v1.0.8
- Sprint 4 complete → v1.0.9

Each bump: update `agentsuite/__version__.py`, `pyproject.toml`, README badge, USER-MANUAL version, landing page badge, CHANGELOG entry, CONTRIBUTING test counts. The version-sync step is now part of the sprint close, not an afterthought.

---

## Ready to start Sprint 1?

Sprint 1 dispatch plan:
- Subagent A: ENG-001 (path traversal — cio + trust_risk mcp_tools)
- Subagent B: UX-002 + QA-001 (RevisionRequired recovery + auth retry fix)
- Subagent C: TEST-001 + DOC-002 + UX-001/DOC-005 (CI + USER-MANUAL + landing page)

All three dispatched simultaneously. Each returns with its own test pass/fail status. After all three return: run full test suite, audit-lite, then decide whether to commit or fix first.
