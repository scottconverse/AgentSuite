# Next-Sprint Watch List — AgentSuite v1.0.2-dev Audit

**Forward-looking items: architectural decisions, design debts, scaling concerns**

---

## W-01: Blast-radius analysis discipline is the systemic gap

**Priority:** High  
**Observation:** Three sprints in a row, a fix has been applied to the specific finding without sweeping the general pattern:
1. v1.0.0 → v1.0.1: `validate_run_id` added to `ArtifactWriter` but not to MCP read-path
2. v1.0.1 → v1.0.2 sprint: `require_run_dir` added to 7 agents' get_status/resume/approve but not to `{agent}_run` result path
3. v1.0.1 → v1.0.2 sprint: `RunStateSchemaVersionError` caught in `agentsuite_cost_report` but not in 9 `list_runs` and 14 `get_status` call sites

**Recommendation:** Before closing any security or error-handling fix, run a codebase-wide grep for the pattern. For `StateStore.load()`: `grep -rn "StateStore" agentsuite/` — every unprotected hit is a candidate. Adopt as a sprint-closure step.

---

## W-02: `_INPUTS_BY_AGENT` registry will silently drift as agents are added

**Priority:** Medium  
**Observation:** `state_store.py:25–33` hardcodes agent name → input schema. A new agent missing from the dict silently falls back to `AgentRequest`, dropping agent-specific fields. No test enforces parity with `registry.py`.

**Recommendation:** Add a parity test: enumerate registered agents, assert each appears in `_INPUTS_BY_AGENT`.

---

## W-03: `{agent}_list_runs` has no pagination

**Priority:** Medium  
**Observation:** Iterates all run dirs and loads every state file. 200+ disk reads on heavy workspaces. No `limit`, `since`, or status filter.

**Recommendation:** Add `limit` and `since` parameters in v1.1. Until then, document expected scale.

---

## W-04: `ArtifactWriter.promote()` not atomic on Windows

**Priority:** Medium  
**Observation:** `artifacts.py:167–169` — delete-then-rename leaves a window where both target and staging are absent. CI does not exercise this path on Windows with real files.

**Recommendation:** Use `os.replace()` semantics or document the limitation. Add a Windows interrupt test.

---

## W-05: No migration path for future schema changes

**Priority:** Low-Medium  
**Observation:** `RunStateSchemaVersionError` cleanly refuses to silently corrupt, but "delete and re-run" scales poorly. The ghost `agentsuite migrate` is the immediate symptom.

**Recommendation:** Implement stub `agentsuite migrate` in v1.1 that lists affected dirs and prints manual steps. Removes ghost-command problem; defers actual migration logic.

---

## W-06: Golden tests verify structure, not prompt quality

**Priority:** Low  
**Observation:** Mocked LLM output detects shape regressions, not prompt quality. Broken prompts pass golden tests.

**Recommendation:** v1.1 adds a lightweight prompt-regression check using local Ollama (cost ~$0), gated to PRs touching prompt files.

---

## W-07: Version-bump process manual and error-prone

**Priority:** Low  
**Observation:** Version lives in 3 files plus CHANGELOG. This sprint produced version skew (CHANGELOG ahead of package).

**Recommendation:** `scripts/bump-version.sh <new_version>` updating all locations atomically.

---

## W-08: Per-agent `mcp_tools.py` modules are 90% duplicated

**Priority:** Medium  
**Observation:** All 7 agents' mcp_tools.py have near-identical `_run`, `_resume`, `_approve`, `_get_status`, `_list_runs`, differing only in agent name and primary artifact filename. Bug fixes (like QA-301) require touching 7 files.

**Recommendation:** Extract `register_standard_tools(agent_name, primary_artifact, ...)` in `agents/_common.py`. Agents with extended tools (trust_risk, cio) inherit standard set + add their own. Reduces 7-fold maintenance to 1-fold.

---

## W-09: No SECURITY.md disclosure policy

**Priority:** Low  
**Observation:** v1.0.0 → v1.0.1 → v1.0.2 shipped 3 path-traversal fixes plus a schema-error fix. No `SECURITY.md` describes responsible disclosure for users finding similar issues.

**Recommendation:** Add `SECURITY.md` with contact address and disclosure policy. Even a 5-line file beats none.
