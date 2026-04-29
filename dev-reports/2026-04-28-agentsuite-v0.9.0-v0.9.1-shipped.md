# Dev Report — AgentSuite v0.9.0 + v0.9.1 (combined)

**Session:** 2026-04-28
**Project:** AgentSuite
**Scope:** Sprint 3 engineering hardening release. v0.9.0 = full feature surface tagged but the release workflow's CLI-smoke step failed against the bare wheel. v0.9.1 = same surface with a working release pipeline. Treat as a single Sprint 3 ship.
**State at report time:** v0.9.1 GH release live with 4 assets; CI 3/3 green; loop continues to v0.9.2.

---

## Summary

Sprint 3 closed all seven planned items plus surfaced (and fixed) two pre-existing bugs along the way. v0.9.0 is the intended Sprint 3 feature surface. v0.9.1 is the same surface with a working release pipeline — the v0.9.0 first tag run failed during the new clean-install CLI smoke step because the audit-venv didn't include the optional `[mcp]` extra. The hotfix installs the wheel with `[mcp]` so both `agentsuite --help` and `agentsuite-mcp --help` are validated before publish.

The full Sprint 3 plan is documented in `dev-reports/2026-04-28-sprint-plan-to-v1.0.md`. This release closes the v0.9.0 row of that plan.

---

## What was done

### Item 1 — Per-run cost telemetry (commit `19738a8`)

- New `Cost.model: str | None` field on the kernel cost type. Last-non-None wins under `Cost.__add__` aggregation so per-stage and total summaries reflect the most recent model recorded.
- `CostTracker` now tracks `per_stage: dict[Stage, Cost]`, exposes identity fields (`run_id`, `agent`, `provider`, `model`), and ships a frozen `summary()` schema and `save_summary(path)` persistence.
- `_drive()` sets `cost_tracker.current_stage` before each handler call and writes `cost_summary.json` to the run dir after every successful stage. Best-effort write also fires on failure so a crashed run leaves an authoritative cost record.
- Tests: 7 new (per-stage aggregation, current_stage=None passthrough, summary schema, canonical Stage ordering, save_summary nested dir, cap_warned tracking, model last-wins).
- **Surprise:** sprint plan said "raise cap default to $5". Default `hard_kill_usd` was already 5.0 in `agentsuite/kernel/cost.py`. The raise was a no-op; per-stage telemetry was the real win.

### Item 2 — RunState subclass-aware persistence + schema_version (commit `b1c0323`)

- `StateStore.save()` dumps `inputs` using the runtime instance's schema rather than the declared `RunState.inputs: AgentRequest` field type. Subclass-specific fields (`DesignAgentInput.campaign_goal`, `CIOAgentInput.organization_name`, etc.) survive save/load round-trip.
- Lazy importlib registry `_INPUTS_BY_AGENT` resolves agent name to its input subclass on `load()` so the kernel never imports agent packages at import time (avoids circular imports).
- New `SCHEMA_VERSION = 2` written to every `_state.json` envelope.
- New typed `RunStateSchemaVersionError` raised on load when on-disk version is missing or older. No automatic migration shipped — pre-v0.9 has no installed base outside the local workspace.
- ValidationError fallback to base `AgentRequest` preserves legacy fixture paths.
- Tests: 8 new (schema_version on disk, legacy reject, older-version reject, parametrised round-trip across all 7 agents). Existing "documents the limitation" test flipped to a positive assertion.

### Item 3 (lite) — Golden content assertions (commit `3076923`)

