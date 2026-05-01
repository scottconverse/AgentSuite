# Test Deep-Dive — AgentSuite v1.0.2-dev (Post-Sprint Audit)

**Role:** Test Engineer  
**Date:** 2026-04-30  
**Test suite state:** 786 passed, 3 deselected, 2 warnings, 0 failures, 0 skips  

---

## What's Working Well

- **786 tests, 0 skips.** The no-skip rule (Hard Rule 4a) is holding. Every test runs. The deselected 3 are known-unreachable private-access tests, not suppressed failures.
- **Four test tiers exist and are populated:** unit (`tests/unit/`), integration (`tests/integration/`), golden (`tests/golden/`), and top-level cross-cutting (`tests/test_*.py`).
- **Golden tests per agent.** `tests/golden/test_founder_patentforgelocal.py` and equivalents provide snapshot-style regression detection — if agent output shape changes unexpectedly, the golden test breaks.
- **Resume idempotency contract is tested.** `tests/integration/test_resume_idempotency.py` exercises the specific guarantee that resuming a run doesn't double-charge cost or restart from stage 0.
- **mypy integration test exists.** `tests/integration/test_downstream_consumer.py::test_downstream_consumer_typechecks_clean` runs mypy --strict against a sample consumer file. Type regressions are caught in CI, not in production.
- **New traversal probe tests (ENG-001, ENG-002).** `test_founder_get_status_rejects_traversal_run_id` and `test_kernel_artifacts_rejects_traversal_project_slug` directly test the `_common.py` helpers for the documented attack payloads (`../../etc/passwd`, `/etc/passwd`, `""`).
- **New schema version test (ENG-004/QA-203).** `test_cost_report_skips_schema_version_mismatch_dirs` confirms the cost_report tool skips pre-v0.9 state files. Pattern is correct.
- **New UX-201 test.** `test_approve_latest_handles_schema_version_error` confirms `approve --latest` returns a clean error (not a traceback) for schema-mismatch runs.

---

## Findings

### CRITICAL — TEST-301: No test for `RunStateSchemaVersionError` in `list_runs` (mirrors QA-301)

**Category:** Coverage gap  
**Severity:** Critical  
**Evidence:** `test_cost_report_skips_schema_version_mismatch_dirs` tests the cost_report tool. There is no equivalent test for:
- `agentsuite list-runs` CLI command (global) with a pre-v0.9 run dir
- `agentsuite founder list-runs` CLI command with a pre-v0.9 run dir
- `agentsuite_founder_list_runs` MCP tool with a pre-v0.9 run dir in the runs root

These call sites are currently unprotected (QA-301 in engineering report). Without tests, fixing QA-301 is not verifiable — and un-fixing it by a future refactor is undetectable.

**Fix path:** Add a parametrized test modeled on `test_cost_report_skips_schema_version_mismatch_dirs`:
1. Create a pre-v0.9 state file in a runs dir
2. Invoke `list-runs` (CLI) and `{agent}_list_runs` (MCP tool)
3. Assert exit code 0 (CLI) / no exception (MCP), and the bad run is absent from output

---

### CRITICAL — TEST-302: No test for `RunStateSchemaVersionError` in `{agent}_get_status` single-run path

**Category:** Coverage gap  
**Severity:** Critical  
**Evidence:** `test_founder_get_status_tool_handles_missing_run` tests the `FileNotFoundError` path. There is no test for calling `founder_get_status` with a `run_id` that points to a pre-v0.9 state file. The expected behavior is a clean error (not a raw `RunStateSchemaVersionError` propagating to the MCP caller), but there is no test asserting this.

**Fix path:** Add `test_founder_get_status_rejects_schema_version_mismatch` parallel to the existing missing-run test. Create a pre-v0.9 state file for a known run_id, call `get_status`, assert a clean error.

---

### MAJOR — TEST-303: No dedicated unit test file for `agentsuite/agents/_common.py`

**Category:** Coverage organization  
**Severity:** Major  
**Evidence:** `_common.py` is tested only indirectly via `test_mcp_server.py::test_founder_get_status_rejects_traversal_run_id` and `test_kernel_artifacts_rejects_traversal_project_slug`. These tests call `require_run_dir` and `require_kernel_dir` directly, which is good, but:
1. There is no `tests/unit/agents/test_common.py`
2. The test for the valid-identifier happy path (`result = require_run_dir(lambda: tmp_path, "run-20260430-123456-789012")`) exists but lives in a cross-cutting server test rather than a module-specific unit test
3. Edge cases not tested: single-char run_id (`"a"`), 64-char max, leading underscore, dot in the middle of a slug

**Fix path:** Create `tests/unit/agents/test_common.py` with:
- `test_require_run_dir_validates_and_returns_correct_path`
- `test_require_run_dir_rejects_traversal`
- `test_require_kernel_dir_validates_and_returns_correct_path`
- `test_require_kernel_dir_rejects_traversal`
- Edge cases for boundary lengths and allowed characters

---

### MAJOR — TEST-304: MCP tool-level traversal rejection not tested end-to-end

**Category:** Coverage depth  
**Severity:** Major  
**Evidence:** The existing traversal tests call `require_run_dir` and `require_kernel_dir` directly. They confirm the helpers reject bad inputs. But there is no test that calls `founder_get_status(run_id="../../etc/passwd")` via the MCP tool dispatch path — confirming the rejection propagates correctly through the full MCP tool call rather than only at the helper level.

This distinction matters: if a future refactor changes how the MCP tool constructs the path (e.g. calling the agent method directly which has its own validation), the helper-level test would still pass while the tool might be unprotected.

**Fix path:** Add one end-to-end traversal test per agent's `get_status` MCP tool, using the spy-server pattern already established in `test_founder_get_status_tool_handles_missing_run`.

---

### MINOR — TEST-305: `test_cli_list_runs_after_run` only tests the global list-runs, not per-agent

**Category:** Coverage gap  
**Severity:** Minor  
**Evidence:** `test_cli_list_runs_after_run` tests `agentsuite list-runs` (global). There is no test for `agentsuite founder list-runs` (the per-agent subcommand). The per-agent list-runs has its own code path (`_make_list_runs_fn`) with agent-name filtering logic that is untested.

**Fix path:** Add `test_cli_founder_list_runs_after_run` that invokes `["founder", "list-runs"]` and asserts the run_id appears in output.

---

## Severity Counts

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Major | 2 |
| Minor | 1 |
| Nit | 0 |

---

## Summary

The test suite is in excellent shape overall — 786 tests, 0 skips, mechanically enforced. The new tests added in this sprint (traversal probes, schema version, UX-201) are well-structured and follow the established patterns. The remaining gaps are all in the same thematic area: the `RunStateSchemaVersionError` coverage was scoped to the cost_report fix but not extended to the list_runs and get_status paths that have the same vulnerability. The pattern for the missing tests is already established — just needs to be applied to the unprotected sites.
