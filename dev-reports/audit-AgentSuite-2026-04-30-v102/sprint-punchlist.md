# Sprint Punch List — AgentSuite v1.0.2-dev Audit

**For this sprint (fix before release):**

---

## P0 — Fix before any merge to main

### 1. [ENG/QA] Wrap `list_runs` `StateStore.load()` in `try/except RunStateSchemaVersionError` (QA-301)

**Scope:** 9 sites  
**Files:**
- `agentsuite/cli.py` — `_make_list_runs_fn` (line 166) and `list_runs_cmd` (line 228)
- `agentsuite/agents/founder/mcp_tools.py` line 116
- `agentsuite/agents/design/mcp_tools.py` line 112
- `agentsuite/agents/product/mcp_tools.py` line 113
- `agentsuite/agents/engineering/mcp_tools.py` line 110
- `agentsuite/agents/marketing/mcp_tools.py` line 110
- `agentsuite/agents/trust_risk/mcp_tools.py` line 123
- `agentsuite/agents/cio/mcp_tools.py` line 127

**Pattern:** Same as the already-correct fix in `agentsuite_cost_report`:
```python
try:
    state = StateStore(run_dir=d).load()
except RunStateSchemaVersionError:
    _log.warning("Skipping pre-v0.9 run dir %s", d.name)
    continue
```

**Surfaced by:** Engineering (QA-301), QA (QA-301)

---

### 2. [ENG/QA] Catch `RunStateSchemaVersionError` in `{agent}_get_status` single-run path (QA-302)

**Scope:** All 7 agents' `get_status` / `get_run_status` tools + extended tools in trust_risk and cio  
**Files:** `agentsuite/agents/*/mcp_tools.py` — the `*_get_status` / `get_run_status` functions  

**Pattern:**
```python
try:
    state = StateStore(run_dir=run_dir).load()
except RunStateSchemaVersionError as exc:
    raise ValueError(
        f"run_id {run_id!r} uses a pre-v0.9 schema — "
        f"delete the run directory and re-run."
    ) from exc
```

**Surfaced by:** Engineering (QA-302), QA (QA-302)

---

### 3. [TEST] Add `RunStateSchemaVersionError` tests for `list_runs` and `get_status` (TEST-301, TEST-302)

**Files:** `tests/unit/test_cli.py`, `tests/unit/test_mcp_server.py`  
**Pattern:** Same as `test_cost_report_skips_schema_version_mismatch_dirs` and `test_approve_latest_handles_schema_version_error` — create a pre-v0.9 state file, invoke the command, assert clean output.

Tests needed:
- `test_cli_list_runs_skips_schema_version_mismatch_dirs`
- `test_cli_founder_list_runs_skips_schema_version_mismatch_dirs`
- `test_founder_get_status_handles_schema_version_error` (one representative agent is enough; parametrize if desired)

**Surfaced by:** Test Engineer (TEST-301, TEST-302)

---

### 4. [DOC] Bump version to 1.0.2 in all version files (DOC-302, ENG-103)

**Files:** `pyproject.toml`, `agentsuite/__version__.py`, `README.md`  
**Action:** Change `1.0.1` → `1.0.2` in all three.  
**Surfaced by:** Documentation (DOC-302), Engineering (ENG-103)

---

### 5. [UX] Fix next-step hint placeholders (UX-301)

**Files:** All 7 `agentsuite/agents/*/agent.py` — the `next_step_hint` string  
**Change:** Replace `<your-name>` and `<slug>` with `YOUR_NAME` and `YOUR_SLUG` (uppercase, shell-safe), or use the actual `--project-slug` value from the CLI input if it's available at emit time.  
**Surfaced by:** UX (UX-301)

---

## P1 — Fix this sprint (before end of sprint)

### 6. [DOC] Fix `agentsuite migrate` ghost command reference (DOC-305, ENG-102, QA-303)

**Files:** `agentsuite/mcp_server.py:133`  
**Change:** Replace `upgrade with \`agentsuite migrate\`` with `delete {d.name} and re-run`.  
**Surfaced by:** Engineering (ENG-102), Documentation (DOC-305), QA (QA-303)

---

### 7. [DOC] Update USER-MANUAL.md version badge (DOC-301)

**File:** `USER-MANUAL.md:3`  
**Change:** `**Version 0.9.1**` → `**Version 1.0.2**` (or 1.0.1 if 1.0.2 not yet released)  
Also sweep the manual for procedures affected by `--force`, `--quiet`, `--latest` flags added since 0.9.1.  
**Surfaced by:** Documentation (DOC-301)

---

### 8. [DOC] Document `_common.py` helpers in CONTRIBUTING.md (DOC-303)

**File:** `CONTRIBUTING.md`  
**Add:** A "Security: path validation" section explaining that any MCP tool taking `run_id` or `project_slug` from a remote caller MUST use `require_run_dir` / `require_kernel_dir` from `agentsuite.agents._common`.  
**Surfaced by:** Documentation (DOC-303)

---

### 9. [TEST] Create `tests/unit/agents/test_common.py` (TEST-303)

**Coverage:** `require_run_dir` and `require_kernel_dir` — valid paths, traversal rejection, boundary lengths.  
**Surfaced by:** Test Engineer (TEST-303)

---

## P2 — Watch list (address if time permits this sprint)

- **ENG-101:** Standardize `{agent}_run` result path to use `require_run_dir` (safe today, pattern inconsistency)
- **TEST-304:** Add end-to-end traversal tests through MCP tool dispatch (not just helper-level)
- **TEST-305:** Add `test_cli_founder_list_runs_after_run` for per-agent list-runs subcommand
- **UX-303:** Add context to per-agent list-runs empty output when agent has no runs
- **UX-401:** Improve `--quiet` flag discoverability in per-agent help text
