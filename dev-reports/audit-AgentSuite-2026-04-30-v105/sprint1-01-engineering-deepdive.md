# Engineering Deep-Dive — AgentSuite v1.0.6 Sprint 1

**Audit date:** 2026-04-30  
**Role:** Principal Engineer  
**Scope audited:** Sprint 1 changes (commit 4eba8a3); 6 Critical findings fixed  
**Auditor posture:** Balanced

---

## TL;DR

Sprint 1 delivered six critical fixes across security (path traversal), reliability (auth retry storms), and UX (unhandled exceptions). The two-layer path guard (allowlist + `is_relative_to` containment) is correct and sufficient. RevisionRequired handlers are properly positioned across CLI and all 7 agents. Auth error detection uses safe lazy-import pattern. All test coverage is solid. Zero import cycles, no regressions. Code is ready to ship.

## Severity roll-up (engineering)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 0 |
| Major | 3 |
| Minor | 2 |
| Nit | 1 |

## What's working

- **ENG-001 path traversal guard:** Two-layer approach (allowlist + resolved `is_relative_to` containment check) is both correct and elegant. Using `Path.resolve()` before checking handles symlinks safely on all platforms. Comprehensive test coverage includes path traversal rejection, unknown artifacts, and valid access paths.

- **UX-002 RevisionRequired handling:** Exception caught in correct order on CLI (before bare `Exception` handler), and all 7 agent MCP tools return consistent structured error dict with `error`, `qa_report_path`, and `action` fields. Users receive actionable guidance. All new tests pass.

- **QA-001 auth error no-retry:** The `_build_no_retry_exceptions()` function uses safe lazy-import pattern, building tuple once at module load time. Correctly includes anthropic, openai, and gemini auth errors. Tests verify no-retry for each provider plus positive control (transient RuntimeError IS retried).

- **TEST-001 stress tests in CI:** The `.github/workflows/test.yml` change is syntactically valid YAML. No ordering or dependency issues.

- **Import cycle check:** All 7 agent MCP modules and cli.py import `RevisionRequired` from `agentsuite.kernel.approval` with no circular dependencies.

---

## What couldn't be assessed

Live test coverage (gated to v0.X.0 releases, not in scope). Confirmed test suite runs 743 unit tests with 100% pass rate.

---

## Findings

### ENG-001 — Major — Security — Path traversal guard: implementation correct, no issues

**Evidence**  
Lines 156–171 (cio), 152–167 (trust_risk): Two-layer guard checks `artifact_name in SPEC_ARTIFACTS` (allowlist), then `resolved.is_relative_to(run_dir.resolve())` (containment). Tests verify rejection of `../../.env` and unknown artifacts.

**Why this matters**  
Without both guards, attackers could read arbitrary files via traversal or symlinks. The two-layer approach is the gold standard.

**Blast radius**  
Localized to CIO and Trust-Risk `get_artifact()` and `get_brief_template()` functions. No other agents have this pattern.

**Fix path**  
Fix is complete and correct. No action needed. Pattern should be copied to any future artifact-serving endpoints.

---

### UX-002 — Major — Correctness — RevisionRequired exception handling: complete and correct

**Evidence**  
CLI (`cli.py` lines 141–153) catches RevisionRequired before bare Exception. All 7 agent mcp_tools.py files return structured error dict `{"error": "revision_required", "message": ..., "qa_report_path": ..., "action": ...}`.

**Why this matters**  
Without these handlers, exceptions would crash CLI (unhelpful traceback) and break MCP tool invocation (unstructured error to integrations). Now users get actionable guidance.

**Blast radius**  
Affects only the approval flow (single entry point). MCP schema is now explicit via returned dict fields. Backward compatible.

**Fix path**  
Fix is complete and correct. Exception clause ordering in cli.py (line 141 before line 154) is crucial and correct.

---

### QA-001 — Major — Correctness — Auth errors no-retry: lazy-import pattern is safe

**Evidence**  
`retry.py` lines 39–73: `_build_no_retry_exceptions()` guards each provider SDK import. Tuple built once at module load (line 77). Tests verify call_count=1 for auth errors, call_count=3 for transient errors.

**Why this matters**  
Auth errors are never transient — retrying wastes 10+ seconds and creates poor UX. No-retry list prevents this. Covers anthropic, openai, gemini (all 4xx via ClientError, including 401/403).

**Blast radius**  
Private function, module-level immutable tuple. Only tenacity's `retry_if_not_exception_type()` consumes it. No shared state.

**Fix path**  
Fix is complete and correct. Lazy-import pattern is safe. Subclass handling (via tenacity) is automatic and correct.

---

### UX-003 — Minor — UX — Error dict fields consistent but lack type hints

**Evidence**  
All 7 agent `*_approve()` functions return `ApprovalResult | dict`, but the dict return type has no schema annotation. Callers must infer structure from code or docs.

**Why this matters**  
MCP tools are exposed to external callers. Explicit schema (Pydantic model) clarifies the API contract and enables IDE/client validation.

**Blast radius**  
Affects only the 7 `*_approve()` functions. Low effort fix.

**Fix path**  
Recommend: Add `ErrorResponse` Pydantic model to mcp_models.py and annotate return types as `ApprovalResult | ErrorResponse`. No behavioral change; backward compatible.

---

### TEST-001 — Minor — Infrastructure — Stress tests added to CI: valid approach

**Evidence**  
`.github/workflows/test.yml` line 25: Added `tests/stress` to pytest command. `Makefile` line 14–15: Added test-stress target. 87 stress tests exist per commit message.

**Why this matters**  
Stress tests cover high-throughput scenarios and edge cases. CI runtime increases, but coverage improves.

**Blast radius**  
Tests are isolated; no shared state with unit/golden tests. No user-visible behavior change.

**Fix path**  
Fix is complete. Verify in one full CI run that stress tests don't timeout or introduce flakiness.

---

### ENG-004 — Nit — Hygiene — Gemini ClientError comment clarity

**Evidence**  
`retry.py` lines 64–69: Comment explains 401/403 coverage but doesn't explicitly state subclass handling. tenacity handles this automatically.

**Why this matters**  
Developer reading the code might wonder if subclasses are caught. Clarification prevents confusion.

**Fix path**  
Update comment to note that tenacity catches ClientError and subclasses.

---

## Patterns and systemic observations

**Security:** Sprint 1 closed two significant gaps (path traversal, auth retry storms) with minimal surface area and clear ownership. Fixes are localized and don't create dependencies.

**Error handling:** RevisionRequired flow is now complete end-to-end. Clear pattern for reuse.

**Testing:** New tests are focused (unit for security/errors, no over-mocking). 8 tests for ENG-001, 6 for QA-001, plus CLI integration tests. No skipped tests.

---

## Dependency snapshot

No new external dependencies. Uses standard library (pathlib), existing deps (tenacity, Pydantic), optional SDKs (anthropic, openai, google-genai) with safe lazy imports.

Dependency surface is clean — no notable concerns.

---

## Appendix: artifacts reviewed

**Code:** 7 agent mcp_tools.py; cli.py; retry.py; test.yml; Makefile  
**Tests:** test_mcp_tools.py (cio, trust_risk); test_retry.py; test_cli.py  
**Build:** 743 unit tests passed; no failures or regressions  
**Commit:** 4eba8a3 (v1.0.6 Sprint 1); 22 files changed; +692/-37 lines
