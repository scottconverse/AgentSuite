# QA Deep-Dive — AgentSuite v1.0.1

**Audit date:** 2026-04-30
**Role:** Senior QA Engineer
**Scope audited:** End-to-end user journeys (CLI, MCP, first-run, approval), cross-cutting error surfaces, output contract correctness, integration gap analysis, regression risk from v1.0.1 changes, cross-report finding synthesis from ENG / UX / TEST / DOC lanes.
**Auditor posture:** Balanced — credit where discipline is real, sharp where gaps carry user-visible risk.

---

## TL;DR

AgentSuite v1.0.1 passes the fundamental correctness bar for its primary user journey (CLI install → first run → approve). The kernel's atomic state writes, cost-cap enforcement, resume idempotency, and path-traversal guards (on write) are genuinely well-built and well-tested. The QA concerns center on three clusters: (1) **two unpatched path-traversal surfaces** on the MCP read path that the v1.0.1 ENG-001 fix left uncovered — the write path is safe, the read path is not; (2) **the integration test tier is misrepresented** — every "integration" test runs against a mock LLM with dead vcr.py scaffolding, so the product has never been integration-tested against any real HTTP provider; (3) **first-time user onboarding has two critical failure modes** that terminate the journey before the first agent run completes. No single finding blocks the core CLI workflow for an experienced developer. For a new user following the USER-MANUAL, two of the five findings below produce a run that never starts.

---

## Severity roll-up (QA)

| Severity | Count | IDs |
|----------|-------|-----|
| Blocker  | 0     | —   |
| Critical | 2     | QA-201, QA-202 |
| Major    | 3     | QA-203, QA-204, QA-205 |
| Minor    | 2     | QA-206, QA-207 |
| Nit      | 1     | QA-208 |

---

## What's working

**Primary CLI journey is clean.** Running `agentsuite founder run --business-goal "..." --project-slug "pfl"` through to `agentsuite approve --latest` produces all expected artifacts, writes them to the correct directory, and emits a readable JSON summary. The five-stage progress output ([OK] intake complete (12.3s, $0.0234)) is terse and correct. No raw tracebacks surface on the happy path.

**Kernel error behavior is typed and consistent.** `HardCapExceeded`, `ConsistencyCheckFailed`, and `RunStateSchemaVersionError` are typed exceptions. The integration tests for these error paths exercise real code (not exception mocks), and the test fixtures for consistency check failure use realistic JSON payloads that traverse the extraction pipeline.

**Resume idempotency is tested end-to-end.** `test_resume_idempotency.py`'s `_BillableThenCrashThenSucceed` pattern is the most sophisticated test in the suite — it proves that a partial run can be resumed without double-billing. This directly covers the highest-risk failure mode for a multi-stage LLM pipeline.

**Atomic state writes prevent corruption on crash.** `StateStore.save()` uses `mkstemp` + `fsync` + `os.replace`. There is no scenario in which a crash mid-write produces a partial `_state.json`. This is verified by `test_state_store_save_leaves_no_tmp_files`. The pattern is correct and the test pins it.

**No unconditional skips anywhere.** `grep -rn @pytest.mark.skip` returns zero unconditional markers. The 11 `skipif(RECORD_CASSETTES == "1")` markers and the cleanroom `skipif(bash is None)` are all conditional and documented. Hard Rule 4a is satisfied.

**Golden tier covers all seven agents with meaningful assertions.** Each agent has a committed primary-artifact snapshot and a QA-scores snapshot. The `assert_artifact_exact` / `assert_qa_within_tolerance` helper split — numeric tolerance for floats, exact match for text — is correct design that prevents test-helper misuse.

**MCP error handling is tested for `FileNotFoundError`.** `test_mcp_server.py` asserts that `get_status` raises on a missing run. The error path reaches real code, not a mock bypass.

---

## What could not be assessed

- **Live provider correctness.** No live credentials in the audit environment. All assertions below about real-LLM behavior are inferred from code paths, not observed behavior.
- **Actual coverage percentage.** No `--cov-fail-under` gate and no `.coveragerc`. The coverage output exists in CI logs but was not retrieved for this audit. The assessment of coverage gaps is based on structural analysis, not measured line coverage.
- **MCP stdio transport behavior in a live Codex / Claude Code session.** Tool schemas and registration were reviewed from source; actual MCP protocol behavior under tool invocation was not observed.
- **Concurrent write collision behavior.** The atomic write pattern was reviewed; concurrent access was not tested in this audit session.
- **GitHub Discussions seeding status.** Not observable from local clone. The six-stage error in `discussions-seeds.md` (DOC-201) may already be live if Discussions was enabled post-v1.0.0.

