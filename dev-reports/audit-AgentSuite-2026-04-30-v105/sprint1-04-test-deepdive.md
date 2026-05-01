# Test Suite Deep-Dive — AgentSuite v1.0.6 Sprint 1

**Audit date:** 2026-04-30
**Role:** Test Engineer
**Scope audited:** Sprint 1 test changes — 5 test files (new + updated)
**Auditor posture:** Balanced
**Test framework:** pytest
**Coverage:** Unit tests, integration tests via mocks

---

## TL;DR

Sprint 1's new tests are well-intentioned but narrow in scope. Path traversal tests (ENG-001) in cio/trust_risk verify happy paths and basic `../` attacks but miss encoded traversal variants and boundary encoding. RevisionRequired tests (UX-002) in founder/cli verify the happy case but lack edge cases (missing qa_report_path, malformed state). Retry tests (QA-001) correctly verify no-retry for auth errors and use pytest.importorskip properly, but don't verify the regression scenario (transient errors still retry). The test suite would miss: URL-encoded or double-encoded traversal attacks, RevisionRequired errors with incomplete state, structured response validation beyond presence checks, and cross-agent RevisionRequired inconsistency. No `.skip` or `.xit` shortcuts found — good discipline.

---

## Severity roll-up (tests)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 2 |
| Minor | 3 |
| Nit | 1 |
| **Total** | **7** |

---

## What's working

- **Path traversal guard exists.** CIO and trust_risk implementations check both allowlist membership (`if artifact_name not in SPEC_ARTIFACTS`) and path resolution (`is_relative_to()` check). This is defense-in-depth and prevents simple attacks.
- **pytest.importorskip used correctly.** Retry tests use `pytest.importorskip("anthropic")` to conditionally load optional dependencies. Tests skip gracefully if SDK is not installed.
- **Auth error no-retry verified accurately.** Test confirms `call_count == 1` (not retried) for `anthropic.AuthenticationError`, `anthropic.PermissionDeniedError`, OpenAI equivalents, and Gemini `ClientError`. Uses real exception classes via `__new__`.
- **RevisionRequired returns structured dict.** Founder's approve handler returns `{"error": "revision_required", "qa_report_path": "...", "action": "..."}` on requires_revision=True, not a raw exception or string. Test verifies dict presence.
- **No shortcuts detected.** Zero `pytest.mark.skip`, `xit`, `@pytest.mark.xfail`, `.only`, or `TODO: add test` comments across all reviewed test files. This shows discipline.
- **CLI tests exercise realistic user flows.** test_cli.py runs full agent workflows (run → approve) and tests cross-agent coverage (founder, design, product, engineering, marketing, cio, trust_risk).

---

## What couldn't be assessed

- **Transient error retry regression test meaningfulness.** test_transient_runtime_error_is_retried (line 257) verifies RuntimeError is retried up to max_attempts=3, but it uses a mock that always fails. The test does not verify behavior changed after a bugfix that tried to filter out transient errors. Without access to git history or a before-state version of the code, I cannot confirm this is a genuine regression test vs. a happy-path coverage test.
- **CI/CD blocking behavior.** Test runs appear isolated (no CI config reviewed). Cannot verify whether CI actually blocks pre-commit or if test suites run in parallel / are parallelized.

---

## Test landscape

| Dimension | Observation |
|---|---|
| Framework | pytest (Python) |
| Test pyramid shape | Heavy unit (artifact/template/tool tests), thin integration (mocked LLM), no E2E (no live API calls in Sprint 1 tests) |
| Coverage tool | Not configured in this scope (coverage.py not invoked in test files) |
| Reported coverage | None reported in test files; audit does not measure overall % |
| Flakiness posture | Clean — no flaky test patterns, no `--retry` config, no sleep-based waits |
| CI blocking? | Unknown — not audited in this scope |

---

## Findings

### TEST-001 — Critical — Coverage — Path traversal tests miss encoded sequence variants

**Evidence**

- `tests/unit/agents/cio/test_mcp_tools.py` line 37–44: test_get_artifact_rejects_path_traversal tests only `"../../.env"`
- `tests/unit/agents/trust_risk/test_mcp_tools.py` line 37–44: identical test with same single payload
- `agentsuite/agents/cio/mcp_tools.py` source uses `resolve()` + `is_relative_to()` check, which blocks `../` but source code does not appear to handle:
  - URL-encoded traversal: `"..%2F..%2Fenv"`
  - Double-encoded: `"..%252F..%252F.env"`
  - Unicode normalization attacks (if filesystem supports)

