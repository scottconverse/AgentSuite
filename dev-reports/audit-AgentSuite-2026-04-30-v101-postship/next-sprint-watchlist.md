# Next-Sprint Watchlist — AgentSuite v1.0.1 Post-Ship Audit

**Audit date:** 2026-04-30
**Planning target:** v1.0.2 / v1.1.x sprints
**Source:** `00-executive-audit.md` — forward-looking items, not in scope for the immediate v1.0.2 punch list

These are structural, scaling, and polish concerns that don't block v1.0.2 shipping but will compound if deferred indefinitely. Review at the start of each sprint and pull items forward as capacity allows.

---

## Security

| ID | Severity | Effort | What to watch |
|---|---|---|---|
| ENG-003 | Major | L | Intake stage reads arbitrary filesystem paths supplied via `inputs_dir`, `brand_docs`, and `screenshots` parameters without an allowlist. A user (or MCP client) can point these at any readable path on the host. Add `AGENTSUITE_INPUT_ROOT` env var or enforce CWD-relative paths only. This is the highest-effort item here and warrants its own ADR before implementation. |
| ENG-007 | Minor | S | Secrets-scan regex `sk-[A-Za-z0-9]{20,}` misses Anthropic key format (`sk-ant-...` with hyphens and underscores). Fix pattern to `sk-[A-Za-z0-9_-]{20,}` or adopt `gitleaks` for a maintained ruleset. |

---

## Engineering

| ID | Severity | Effort | What to watch |
|---|---|---|---|
| ENG-005 / QA-206 | Minor | S | `CostCap.from_env()` raises a bare `ValueError` when `AGENTSUITE_COST_CAP_USD` is set to a non-numeric value. Catch and re-raise with an actionable message: "AGENTSUITE_COST_CAP_USD must be a positive number; got '{val}'". |
| ENG-006 | Minor | S | `OpenAIProvider.default_model()` returns `"gpt-5.4"`. Verify this model ID is live in OpenAI's production API. If not, update to a current model (e.g. `"gpt-4o"` or `"gpt-4-turbo"`). |
| ENG-008 | Nit | S | Inline `import os`, `import sys`, `import time` in `base_agent.py` should move to module top level for clarity and to satisfy import-order linters. |

---

## UX / CLI

| ID | Severity | Effort | What to watch |
|---|---|---|---|
| UX-203 | Major | S | `approve` command output is missing promoted artifact paths. Add `kernel_dir` and `promoted_count` to the JSON output so downstream scripts (and MCP clients) know where to find the approved artifacts without directory-scanning. |
| UX-205 / DOC-204 | Major | S | `trust_risk` (underscore) is the correct identifier, but README MCP config blocks use the hyphen form (`trust-risk`). This breaks MCP wiring silently. Standardize to underscore everywhere; add a `docs/troubleshooting.md` entry for this common mistake (one entry exists for the CLI — the MCP version is missing). |
| UX-206 / DOC-203 | Major | S | The README Status section and the landing page still show a "v0.8 Next Agent" roadmap card with placeholder text. Replace with v1.0.2 and v1.1.x items from CHANGELOG `[Unreleased]`. |
| UX-207 | Minor | S | The `--quiet` CLI flag's help text leaks internal audit IDs ("suppresses UX-006/QA-005 verbosity"). Replace with plain-language description. |
| UX-208 | Minor | S | `list-runs` subcommand is only registered on `trust_risk` and `cio` agents. Set `has_list_runs=True` for all seven agents for consistency. |
| UX-209 | Minor | S | Founder and Design agent subcommand help text is generic ("Run the agent pipeline"). Add descriptive one-liners specific to each agent's output artifact. |
| UX-210 | Minor | S | Sample output in README references internal dev-report paths and audit vocabulary. Replace with realistic user-project output. |

---

## Tests

| ID | Severity | Effort | What to watch |
|---|---|---|---|
| TEST-001 | Critical | M | **Resolve the vcr cassette ambiguity.** The vcr scaffolding (11 `skipif` guards, `conftest.py` fixture, `vcrpy` dev dependency, `tests/cassettes/` directory) is all in place but no cassettes have been recorded. This means the "integration" tier is unit tests with live network calls skipped — not replay integration tests. Two honest paths: (a) Record cassettes against real providers and check them in — tests become genuine HTTP replay tests. (b) Remove all vcr scaffolding and treat `RUN_LIVE_TESTS=1` as the only live gate. Either is correct; leaving the scaffolding as an implied promise is not. |
| TEST-002 | Major | L | Add one live test per remaining six agents following the `test_founder_live.py` pattern (requires `RUN_LIVE_TESTS=1`, capped at $10 total, runs only on v0.X.0 tags). Currently only Founder has a live test. |
| TEST-003 | Major | S | Update `CONTRIBUTING.md` and `docs/test-coverage.md` with the current test count (782 in default invocation, 785 with extras). Consider a CI-generated badge so the count stays current automatically. |
| TEST-004 | Major | S | Measure the current coverage floor with `pytest --cov=agentsuite --cov-report=term-missing`, then add `--cov-fail-under=<measured_floor>` to the CI test command. Close the open "will be considered for rc1" note in `docs/test-coverage.md`. Establish the floor from the measured value — don't guess. |
| TEST-005 | Major | M | The SVG extractor in `test_readme_cli_invocations.py` is coupled to rich's specific SVG output format with no unit tests. Add a synthetic SVG fixture test so regressions in the extractor are caught without running a full CLI invocation. |

---

## Documentation

| ID | Severity | Effort | What to watch |
|---|---|---|---|
| DOC-205 | Major | S | Three documents cite three different test counts (CONTRIBUTING.md says 689, test-coverage.md says 777, actual is 782). Sync all three to the current value in a single commit. |
| DOC-206 | Minor | S | `--quiet`, `AGENTSUITE_LLM_MAX_ATTEMPTS`, and `AGENTSUITE_LLM_TIMEOUT_SECS` are implemented and functional but not listed in README or USER-MANUAL configuration tables. Add them. |

---

## CI / Infrastructure

| ID | Severity | Effort | What to watch |
|---|---|---|---|
| QA-207 | Minor | S | The test matrix runs only on `ubuntu-latest`. Windows path-handling (backslash traversal in `validate_run_id`, `ArtifactWriter._resolve_safe`) is not CI-tested. Add `windows-latest` to the test matrix so Windows-specific edge cases are caught before release. |

---

## Ordering Guidance

If pulling items into v1.0.2 sprint beyond the punch list, suggested priority:

1. **TEST-001** (vcr ambiguity) — architectural decision, should be made once rather than deferred again
2. **ENG-003** (intake path traversal) — second traversal surface after the MCP fix
3. **UX-203** (approve output paths) — frequently requested by MCP integrators
4. **UX-205/DOC-204** (trust_risk underscore) — causes silent wiring failures
5. **TEST-004** (coverage floor) — closes the open note and locks in a quality floor
6. Everything else in effort order (S before M/L)