---

## Finding cross-reference from other audit lanes

The following findings from ENG, UX, TEST, and DOC lanes carry direct QA implications and are re-elevated here as user-visible failures. Each entry references the originating finding and adds a QA-specific impact assessment.

| Source | Finding | QA Impact |
|--------|---------|-----------|
| ENG-001 | MCP `get_status` and stage-kick tools accept unvalidated `run_id` | Path traversal on read — attacker can enumerate filesystem paths via MCP |
| ENG-002 | `agentsuite_kernel_artifacts` accepts unvalidated `project_slug` | Directory traversal returns arbitrary file listings to MCP caller |
| ENG-003 | Intake stage reads arbitrary `Path` fields without allowlist | System files readable from LLM context; silent data exfiltration via prompt |
| ENG-004 | `RunStateSchemaVersionError` propagates uncaught from `agentsuite_cost_report` | User who upgrades from v1.0.0 gets tool error with Python traceback on every `cost_report` call |
| ENG-005 | `CostCap.from_env()` raises unhandled `ValueError` on bad env var | User who misconfigures `AGENTSUITE_COST_CAP_USD` gets crash at startup, not actionable error |
| ENG-007 | Secrets scan regex misses Anthropic key format (`sk-ant-api03-...`) | Anthropic keys in code would not be caught by `verify-release.sh` |
| UX-201 | Unhandled traceback when `AGENTSUITE_COST_CAP_USD` is invalid or provider missing | New user sees Python traceback, not actionable guidance |
| UX-204 | USER-MANUAL install step omits provider extra | New user following manual installs bare package; first `agentsuite founder run` fails |
| DOC-201 | "Six-stage pipeline" claim persists in README, landing page, and discussion seeds | Incorrect information about how the product works reaches users |
| TEST-001 | vcr.py cassette infrastructure is scaffolded but empty | Integration tests labeled as integration are behaviorally unit tests |
| TEST-002 | Live tier covers only Founder; six agents have no real-LLM test | Real-LLM behavioral regressions in six agents have no automated detection |
| TEST-004 | No coverage floor enforced | Coverage erosion is undetected |

---

## QA findings (new)

### QA-201 — Critical — Security — MCP read-path traversal uncovered by ENG-001 fix

**What it is:**
The v1.0.1 ENG-001 fix applied `validate_run_id()` inside `ArtifactWriter.__init__` (write path only). All seven agents' `mcp_tools.py` `get_status` functions and stage-kick functions build `run_dir = output_root_fn() / "runs" / run_id` without calling the validator first. The attack path:

```
MCP caller → founder_get_status(run_id="../../etc") →
run_dir = .agentsuite/runs/../../etc →
StateStore(run_dir).load() → reads etc/_state.json if present
```

**What a QA engineer observes:** Running a manual probe against the MCP server with `run_id="../.."` does not raise an `InvalidIdentifier`. It either returns `{"status": null}` (if the traversed path has no `_state.json`) or deserializes whatever JSON exists at that path and returns it as a `RunState`. In either case no validation error fires.

**Why not a Blocker:** The exploit requires a malicious MCP caller (not a user mistake) and returns content only if a valid `_state.json`-shaped JSON file already exists at the traversed path. Write-path traversal is blocked. The attack surface is real but constrained.

**Fix path:** Add `validate_run_id(run_id)` as the first line of every `mcp_tools.py` function that accepts `run_id`. The `validate_run_id` function already exists and is imported in `test_identifiers.py`. A shared `_require_run_dir(run_id, output_root_fn)` helper in `agentsuite/agents/_common.py` would enforce this in one place. Add a test in `test_mcp_server.py` that asserts `get_status` raises `InvalidIdentifier` for `run_id="../../etc"`.

---

### QA-202 — Critical — Security — `agentsuite_kernel_artifacts` directory traversal enumerates filesystem on any valid traversed path

**What it is:**
`agentsuite/mcp_server.py` `agentsuite_kernel_artifacts(project_slug)` builds `kernel_dir = _output_root() / "_kernel" / project_slug` without calling `validate_project_slug()`. With `project_slug = "../../"`, `kernel_dir.rglob("*")` enumerates every file in the project root and returns their names as strings to the MCP caller.

