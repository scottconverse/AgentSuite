# Engineering Deep-Dive — AgentSuite v1.0.2-dev (Post-Sprint Audit)

**Role:** Principal Engineer  
**Date:** 2026-04-30  
**Codebase state:** 16cebe8 (post-sprint commit closing 8 v1.0.1 audit items)

---

## What's Working Well

- **ArtifactWriter security posture is correct.** `_resolve_safe()` does null-byte check + `is_relative_to()` containment verification. `__init__` calls `validate_run_id()` and also re-verifies `run_dir.is_relative_to(output_root)` after `resolve()`. This is defense-in-depth done right.
- **`agentsuite/agents/_common.py` is a clean choke point.** The module is small (41 lines), well-documented, directly expresses the invariant ("validate before path construction"), and is already wired into all 7 agents' `get_status`, `resume`, `approve`, and stage tools.
- **Atomic state writes.** `StateStore.save()` uses `tempfile.mkstemp` + `os.fsync` + `os.replace`. A partial write never corrupts the live state file.
- **ruff clean, mypy --strict clean (121 source files).** Type discipline enforced mechanically.
- **786 tests, 0 failures, 0 skips.** The no-skip rule is holding.
- **`_common.py` validation tests exist** in `test_mcp_server.py` — traversal probes for both `require_run_dir` and `require_kernel_dir`.

---

## Findings

### CRITICAL — QA-301: `RunStateSchemaVersionError` not handled in `list_runs` iteration (9 sites)

**Category:** Correctness / Stability  
**Severity:** Critical  
**Evidence:**  

`cli.py:166` (`_make_list_runs_fn`):
```python
state = StateStore(run_dir=d).load()  # raises RunStateSchemaVersionError on pre-v0.9 dir
if state is None or state.agent != agent_name:
    continue
```

`cli.py:228` (global `list_runs_cmd`):
```python
state = StateStore(run_dir=d).load()  # same — no handler
```

All 7 `{agent}/mcp_tools.py` `{agent}_list_runs` functions:
- `founder/mcp_tools.py:116`
- `design/mcp_tools.py:112`
- `product/mcp_tools.py:113`
- `engineering/mcp_tools.py:110`
- `marketing/mcp_tools.py:110`
- `trust_risk/mcp_tools.py:123`
- `cio/mcp_tools.py:127`

**Impact:** Any workspace that has a pre-v0.9 run directory will cause `agentsuite list-runs`, `agentsuite founder list-runs`, and all equivalent MCP `{agent}_list_runs` calls to throw an unhandled `RunStateSchemaVersionError`. The entire listing crashes rather than skipping the offending directory — the same skip-pattern that was correctly implemented in `agentsuite_cost_report` (ENG-004/QA-203).