- New `tests/golden/_helpers.py` with `assert_artifact_exact()` (byte-stable text/JSON, unified-diff failure messages) and `assert_qa_within_tolerance(rtol=0.05)` (numeric scores + average; exact match on `passed` / `requires_revision` / `revision_instructions`; unknown keys raise `TypeError` so the schema can't silently drift).
- `load_qa_scores()` convenience parser.
- Founder snapshot extended with `brand-system.md` + `qa_scores.json` fixtures captured under deterministic mock LLM.
- Two new content-aware tests on Founder golden using the helpers.
- Makefile gains `update-goldens` target (alias for `resnap-golden`); CONTRIBUTING gains regenerate-and-review section.
- **Cut from v0.9.0 (deferred to v0.9.2):** content snapshots for the remaining 6 agents (Design, Product, Engineering, Marketing, TrustRisk, CIO). Mechanical roll-out following the Founder template — fast in v0.9.2.

### Item 4 — CIO date reproducibility (commit `09cafbc`)

- New `as_of_date: date | None = None` field on `CIOAgentInput`. `None` defaults to today's UTC date at execute time; explicit values let golden tests + retro reports pin rendered quarter / fiscal-year strings.
- New `_resolve_as_of(inp)` helper centralizes the "today vs. injected" decision so the date source is explicit and testable.
- `_current_quarter`, `_next_quarter`, `_current_fiscal_year`, `_fiscal_year_range` refactored to accept `as_of: date`. Naive `datetime.now()` replaced with `datetime.now(tz=timezone.utc)`.
- Tests: 3 new (as_of drives quarter strings; as_of=None defaults to today; year-boundary wrap Q4 → Q1+1; helper selector logic).
- **Surprise 1:** sprint plan said "replace `cio_name = strategic_priorities.split()[0]` hack". The hack didn't exist — `cio_name` has been a proper `CIOAgentInput` field with default since pre-v0.8.x. Sprint plan misidentified.
- **Surprise 2:** sprint plan said "replace hardcoded date literals". The code already used `datetime.now()` (naive). The real fix was tz-awareness + injectability, not literal removal.
- The remaining `priority_N_title` split hack on `strategic_priorities` has graceful fallbacks; deferred to a v0.9.x backlog rather than expanding scope here.

### Item 5 — Resume idempotency contract (commit `3e765cf`)

- `_drive()` now seeds the new `CostTracker` with `state.cost_so_far` on resume and rehydrates `per_stage` from the prior `cost_summary.json` (best-effort). Without this, resume would silently let a run that already spent $4 spend another $5 of cap.
- New integration test in `tests/integration/test_resume_idempotency.py`: billable+crashing mock fails on the Nth call, the first `agent.run` raises, the second `agent.run` resumes from saved state, asserts stages BEFORE the crashed stage are not re-billed and the carried-forward total matches `state.cost_so_far`.
- ADR-0007 updated mid-test with the crashed-stage caveat surfaced by the test: the failed stage itself legitimately re-bills on resume because stage-atomic restart can't know an agent's internal sub-call shape. In-stage checkpointing would break the kernel abstraction.

### Item 6 — ADR backfill (commit `41103e5`)

Seven Architecture Decision Records under `docs/adr/`, one paragraph per Context / Decision / Consequences section:

- 0001 — Rubric dimension count and selection (Founder 7 vs. others 9 stays as-is; symmetry is aesthetic, not signal-bearing)
- 0002 — RunState shape and resume contract (subclass-aware persistence + SCHEMA_VERSION)
- 0003 — LLM retry/timeout policy (RetryingLLMProvider default-on; settable `name` instance var)
- 0004 — MCP tool naming convention (`agentsuite_<agent>_<verb>`; no alias shim)
- 0005 — Cost cap vs. cost telemetry split (cap minimal; cost_summary.json layered)
- 0006 — No-PyPI distribution policy (GitHub releases only through v1.0)
- 0007 — Resume-from-failure idempotency contract (stage-atomic; no per-call rollback)

Index at `docs/adr/README.md` with shortened MADR template; CONTRIBUTING gains an "Architecture decisions" pointer.

**Surprise:** sprint plan said Founder rubric 7 vs. others 9 is a "real asymmetry to fix". On audit (ADR-0001) the dimensions cover the same signal under different names. The fix is "stop flagging this", not "expand Founder."

### Item 7 — Clean-install verification on tag push (commit `bb48a3e`)

- README install commands wrapped with `<!-- install:start -->` / `<!-- install:end -->` markers.
- Canonical fixture at `tests/fixtures/install-block.md` mirrors the README block byte-for-byte.
- New `scripts/check_install_block_drift.py` extracts the README block, diffs against the fixture, exits 1 with a unified diff on drift.
- `release.yml` gains a drift-check step before build (fails the release if README and fixture have desynced) and a smoke step after the wheel install that runs `agentsuite --help` and `agentsuite-mcp --help` from the clean `.audit-venv`.
- 4 unit tests on the extractor: marker present, marker missing raises, real-repo match, fake-divergence detected.
- **Windows matrix deferred to v0.9.x.** Ubuntu catches the common-case regression and the test infrastructure transfers identically when added.

### v0.9.0 final tag (commit `f170288`)

- Version bumped 0.8.4 → 0.9.0 across 7 files (pyproject, __version__, README, USER-MANUAL, docs/index.html, docs/troubleshooting.md, CHANGELOG).
- Comprehensive `[0.9.0]` CHANGELOG entry with sections: ⚠ BREAKING, Added, Changed, Fixed, Test counts.
- `verify-release.sh` ALL CHECKS PASSED.
- Tag pushed; CI green on lint + test; release workflow FAILED.

### v0.9.0 release-workflow failure (root cause)

```
.audit-venv/lib/python3.12/site-packages/agentsuite/mcp_server.py:65
ModuleNotFoundError: No module named 'mcp'
```

The `.audit-venv` was installed from the bare wheel (no extras). `agentsuite-mcp --help` triggers FastMCP's deferred import, which fails when the `[mcp]` extra isn't installed. The smoke step's `agentsuite-mcp --help` line failed; `softprops/action-gh-release` never ran; no v0.9.0 GH release was published.

### v0.9.1 hotfix (commit `b5a2b59`)

- `release.yml` smoke step now installs the wheel with `[mcp]` (`pip install "${WHEEL}[mcp]"`).
- Version bumped 0.9.0 → 0.9.1 across 7 files.
- `[0.9.1]` CHANGELOG entry calling out v0.9.0 as the intended surface and v0.9.1 as the working pipeline.
- Tag pushed; CI 3/3 green; GH release published with 4 assets.

---

## Verified

| Check | Result |
|---|---|
| `gh run list` v0.9.1 | release ✓, lint ✓, test ✓ |
| `gh release view v0.9.1 --json assets` | 4 assets: `agentsuite-0.9.1-py3-none-any.whl`, `agentsuite-0.9.1.tar.gz`, `agentsuite-0.9.1-sbom.cdx.json`, `pip-audit.json` |
| Test counts | 648 (v0.8.4 baseline) → 676 (v0.9.0 / v0.9.1). +28 tests across cost, RunState, CIO date, drift check, idempotency, golden helpers. 0 skipped. |
| `bash scripts/verify-release.sh` (v0.9.0 + v0.9.1) | ALL CHECKS PASSED both runs |
| Hard Rule 11 commit-size gate | Largest commit (v0.9.0 final): 93 ins / 10 del — well under 800. Tag-required `[LARGE-CHANGE]` token NOT triggered. |
| Hard Rule 4a (no skipped tests) | 0 skipped maintained from v0.8.3 onward |

---

## Not verified / deferred

- **Content snapshots for 6 agents** (Design, Product, Engineering, Marketing, TrustRisk, CIO): roll out the Founder pattern → v0.9.2.
- **Founder rubric audit one-pager** (the side-by-side dimension comparison): → v0.9.2.
- **Skip / deselect cleanup**: 3 `pytest --collect-only` deselected items still on the list. Each needs a paragraph in `docs/test-coverage.md` explaining why or a fix → v0.9.2 (Hard Rule 4a long-term posture; not a v1.0 blocker yet).
- **Screenshots + sample-output fixture (P4)**: → v0.9.3.
- **Windows-matrix clean-install verification**: → v0.9.x. Ubuntu coverage shipped in v0.9.0/v0.9.1.
- **Provider drift workflow first run**: scheduled for next Monday 09:00 UTC. Can be exercised manually via `gh workflow run provider-drift.yml` if Scott wants smoke validation sooner.
- **GPG-signed tags**: deferred to v1.0 setup. Decision pending from Scott.
- **`good-first-issue` ticket topics**: three suggestions on the table (CLI `--quiet` flag, USER-MANUAL Marketing example, `AGENTSUITE_OUTPUT_DIR` test). Not yet filed pending Scott confirmation.

---

## Broken / regressions

None remaining. v0.9.0's release-workflow failure was the regression of the session; v0.9.1 fixed it. v0.9.0 tag still exists in git as an audit-trail artifact but no GH release was published from it.

---

## Pre-existing bugs surfaced and fixed inline

1. **`_drive()` did not carry `state.cost_so_far` across resume** — discovered while writing the ADR-0007 idempotency test. Fresh `CostTracker` started at zero on every resume, silently allowing total cap to be exceeded across multiple attempts. Fixed in same commit as the test (Item 5).
2. **`release.yml` smoke step missed `[mcp]` extra** — discovered when v0.9.0's first tag run failed. Fixed in v0.9.1 hotfix.

Both were on v0.9.0's critical path; fixing them was scope-required, not opportunistic.

---

## Surprises that re-shaped the sprint

- **Cap default already $5.** Sprint plan target was a no-op. Per-stage telemetry was the real Item 1 deliverable.
- **CIO `cio_name` field already proper.** Sprint plan's "replace the strategic_priorities split hack" claim was mis-aimed at the wrong field; the real Item 4 fix was tz-aware date helpers + an `as_of_date` injection point.
- **Founder rubric 7-vs-9 is not a defect.** ADR-0001 records the decision: dimensions cover the same signal under different names; symmetry alone is aesthetic.
- **Crashed-stage re-bills on resume.** ADR-0007 originally said "stages 1–N not re-billed" without the caveat that the crashed stage itself runs again. The integration test surfaced this; ADR was updated mid-sprint with the architectural reason (in-stage checkpointing would break the kernel abstraction).

---

## Next decision needed

Three open Scott decisions for v1.0 prep:

1. **GPG-signed tags from v1.0?** ~30-minute setup (generate key, register on GitHub, configure git, backup private key). Standard for serious OSS. Recommend yes.
2. **Three `good-first-issue` topics for rc1.** Suggested: (a) CLI `--quiet` flag suppressing stage progress markers, (b) USER-MANUAL Marketing-agent example walkthrough, (c) unit test for `AGENTSUITE_OUTPUT_DIR` env var. Want different ones?
3. **Screenshot automation approach for v0.9.3.** pyautogui? Playwright for landing page only + `asciinema → svg-term-cli` for CLI captures? Or Scott captures by hand?

---

## Open watches

- Hard Rule 10 enforcement hook still live in workspace (Scott removed context-mode + watchdog this session, but Rule 10/11 hooks remain).
- Memory rule `feedback_no_subagents_inline_only.md` still active — all work inline.
- v0.9.2 next: rubric audit + skip cleanup + 6-agent golden content snapshots.
- Loop terminator: v1.0.0 GA tag.
