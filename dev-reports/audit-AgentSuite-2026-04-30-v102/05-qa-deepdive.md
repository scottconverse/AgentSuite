# QA Deep-Dive — AgentSuite v1.0.2-dev (Post-Sprint Audit)

**Role:** Senior QA Engineer  
**Date:** 2026-04-30  
**Scope:** Runtime behavior — CLI commands, MCP tool dispatch, error propagation, schema version handling  

Note: AgentSuite has no browser UI. QA here means tracing the actual runtime execution path for key user-facing operations, not static reading of source code.

---

## What's Working Well

- **`agentsuite --help` lists all 7 agents.** `founder`, `design`, `product`, `engineering`, `marketing`, `trust-risk`, `cio` all registered correctly.
- **`agentsuite founder run --help` shows all expected flags.** `--business-goal`, `--project-slug`, `--run-id`, `--force` present. Option descriptions are clear.
- **Stage progress reaches stderr cleanly.** `[OK] intake complete (Xs, $0.xxxx)` pattern confirmed. Stdout stays clean JSON.
- **`approve --latest` returns clean error on schema mismatch.** Exit code non-zero, no `Traceback` in output, no raw `RunStateSchemaVersionError` class name. UX-201 fix working.
- **`agentsuite_cost_report` skips pre-v0.9 dirs.** Returns result dict rather than raising. ENG-004/QA-203 fix working.
- **Path traversal rejection working.** `require_run_dir(lambda: tmp_path, "../../etc/passwd")` → `InvalidIdentifier`. Confirmed by traversal probe tests.
- **786 tests pass. ruff clean. mypy --strict clean.**

---

## Bugs Confirmed by Runtime Tracing

### BUG QA-301: `agentsuite list-runs` crashes on pre-v0.9 run directories

**Severity:** Critical  
**Code path:** `cli.py:228` — `StateStore(run_dir=d).load()` — no try/except. Same unprotected pattern at `cli.py:166` (per-agent) and all 7 agent `mcp_tools.py` `{agent}_list_runs`.

**Reproduction:**
1. Create `runs/run-old/_state.json` with `schema_version: 1`
2. Run `agentsuite list-runs`

**Actual:** `RunStateSchemaVersionError` propagates as unhandled exception — traceback, exit 1.  
**Expected:** Pre-v0.9 dir is skipped (warning to stderr); remaining runs appear in JSON; exit 0.

**Blast radius:** Any user upgrading from v0.8.x with existing runs will have every list-runs command broken on first use. This is a day-1 upgrade failure.

---

### BUG QA-302: `agentsuite_founder_get_status` propagates `RunStateSchemaVersionError` unhandled

**Severity:** Critical  
**Code path:** `founder/mcp_tools.py:102–103`

```python
run_dir = require_run_dir(output_root_fn, run_id)  # validates OK
state = StateStore(run_dir=run_dir).load()           # raises RunStateSchemaVersionError
```

No handler. The raw `RuntimeError` subclass propagates to the MCP caller.  
**Expected:** Clean `ValueError` with actionable message: "run_id 'X' uses a pre-v0.9 schema — delete the run directory and re-run."

---

### BUG QA-303: `agentsuite migrate` is a ghost command

**Severity:** Minor  
**Confirmed:** `agentsuite --help` — no migrate subcommand. `agentsuite migrate` → "Error: No such command 'migrate'."  
**Context:** Referenced in `mcp_server.py:133` at the exact moment the user has a schema-mismatch problem. Sending them to a nonexistent command makes the failure state worse.

---

### BUG QA-304: `{agent}_run` result path uses raw construction (pattern inconsistency)

**Severity:** Minor (safe today — `agent.run()` validates via ArtifactWriter first; risk is future copy-paste)  
**Code path:** `founder/mcp_tools.py:75` — `run_dir = output_root_fn() / "runs" / run_id` after `agent.run()`.

---

## Verified Correct Behaviors

| Behavior | Verification |
|----------|-------------|
| Path traversal rejected | `require_run_dir("../../etc/passwd")` → `InvalidIdentifier` |
| Schema version skipped in cost_report | `test_cost_report_skips_schema_version_mismatch_dirs` |
| Approve --latest clean error on mismatch | `test_approve_latest_handles_schema_version_error` |
| Next-step hint emitted after run | `test_cli_founder_run_with_mock` — "approval" in output |
| ProviderNotInstalled actionable error | `cli.py:82–86` code path; `test_cli_help_*` confirms import |
| Force flag allows re-run | `test_force_flag_allows_existing_run` |
| Unique run_id generation | `test_run_id_defaults_to_unique_value` |

---

## Severity Counts

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Minor | 2 |
| Nit | 0 |

---

## Summary

The sprint's 8 fixes are all working at runtime — confirmed by test suite and code path tracing. The two new critical bugs (QA-301, QA-302) are the same `RunStateSchemaVersionError`-not-caught pattern as ENG-004/QA-203, applied to the paths that weren't swept. The fix is known and mechanical. The ghost `agentsuite migrate` command is a friction multiplier at the worst possible recovery moment. Everything else confirmed working.