**Why this matters**

A path traversal vulnerability is a high-impact security issue. The test suite demonstrates awareness of the threat class and implements a guard, but the test coverage is narrow. An attacker could bypass `../` filtering with encoding variants, escalating the risk from "covered by test" to "vulnerable by path."

**Blast radius**

- Affected code: `agentsuite/agents/cio/mcp_tools.py::agentsuite_cio_get_artifact`, `agentsuite/agents/trust_risk/mcp_tools.py::agentsuite_trust_risk_get_artifact`
- Shared logic: Both agents use identical artifact allowlist + path resolution pattern. A fix in one must apply to both.
- Propagation: design, engineering, product, marketing agents also have `mcp_tools.py` files but no path traversal tests at all (no mcp_tools test file for engineering/marketing; design/product test files exist but only cover happy path).
- Related findings: TEST-004 (cross-agent artifact handler inconsistency).

**Fix path**

Add parametrized test cases to both cio and trust_risk covering:
1. URL-encoded: `"..%2F..%2F.env"`
2. Double-encoded: `"..%252F.env"`
3. Mixed: `"..%2F../.env"`
4. Case variations if filesystem is case-insensitive

Recommend using `@pytest.mark.parametrize` with at least 5 malformed payloads. Also audit the source code to confirm `resolve()` + `is_relative_to()` is sufficient for the target filesystem.

---

### TEST-002 — Major — Coverage — RevisionRequired tests lack edge cases (missing qa_report_path, incomplete state)

**Evidence**

- `tests/unit/agents/founder/test_mcp_tools.py` line 151–191: test_founder_approve_revision_required_returns_structured_error creates a clean RevisionRequired state with all fields set.
- `tests/unit/test_cli.py` line 397–418: test_cli_approve_revision_required_exits_1_with_actionable_message assumes qa_report_path is always present.
- Test does NOT cover:
  - `requires_revision=True` but `qa_report_path` missing or empty string
  - State file corrupted (partial JSON)
  - qa_report.md file does not exist on disk despite path reference

**Why this matters**

The RevisionRequired feature is a critical user-facing flow. The test assumes the happy case: state is well-formed, qa_report_path is set, and the file exists. In production, state files can be partially written, paths can be wrong, or files can be deleted by cleanup tasks. If qa_report_path is missing or the file is not found, the user sees an opaque error instead of actionable guidance.

**Blast radius**

- Affected code: `agentsuite/agents/founder/mcp_tools.py::agentsuite_founder_approve` (and equivalent in other agents)
- User-facing: All 7 agents (founder, design, engineering, product, marketing, cio, trust_risk) have an approve flow. Only founder is tested; the other 6 have no RevisionRequired tests at all.
- Related findings: TEST-004 (only founder has RevisionRequired test coverage).

**Fix path**

Extend test_founder_approve_revision_required_returns_structured_error to cover:
1. State with `requires_revision=True` but no `qa_report_path` field → must still return a dict with "error" key and graceful message
2. State with `qa_report_path` set but file missing → must not raise FileNotFoundError
3. State file itself corrupted (invalid JSON) → must handle StateStore.load() exception gracefully

Add similar tests for design, engineering, product, marketing, cio before they ship.

---

### TEST-003 — Major — Coverage — Path traversal tests do not enumerate all valid artifact names

**Evidence**

- `tests/unit/agents/cio/test_mcp_tools.py` line 47–54: test_get_artifact_rejects_unknown_artifact tests `"secret-data"` (not in allowlist).
- Test uses hardcoded string, not exhaustive list of valid names.
- Source code defines SPEC_ARTIFACTS but test only uses `SPEC_ARTIFACTS[0]` for positive case (line 62).
- Test does not verify that EVERY name in SPEC_ARTIFACTS is accepted.

**Why this matters**

If an artifact name is added to SPEC_ARTIFACTS in source but tests aren't updated, the allowlist can drift. A test that verifies "unknown names are rejected" without verifying "all known names are accepted" can miss drift.

**Blast radius**