**Blast radius:** Every user who upgrades from v0.8.x or earlier to v1.0.x and runs any list-runs command is hit by this. The `agentsuite_cost_report` MCP tool was fixed; `agentsuite_list_agents` is safe (doesn't load state files); but 9 other list-iteration sites were not swept.

**Why this was missed:** ENG-004/QA-203 was scoped to the specific finding ("cost_report propagates schema error") rather than answering "what other code iterates over run dirs and calls `.load()`?" — the same blast-radius question that was missed in the original ENG-001 write-path fix.

**Fix path:**
```python
# In _make_list_runs_fn, list_runs_cmd, and all {agent}_list_runs:
try:
    state = StateStore(run_dir=d).load()
except RunStateSchemaVersionError:
    _log.warning("Skipping pre-v0.9 run dir %s", d.name)
    continue
if state is None ...:
    continue
```

---

### CRITICAL — QA-302: `RunStateSchemaVersionError` not handled in `{agent}_get_status` single-run path (14 sites)

**Category:** Correctness / Stability  
**Severity:** Critical  
**Evidence:**

`founder/mcp_tools.py:103`:
```python
def founder_get_status(run_id: str) -> RunState:
    run_dir = require_run_dir(output_root_fn, run_id)
    state = StateStore(run_dir=run_dir).load()  # raises on pre-v0.9 dir
    if state is None:
        raise FileNotFoundError(...)
    return state
```

Same pattern in `design`, `product`, `engineering`, `marketing`, and `trust_risk`/`cio` (`get_run_status`). Also: `trust_risk/mcp_tools.py:191`, `cio/mcp_tools.py:195` (`get_qa_scores`, `get_revision_instructions`).

**Impact:** A targeted `get_status` query against a pre-v0.9 run_id throws an unhandled `RuntimeError` subclass to the MCP caller rather than a clean `FileNotFoundError` or an explicit "schema version mismatch" message.

**Fix path:** Wrap `.load()` in `try/except RunStateSchemaVersionError` and raise a descriptive `ValueError` or `FileNotFoundError` with a clear migration message.

---

### MINOR — ENG-101: Inconsistent `require_run_dir` usage in `{agent}_run` result path

**Category:** Code quality / Future safety  
**Severity:** Minor  
**Evidence:** `founder/mcp_tools.py:75`:
```python
run_id = request.run_id or _now_id()
agent = agent_class()
...
state = agent.run(request=founder_input, run_id=run_id)
run_dir = output_root_fn() / "runs" / run_id  # raw path — bypasses require_run_dir
return _result_from_state(state, run_dir)
```

The `run_id` is validated by `ArtifactWriter` inside `agent.run()`, so this specific site is safe. But the pattern is inconsistent — someone copying the pattern for a new tool might skip the `agent.run()` step and have an unvalidated path construction.

Same pattern across all 7 agents' `{agent}_run` functions.

**Fix path:** Change to `run_dir = require_run_dir(output_root_fn, run_id)` after the `agent.run()` call — it's a no-op semantically (already validated) but makes the pattern consistent.

---

### MINOR — ENG-102: `agentsuite migrate` referenced in error message but not implemented

**Category:** Correctness  
**Severity:** Minor  
**Evidence:** `mcp_server.py:133`:
```python
_log.warning(
    "Skipping run dir %s: schema version mismatch "
    "(pre-v0.9 run directory — upgrade with `agentsuite migrate`)",
    d.name,
)
```

`agentsuite --help` shows no `migrate` subcommand. The CLI registration in `cli.py` has no migrate command. A user who reads this warning and runs `agentsuite migrate` gets "Error: No such command 'migrate'".

**Fix path:** Either implement a stub `migrate` command that explains how to delete old run dirs, or change the error message to say "delete the run directory and re-run" (matching the language in `RunStateSchemaVersionError` itself).

---

### MINOR — ENG-103: Version not bumped (pyproject.toml still 1.0.1)

**Category:** Release hygiene  
**Severity:** Minor  
**Evidence:** `pyproject.toml:7`: `version = "1.0.1"`. `agentsuite/__version__.py:1`: `__version__ = "1.0.1"`. CHANGELOG has `[1.0.2] - Unreleased` but the package still self-reports 1.0.1.

**Fix path:** Bump both files to 1.0.2 in the same commit, update README badge.

---

### NIT — ENG-201: Redundant run_id validation in `resume` path

**Category:** Code quality  
**Severity:** Nit  
**Evidence:** In all agent `mcp_tools.py`, `{agent}_resume` calls `require_run_dir(output_root_fn, run_id)` which calls `validate_run_id(run_id)`. Then `agent.resume()` calls `validate_run_id(run_id)` again (`base_agent.py:101`). The second call is harmless and catches nothing new that the first didn't.

**Fix path:** Remove the redundant call in `BaseAgent.resume()` since the MCP tool layer now validates. Or keep both as defense-in-depth and document it.

---

## Severity Counts

| Severity | Count |
|----------|-------|
| Blocker | 0 |
| Critical | 2 |
| Major | 0 |
| Minor | 3 |
| Nit | 1 |

---

## Summary

The sprint closed 8 genuine issues. The architectural foundation is solid: atomic state, content-addressed artifacts, provider-agnostic LLM layer, mypy-strict type safety. The recurring theme is blast-radius gaps — when a fix is scoped to the specific finding rather than the general pattern. Both new Criticals (QA-301, QA-302) are exact repetitions of this pattern: the `RunStateSchemaVersionError` fix was applied to `agentsuite_cost_report` but not swept across all other `StateStore.load()` call sites.
