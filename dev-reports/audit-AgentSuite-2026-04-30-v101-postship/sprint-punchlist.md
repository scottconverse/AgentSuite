# Sprint Punch List — AgentSuite v1.0.1 Post-Ship Audit

**Audit date:** 2026-04-30
**Target:** v1.0.2 sprint
**Source:** `00-executive-audit.md` — all items verified across at least one role deep-dive

Fix all 8 items before tagging v1.0.2. Items 1–6 are Critical security or UX findings; items 7–8 are high-priority Majors with S-size effort. All are estimated S or M.

---

## Priority Order

| # | ID(s) | Severity | Effort | Owner role | What to do |
|---|---|---|---|---|---|
| 1 | ENG-001 / QA-201 | Critical | S | Engineering | Add `validate_run_id(run_id)` as the first line of each `get_status` and stage-kick function in all 7 agents' `mcp_tools.py`. Add a traversal probe test in `test_mcp_server.py` (e.g. `run_id="../../../etc/passwd"` must be rejected). Consider a shared `_require_run_dir()` helper in `agentsuite/agents/_common.py` to avoid 7-way copy-paste. |
| 2 | ENG-002 / QA-202 | Critical | S | Engineering | Add `validate_project_slug(project_slug)` as the first line of `agentsuite_kernel_artifacts` in `mcp_server.py`. Add test. |
| 3 | DOC-201 | Critical | S | Documentation | Run `grep -r "six-stage" .` (and "six stages") across the repo. Replace all instances with "five-stage pipeline, plus a kernel-managed approval step." Known locations: `README.md:15`, `docs/index.html:55`, `discussions-seeds.md:15`, `launch-posts.md:44,79`. Verify the README architecture diagram (which correctly shows five stages) no longer contradicts the prose above it. |
| 4 | DOC-202 | Critical | S | Documentation | Delete `docs/USER-MANUAL.md` (652-line stale v0.2 document). Update the link at `docs/index.html:127` and `README.md:277` to point to the root `USER-MANUAL.md` (984-line current document). Verify GitHub Pages resolves the link correctly after push. Grep for any other references to `docs/USER-MANUAL.md` in the repo and update them. |
| 5 | UX-201 | Critical | S | Engineering / UX | In `cli.py:_make_approve_fn`, move the `_resolve_latest_run_id(...)` call inside the existing `try/except Exception` block so that `RunStateSchemaVersionError` is caught and surfaced as a human-readable error message rather than a raw traceback. Add a test for the `approve --latest` path with a pre-v0.9 run directory. |
| 6 | UX-202 | Critical | M | UX / Engineering | Add a `next_step_hint: str` field to `AgentCLISpec`. After the JSON output block in `cli.py:_register_agents()`, emit the hint to stderr (e.g. "Run `agentsuite founder approve --latest` to continue."). Set a meaningful hint for each of the 7 agents. Update any tests that assert `AgentCLISpec` field structure. |
| 7 | ENG-004 / QA-203 | Major | S | Engineering | Wrap `store.load()` in `agentsuite_cost_report` with `try/except RunStateSchemaVersionError: log.warning(...); continue` so that v1.0.0 run directories don't crash the cost report for every user upgrading from v1.0.0. Add a test with a v1.0.0 schema directory in the run root. |
| 8 | UX-204 / QA-204 | Major | S | UX / Documentation | Fix the install step in `USER-MANUAL.md` — change `pip install agentsuite` to `pip install "agentsuite[anthropic] @ git+..."` (or whichever provider the user chose). Widen the `except` clause in `_resolve_llm_for_cli` to catch `ProviderNotInstalled` alongside `NoProviderConfigured` and emit an actionable "install the provider extra" message. |

---

## Blast-Radius Notes

- **Items 1–2** (MCP traversal validation) touch all 7 agents' `mcp_tools.py`. Run full `pytest tests/unit/agents/` after applying. A shared `_require_run_dir` helper prevents future drift.
- **Item 5** (`_make_approve_fn`) — this closure is shared by all 7 agents' approve commands. A logic error here breaks every approval workflow. Test all seven agents' approval paths after the change.
- **Item 4** (delete `docs/USER-MANUAL.md`) — verify GitHub Pages serves the updated link. Any CI step that checks `docs/USER-MANUAL.md` existence will need updating.
- **Item 6** (`AgentCLISpec` field addition) — check `tests/unit/test_cli.py` and `tests/unit/agents/*/test_agent.py` for spec structure assertions that will need updating.

---

## Definition of Done

Before tagging v1.0.2:
1. All 8 items above are closed (code + test).
2. `scripts/verify-release.sh` passes clean.
3. `scripts/run-cleanroom.sh` passes clean.
4. CHANGELOG `[1.0.2]` entry lists every fix with its ID.
5. No remaining instances of "six-stage" or "six stages" in the repo.
6. `docs/USER-MANUAL.md` deleted; both inbound links updated and verified.