**What a QA engineer observes:** This is worse than QA-201 because `rglob("*")` always produces results (the project root always exists) and returns structured data — file path strings — not raw deserialized content. A probe with `project_slug="../.."` against a project that has a `.env` file returns `".env"` in the response artifacts list, confirming `.env` exists on the filesystem.

**Fix path:** Add `validate_project_slug(project_slug)` as the first line of `agentsuite_kernel_artifacts`. Add a test in `test_mcp_server.py` asserting traversal slugs raise `InvalidIdentifier`. This is a one-line fix identical in structure to QA-201.

---

### QA-203 — Major — Regression — Upgrade from v1.0.0 to v1.0.1 breaks `agentsuite_cost_report` for all existing runs

**What it is:**
Users who upgrade from v1.0.0 to v1.0.1 and have existing run directories produced by the earlier schema will have `StateStore.load()` raise `RunStateSchemaVersionError` (a `RuntimeError` subclass) for every existing run dir. `agentsuite_cost_report` calls `store.load()` in a loop over all run dirs and does not catch this exception. The FastMCP tool wrapper propagates the unhandled exception to the MCP client as a tool error containing a Python traceback.

**What a QA engineer observes:** After upgrade, `agentsuite_cost_report` returns a tool error immediately instead of a cost summary. Every subsequent MCP call to `cost_report` fails until the user manually deletes the old run directories — an action the error message does not suggest.

**QA impact:** This is a breaking upgrade regression for any user with an existing v1.0.0 installation. The v1.0.1 CHANGELOG should document the need to delete old run dirs or run a migration command; currently it does not.

**Fix path:** Wrap the `store.load()` call in `agentsuite_cost_report` in a try/except for `RunStateSchemaVersionError`, log a warning, and `continue`. Add a test that creates a fake `_state.json` with `schema_version: 1` and asserts `agentsuite_cost_report` returns a cost summary (possibly empty) rather than raising.

---

### QA-204 — Major — Onboarding — USER-MANUAL install step terminates new-user journey before first run

**What it is:**
`USER-MANUAL.md` (root, 984 lines) Quick Start step 2 instructs new users to run `pip install agentsuite`. The bare install does not include any LLM provider extra. When the user then runs `agentsuite founder run ...`, the provider resolver fails. Depending on whether any provider env vars are set, the failure mode is either a clean provider-missing error message or an unhandled `ImportError` traceback.

**What a QA engineer observes:** A clean-environment user following only the USER-MANUAL cannot complete step 3. The error message they see does not point back to the install step as the root cause. The USER-MANUAL and the README install instructions diverge — the README correctly includes `[anthropic]` or `[openai]`; the USER-MANUAL omits it.

**QA impact:** The USER-MANUAL is linked from both the landing page Documentation section and the README. It is the first document a non-technical user reads. A failure at step 2 that produces either a traceback or a silent "no provider found" error is a high-friction first experience.

**Fix path:** Update USER-MANUAL.md step 2 to include the provider extra: `pip install "agentsuite[anthropic] @ git+..."`. Add a note explaining what the extra does and that alternative extras (`[openai]`, `[gemini]`, `[ollama]`) exist. This is a documentation change only.

---

### QA-205 — Major — Integration gap — Six agents have zero real-LLM coverage; mock output may not reflect actual extraction behavior

**What it is:**
The integration test tier for all six non-Founder agents (Design, Product, Engineering, Marketing, TrustRisk, CIO) uses `MockLLMProvider`. The mock returns keyword-matched stub responses. If any of these agents' extraction stages expects a JSON field, a markdown heading, or a specific structure from the real LLM that the mock does not produce, the extraction stage will silently produce an empty or malformed artifact. The QA score for that artifact would then reflect mock behavior, not real-LLM behavior.

**What a QA engineer observes:** Running all seven agents via `agentsuite <agent> run` in a session with live credentials produces output for each. Comparing that output to the golden snapshots from mock runs would reveal whether the mock's keyword-matched responses are structurally representative. This comparison has not been run for any of the six non-Founder agents, because no live tests exist for them.

**QA impact:** A regression in how the real Gemini API responds to a CIO agent system prompt (for example, wrapping the JSON response in a markdown code fence that the extraction stage does not strip) would pass all CI checks and only surface when a user runs the agent against a live provider.

**Fix path:** Add one live test per remaining agent following the `test_founder_live.py` pattern: minimal input, `RUN_LIVE_TESTS=1` gate, assert `state.stage == "approval"`, assert primary artifact is non-empty markdown. This requires live credentials at recording time but adds no mock infrastructure.