- Affected code: `agentsuite/agents/cio/mcp_tools.py::SPEC_ARTIFACTS`, `agentsuite/agents/trust_risk/mcp_tools.py::SPEC_ARTIFACTS`
- Risk: SPEC_ARTIFACTS is a module-level constant. Adding a new artifact name requires updating the constant AND the allowlist guard in get_artifact (if they're separate). A missing sync could leak the new name.

**Fix path**

Parametrize the positive case:
```python
@pytest.mark.parametrize("artifact_name", SPEC_ARTIFACTS)
def test_get_artifact_returns_content_for_every_valid_name(tmp_path, artifact_name):
    # Create file for this artifact and verify it's returned
```

---

### TEST-004 — Major — Coverage — Only founder has RevisionRequired test; other 6 agents untested

**Evidence**

- `tests/unit/agents/founder/test_mcp_tools.py` line 151–191: test_founder_approve_revision_required_returns_structured_error
- `tests/unit/agents/design/test_mcp_tools.py`: no RevisionRequired tests (120 lines total, covers registration and happy-path runs only)
- `tests/unit/agents/product/test_mcp_tools.py`: no RevisionRequired tests (99 lines total, covers registration and list_runs only)
- `tests/unit/agents/engineering/`: no test_mcp_tools.py file at all
- `tests/unit/agents/marketing/`: no test_mcp_tools.py file at all
- `tests/unit/agents/cio/test_mcp_tools.py`: no RevisionRequired tests (only ENG-001 path traversal)
- `tests/unit/agents/trust_risk/test_mcp_tools.py`: no RevisionRequired tests (only ENG-001 path traversal)

**Why this matters**

UX-002 requires all agents' approve handlers to return structured dicts on RevisionRequired. Only founder's handler is tested. Design, product, cio, trust_risk may have inconsistent implementations, missing qa_report_path, or different error keys. An inconsistency between agents becomes a support burden and confuses users.

**Blast radius**

- Affected code: all 7 agents' `mcp_tools.py::*_approve` handlers
- User-facing: approve command is a public MCP tool. Each agent's behavior must be consistent.
- Related findings: TEST-002 (RevisionRequired tests lack edge cases), TEST-005 (cli tests do not cover non-founder approve RevisionRequired).

**Fix path**

Create a shared test helper (e.g., `conftest.py::_test_agent_approve_revision_required(agent_name, tmp_path)`) that:
1. Sets up a requires_revision=True state
2. Calls agent_approve
3. Asserts dict response with keys: `error`, `qa_report_path`, `action`

Add a parametrized test in each agent's test_mcp_tools.py to call this helper.

---

### TEST-005 — Minor — Coverage — CLI tests for approve RevisionRequired only cover founder; other agents untested

**Evidence**

- `tests/unit/test_cli.py` line 397–418: test_cli_approve_revision_required_exits_1_with_actionable_message calls `["founder", "approve", ...]`
- Lines 110–124: parametrized tests for agent_run_help and agent_approve_help exist for all 7 agents (product, engineering, marketing, trust-risk, cio, founder, design).
- Lines 130–174: full run tests exist for product, engineering, marketing, cio, trust_risk.
- But: no full approve tests (with RevisionRequired) for design, product, engineering, marketing, cio, trust_risk.

**Why this matters**

The CLI is the user-facing surface. If an agent's CLI approve command fails differently (e.g., prints a traceback instead of a message), users hit it first. Founder is covered; the other 6 agents' CLI paths are untested.

**Blast radius**

- Affected code: `agentsuite/cli.py::founder_approve`, `agentsuite/cli.py::design_approve`, etc.
- User-facing: all approve CLI commands

**Fix path**

Add parametrized E2E CLI test:
```python
@pytest.mark.parametrize("agent_cmd", ["design", "product", "engineering", "marketing", "cio", "trust-risk"])
def test_cli_approve_revision_required_for_agent(agent_cmd, tmp_path, monkeypatch):
    _write_revision_required_state(tmp_path, agent=agent_cmd)
    # Run approve command for this agent
    # Assert exit code 1, no traceback, includes qa_report message
```

---

### TEST-006 — Minor — Quality — Retry test's call_count assertion uses string interpolation for error message (minor style)

**Evidence**

- `tests/unit/llm/test_retry.py` line 175–177:
  ```python
  assert inner.call_count == 1, (
      f"Expected 1 call (no retry), got {inner.call_count}"
  )
  ```
- Similar pattern in lines 194–196, 213–215, 232–234, 269–271.
- This is clear and functional, but pytest's native assertion rewriting would simplify to just `assert inner.call_count == 1` without the message.

**Why this matters**

This is a style preference, not a bug. The explicit messages are helpful in CI logs, but native pytest rewriting is more maintainable.

**Fix path**

Optional: switch to pytest's native assertion + `pytest.raises(..., match="...")` for clearer diffs. Current version is fine.

---

### TEST-007 — Nit — Regression — "Transient error no-retry" test may not be a genuine regression test

**Evidence**

- `tests/unit/llm/test_retry.py` line 257–271: test_transient_runtime_error_is_retried
- Test verifies that a plain `RuntimeError` (not an auth error) is retried up to max_attempts=3.
- Test uses `_AlwaysFailProvider` which raises RuntimeError on every call.
- Test does NOT:
  - Show a before-state bug (e.g., RuntimeError was NOT retried before)
  - Reference a ticket or commit that fixed a bug
  - Compare behavior to a previous version

**Why this matters**

The comment "A plain RuntimeError (transient failure) MUST still be retried" suggests this test was added to prevent a regression. But without evidence of the original bug (git log, ticket reference, or a before-state assertion), this is a happy-path test labeled as regression. If the retry logic was recently refactored to stop retrying something it should retry, this test catches it — but we have no way to know from the test alone.

**Fix path**

Optional: add a comment with the ticket/issue reference (e.g., `# Regression: GH-123 — retries were being skipped for non-auth errors`) or adjust the test name to `test_transient_runtime_error_is_still_retried_happy_case` to clarify intent.

---

## Shortcut census

| Shortcut pattern | Count |
|---|---|
| `.skip` / `xit` / `@skip` | 0 |
| `.only` (left in) | 0 |
| `TODO: add test` / similar | 0 |
| Empty assertion / placeholder | 0 |
| `--retry` / retries normalized | 0 (no CI config reviewed) |

**Summary:** Zero shortcuts detected. This shows discipline.

---

## Blind spots by class

1. **Encoding attacks (path traversal).** Tests miss URL-encoded, double-encoded, and Unicode normalization variants of `../`.
2. **Partial/corrupted state (RevisionRequired).** Tests don't verify behavior when qa_report_path is missing, incomplete, or when the state file is malformed.
3. **Cross-agent consistency.** Only founder's RevisionRequired is tested; other 6 agents are untested.
4. **Boundary conditions (artifact names).** Tests verify "unknown names rejected" but not "all known names accepted" exhaustively.
5. **Error recovery in CLI.** No test covers what happens if StateStore.load() throws an exception during approve.
6. **Concurrency (not in Sprint 1 scope).** No tests for simultaneous approve calls on the same run.

---

## Patterns and systemic observations

**Narrow scope, good intent.** Sprint 1 tests are focused on three security/UX concerns (ENG-001, UX-002, QA-001) but are implementation-complete only for the happy paths. The team clearly understands the feature requirements but did not extend tests to cover edge cases or cross-agent coverage.

**Asymmetric coverage.** Founder agent is heavily tested (approval handler, RevisionRequired path); design, product, engineering, marketing, cio, trust_risk are lightly tested (registration, happy-path runs only). This is a pattern: the first agent (founder) gets full coverage; subsequent agents reuse patterns but skip edge-case tests.

**Mock-heavy, integration-thin.** All tests use mocked LLM (MockLLMProvider). No tests call real Claude/GPT/Gemini APIs. This is appropriate for unit tests, but the test suite makes no distinction between "unit tests with mocked deps" and "integration tests." The project may benefit from a separate integration test tier that uses real APIs (gated behind RUN_LIVE_TESTS=1 and cost caps, per CLAUDE.md).

**No flakiness culture.** Tests do not use sleep, retry config, or timeouts. This is healthy — tests are deterministic.

---

## Appendix: test artifacts reviewed

**Test files read (5 of 5):**
1. `tests/unit/agents/cio/test_mcp_tools.py` — 135 lines
2. `tests/unit/agents/trust_risk/test_mcp_tools.py` — 135 lines
3. `tests/unit/agents/founder/test_mcp_tools.py` — 191 lines
4. `tests/unit/llm/test_retry.py` — 272 lines
5. `tests/unit/test_cli.py` — 418 lines

**Related test files scanned (not fully read):**
- `tests/unit/agents/design/test_mcp_tools.py` — 120 lines (no RevisionRequired tests)
- `tests/unit/agents/product/test_mcp_tools.py` — 99 lines (no RevisionRequired tests)
- `tests/unit/agents/engineering/` — no test_mcp_tools.py
- `tests/unit/agents/marketing/` — no test_mcp_tools.py

**Reference docs read:**
- test-engineer.md (audit methodology)
- severity-framework.md (severity definitions)
- blast-radius.md (impact assessment)
- 04-test-deepdive.md (report template)
- CLAUDE.md (project standards: no pytest.skip, coverage discipline required)