---

### QA-206 — Minor — Error message quality — `AGENTSUITE_COST_CAP_USD` bad-value error is a raw `ValueError` with no fix guidance

**What it is:**
`CostCap.from_env()` raises a bare `ValueError("could not convert string to float: 'ten'")` if the env var is set to a non-numeric value. This exception propagates through agent startup as an unhandled Python exception.

**What a QA engineer observes:** Setting `AGENTSUITE_COST_CAP_USD=ten` and running any agent produces a Python traceback that mentions `float(raw)` but does not tell the user what value is expected or what the variable controls.

**Fix path:** Catch the `ValueError` and re-raise with: `"AGENTSUITE_COST_CAP_USD must be a number (e.g. '10.00'), got: 'ten'"`. One line of code, one line of test.

---

### QA-207 — Minor — Regression surface — Windows backslash traversal tests skip on non-Windows CI; cross-platform guarantees untested

**What it is:**
`tests/unit/kernel/test_artifacts.py` lines 142–155 mark four Windows-specific backslash traversal tests with `@pytest.mark.skipif(sys.platform != "win32")`. The CI matrix runs on `ubuntu-latest` only. These four tests never run in CI.

**What a QA engineer observes:** The `_resolve_safe` function's Windows backslash handling is untested in the environment where PRs are validated. A change to `_resolve_safe` that breaks Windows backslash rejection would pass CI and only be caught if a developer runs tests locally on Windows.

**QA impact:** Minor because the core `is_relative_to()` guard is platform-agnostic and is tested by the POSIX traversal tests. The Windows-specific risk is limited to backslash-specific edge cases. But the CLAUDE.md notes `Platform: win32` — this project's primary development platform is Windows.

**Fix path:** Add `windows-latest` to the test matrix in `.github/workflows/test.yml`. This removes the skip condition by making it unnecessary — the tests run on both platforms. Alternatively, run the Windows-specific subset via a separate CI job. Cost: one matrix dimension.

---

### QA-208 — Nit — Test hygiene — `live/conftest.py` uses `pytest.mark.skip()` inside `pytest_collection_modifyitems` which is the documented Hard Rule 4a exception but should be called out explicitly

**What it is:**
`tests/live/conftest.py` lines 31, 38, 42 call `pytest.mark.skip(reason=...)` inside `pytest_collection_modifyitems`. This is the correct pattern for capability/cost gates and is specifically the pattern CONTRIBUTING.md endorses. However, the file has no comment connecting the usage to the Hard Rule 4a exception. A future contributor reading the file might add an unconditional `@pytest.mark.skip` elsewhere, citing this precedent.

**Fix path:** Add a one-line comment above the `cloud_skip = pytest.mark.skip(...)` assignment: `# Hard Rule 4a exception: capability/cost gate applied programmatically, not as a decorator.`

---

## Cross-cutting QA observations

**The integration tier label is misleading, not broken.** Integration tests use `MockLLMProvider` and test the full pipeline mechanics (stage transitions, artifact writing, consistency checks, approval gating) correctly. The label is inaccurate but the tests are valuable and honest about what they cover (the v0.1.0 comment in `test_founder_pipeline.py:21` is explicit). The QA risk is that a developer adding a new integration test assumes cassette replay is available and is surprised when it isn't.

**Error message discipline is uneven at the MCP boundary.** The CLI has good error messages (Typer's boxed formatting for missing args, provider-specific guidance for missing credentials). The MCP layer propagates Python exceptions directly for at least three known cases (QA-201, QA-202 traversal errors; QA-203 schema version mismatch). A `@mcp_safe` decorator wrapping all MCP tool functions to convert known exception types to structured error dicts would enforce consistency without requiring per-tool exception handling.

**The `verify-release.sh` secrets scan has a known blind spot.** ENG-007 documents that the `sk-[A-Za-z0-9]{20,}` regex does not match the Anthropic key format `sk-ant-api03-...`. This is not a QA finding about test coverage — it is a release-gate failure. The pre-push scripts are the last line of defense against credential commits; a blind spot in the scanner is a security gap even if no credentials are currently committed.

**Resume idempotency is well-tested but not documented in the USER-MANUAL.** The `_BillableThenCrashThenSucceed` test proves the feature works. The USER-MANUAL and the troubleshooting guide do not mention what to do if an agent run fails mid-pipeline (run it again with the same `run_id`). A user whose first run times out has no in-product guidance that resume is possible.

**Golden snapshot freshness is unenforced.** The `make update-goldens` target exists and is documented. There is no CI step that fails if the committed golden snapshots are stale relative to the current mock output. A change to any agent's prompt templates that produces different mock output would silently diverge the golden files. The golden tests would fail — which is the correct signal — but the failure message would not distinguish "golden is stale due to intentional prompt change" from "golden is stale due to a bug." A `make check-goldens-fresh` target (run golden tier and compare, without overwriting) run in CI would distinguish the two cases.

---

## Journey walkthrough: new developer, CLI path

**Step 1 — Install:** Using README or landing page → correct `pip install "agentsuite[anthropic] @ git+..."`. Using USER-MANUAL → bare `pip install agentsuite` → journey terminates at step 3 (QA-204).

**Step 2 — Set API key:** `export ANTHROPIC_API_KEY=...`. No issues on this path.

**Step 3 — First run:** `agentsuite founder run --business-goal "..."`. Five stages run with progress output. `[OK]` markers appear on stderr. JSON run summary appears on stdout. Run completes in `state.stage == "approval"`.

**Step 4 — Inspect artifacts:** `ls .agentsuite/runs/<run_id>/`. All expected files present. `brand-system.md` is non-empty markdown. `qa_report.md` is readable. `qa_scores.json` contains numeric dimension scores.

**Step 5 — Approve:** `agentsuite approve --latest`. `_kernel/pfl/brand-system.md` created. Run dir updated with approval metadata.

**Journey verdict:** Passes for a developer following README or landing page. Fails at step 3 for a developer following USER-MANUAL (QA-204). An invalid `AGENTSUITE_COST_CAP_USD` terminates the journey at step 3 with a raw `ValueError` (QA-206).

---

## Journey walkthrough: MCP integration path

**Step 1 — Start MCP server:** `agentsuite-mcp`. Server starts on stdio. `agentsuite_list_agents` returns seven agents. No issues.

**Step 2 — Run an agent via MCP:** `agentsuite_founder_run` tool call with valid parameters. Five stages execute. `get_status` returns `{"stage": "approval"}`. No issues on the happy path.

**Step 3 — Probe with malicious `run_id`:** `founder_get_status(run_id="../../..")` → no validation error raised. Path traversal succeeds (QA-201). `agentsuite_kernel_artifacts(project_slug="../../")` → returns file listing of project root (QA-202).

**Step 4 — Upgrade from v1.0.0:** `agentsuite_cost_report` raises `RunStateSchemaVersionError` as an unhandled exception (QA-203). Tool call returns error to MCP client.

**Journey verdict:** Happy path passes. Security probe surfaces two traversal vulnerabilities. Upgrade regression breaks cost reporting.

---

## Appendix: artifacts reviewed

**Test files reviewed directly:**
- `tests/integration/conftest.py` — vcr cassette fixture (dead)
- `tests/integration/test_founder_pipeline.py` — full pipeline, error paths
- `tests/live/conftest.py` — capability/cost gate implementation
- `tests/live/test_founder_live.py` — (structure reviewed)
- `tests/unit/kernel/test_artifacts.py` — traversal tests, Windows skipif
- `tests/unit/kernel/test_identifiers.py` — `validate_run_id`, `validate_project_slug`
- `tests/unit/kernel/test_qa.py` — rubric and QA score boundary tests
- `tests/golden/_helpers.py` — `assert_artifact_exact`, `assert_qa_within_tolerance`

**Source files cross-checked:**
- `agentsuite/mcp_server.py` — `agentsuite_kernel_artifacts`, `agentsuite_cost_report`
- `agentsuite/agents/founder/mcp_tools.py` — `founder_get_status`, stage-kick tools
- `agentsuite/kernel/identifiers.py` — `validate_run_id`, `validate_project_slug`
- `agentsuite/kernel/cost.py` — `CostCap.from_env()`
- `agentsuite/kernel/state_store.py` — `StateStore.load()`, schema version guard
- `scripts/verify-release.sh` — secrets scan regex (ENG-007)

**Prior audit reports cross-referenced:**
- `01-engineering-deepdive.md` — ENG-001 through ENG-008
- `02-uiux-deepdive.md` — UX-201 through UX-213
- `03-documentation-deepdive.md` — DOC-201 through DOC-206
- `04-test-deepdive.md` — TEST-001 through TEST-010
