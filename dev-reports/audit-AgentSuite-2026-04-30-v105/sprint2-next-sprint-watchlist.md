# Next-Sprint Watchlist — AgentSuite Sprint 2 Remediation

**Audit date:** 2026-04-30
**Applies to:** v1.0.7 (commit eb9c175); items deferred from Sprint 2 audit

Forward-looking items. These do not belong in Sprint 2 remediation — most require architectural design, cross-surface coordination, or a product decision before the team can act. A team that ignores this list accumulates structural debt faster than it can pay it down.

---

## Structural / architectural

> Decisions and refactors that need to be planned, not rushed.

| # | ID | Role | What to consider | Trigger to act |
|---|---|---|---|---|
| 1 | ENG-S2-004 | Engineering | Move `check_path_confinement()` enforcement to each agent's intake stage so paths are validated once at the trust boundary, before any downstream stage can read them. Current advisory-only placement means a future stage added without checking the docstring creates a new exfiltration path silently. | Before adding any new agent stage that reads file paths from user input |
| 2 | ENG-S2-006 | Engineering | Add `frozen=True` to both `QAStageConfig` and `SpecStageConfig` dataclasses. Both are passed to kernel functions as configuration contracts; mutable config is a latent correctness risk if a stage accidentally mutates it. Change is one word per dataclass and zero blast radius. | Before Sprint 3 begins — low cost, high protection |
| 3 | Cross-2 | Engineering + QA | Establish a per-agent `WRITTEN_FILES` contract (either a constant list or a capability flag) that MCP tool builders and test helpers consult when constructing output file paths. Three CIO divergence findings in Sprint 2 all trace to the same root: `write_qa_report=False` was not visible to the tools. Without this contract, Sprint 3 will likely introduce a fourth divergence. | Before any new MCP tool is added to the CIO or trust_risk agent |
| 4 | Cross-3 | UX + QA | Consolidate `_stage_to_status()` from 7 identical copies in `agents/*/agent.py` into a single function in `agentsuite/kernel/base_agent.py` with 7 one-line imports replacing the duplicated bodies. As currently structured, adding a new `Stage` literal requires touching all 7 files; missing one produces a user-visible status inconsistency. | Before the next new stage type is added to any agent |

---

## Design debt

| # | ID | Role | What to consider |
|---|---|---|---|
| 1 | UX-A01 | UX | `list_runs` returns a silent `[]` when the `project_slug` filter yields no matches. Developers cannot distinguish a wrong slug from a project with no runs yet. Add a response envelope with a `filter_applied` field and a `context` string (e.g., `"No runs found for project_slug='X'. Check the slug or omit the filter to list all runs."`). Requires deciding on the return-type change across CLI and MCP surfaces for consistency before implementing — see Decisions section. |
| 2 | UX-A02 | UX | CLI `list-runs` output omits `started_at`. The MCP `RunSummary` shape includes it. Developers switching between CLI and MCP output get different fields with no explanation. Add `started_at` to CLI list output and update any test asserting the current shape. |
| 3 | UX-A05 | UX | `product/agent.py` requires `--project-slug` as a mandatory argument while all 6 other agent CLIs make it optional. The asymmetry is undocumented and creates a confusing inconsistency for developers using agents in sequence. Either document the reason (if intentional) or make it optional to match the other 6. |
| 4 | UX-A06 | UX | CLI `list-runs` has no `--project-slug` filter, unlike the MCP `list_runs` tool. Developers who primarily use the CLI lack feature parity for the project filtering introduced in Sprint 2. Add `--project-slug` option to the `list-runs` CLI command. |

---

## Documentation debt

| # | ID | Role | What to consider |
|---|---|---|---|
| 1 | DOC-S2-003 (partial) | Docs | DOC-S2-003 is on the Sprint 2 punch list for its highest-priority items (a, b, c). Items (d) path confinement error messages and (e) cost-warning-to-stderr change were deferred here. Once ENG-S2-001 is fixed, the USER-MANUAL.md §9 and `docs/troubleshooting.md` should describe what the path confinement error looks like and how users recover from it. |
| 2 | DOC-S2-005 | Docs | `docs/troubleshooting.md` was version-bumped to v1.0.7 but its content still reflects Sprint 1 behaviors. The cost-warning-to-stderr behavior change, path confinement errors, and `AGENTSUITE_COST_CAP_USD` malformed-value error message all need entries in the troubleshooting guide. This is the "remaining content gap" after DOC-S2-003 (punch list item 8) ships. |
| 3 | DOC-S2-006 | Docs | The architecture section in README-FULL.pdf and `docs/index.html` does not reflect the Sprint 2 kernel extraction (ENG-003). The kernel extraction was the sprint's most significant architectural change — the block diagrams should show `agentsuite/kernel/` as a shared foundation below the 7 agent modules, with arrows indicating that agent stage wrappers delegate to kernel functions. Update both artifacts together. |
| 4 | — | Docs (process) | The dual `### Fixed` sections and non-standard `### Documentation` section in CHANGELOG [1.0.7] suggest the CHANGELOG was assembled from two PR merges without a final editorial pass. Consider adding a "CHANGELOG review" gate to the pre-push checklist — confirm all sections under the version heading are merged and correctly typed before tagging a release. |

---

## Test-culture debt

| # | ID | Role | What to consider |
|---|---|---|---|
| 1 | TEST-S2-001 | Test | No test verifies that any of the 14 agent stage wrappers (`agents/*/qa.py`, `agents/*/spec.py`) correctly delegate to their kernel counterparts. A config-construction bug in any of these 14 files (wrong field name, missing argument, wrong default) would reach runtime before failing. Add `test_stages_spec_kernel.py` and `test_stages_qa_kernel.py` in `tests/unit/kernel/` — each test calls the wrapper with a known config and asserts the correct kernel function was called with the right arguments. |
| 2 | TEST-S2-002 | Test | The 7 revision cycle tests in `test_revision_cycle.py` hardcode the exact QA `system_msg` string from `founder/stages/qa.py` as the SequentialMockLLMProvider match key. If the prompt text is tuned (common during UX refinement), the mock fails to match and the test silently exercises a different code path than intended. Replace the hardcoded string with a fixture or constant imported from the source file, so changes to the prompt text don't invisibly break test routing. |
| 3 | TEST-S2-003 | Test | `tests/unit/kernel/test_stages_spec.py` covers `..` traversal, absolute paths, and valid in-project paths for `check_path_confinement()`. It does not test symlink traversal — a symlink pointing outside the project that resolves to an allowed path (or vice versa). Add a symlink test case using `tmp_path` with `os.symlink()`. Note the Windows junction-point behavior caveat from the "What we couldn't assess" section of the executive audit. |
| 4 | TEST-S2-004 | Test | Engineering, marketing, and trust_risk MCP tool tests were expanded in Sprint 2 but do not cover `run_id` traversal (reading an artifact from a run other than the most recent). The `get_artifact` tool supports arbitrary `run_id` — confirm a test exercises a non-default `run_id` to prevent regressions on that path. |
| 5 | TEST-S2-005 | Test | `AGENTSUITE_QUIET` suppression is tested at the unit level (cost format function). The pipeline-driver path — where the flag causes the running cost line to be omitted from the live output stream — has no integration test. Add a test that runs the Founder agent with `AGENTSUITE_QUIET=1` and asserts no cost line appears in stdout. |
| 6 | TEST-S2-006 | Test | The `agentsuite_cio_get_qa_scores` bug fix (ENG-S2-003/QA-S2-002, Sprint 2 punch list item 4) requires updating any existing test that asserts "scores not yet available" for a completed run. After fixing the filename, those tests will be asserting the broken behavior. Treat the test update as a required part of that fix, not a follow-up. |

---

## Performance and scaling

| # | ID | Role | What to consider | Trigger to act |
|---|---|---|---|---|
| 1 | ENG-S2-007 | Engineering | `GEMINI_PRICING` is a module-level dictionary with no prefix-match logic. As the Gemini API adds model sub-versions (e.g., `gemini-2.5-flash-preview-04-17`), each new sub-version that isn't an exact key causes a silent `KeyError`-or-fallback that silently zeroes out cost tracking. Design a prefix-match lookup (longest key prefix wins) so that `gemini-2.5-flash-preview-*` variants correctly resolve to the base `gemini-2.5-flash` pricing row. | Before adding any new Gemini model to the provider list |
| 2 | ENG-S2-008 | Engineering | `kernel/stages/spec.py:_read_voice_samples` reads all voice sample files sequentially inside a list comprehension. For agents configured with many voice samples (no current cap on the number of paths), this blocks the event loop. Consider an async read or a configurable cap on voice sample count with a clear error when exceeded. | Before any agent is configured with more than ~10 voice sample paths |
| 3 | ENG-S2-009 | Engineering | The cleanroom script (`scripts/run-cleanroom.sh`) spins up the full mock pipeline. As the number of agents and stages grows, direct-script invocation time will increase proportionally. Consider a `--agents` filter flag so developers can run the cleanroom against a single agent during targeted debugging without waiting for all 7. | When cleanroom wall-clock time exceeds 3 minutes |

---

## Decisions needing product / leadership input

> These aren't pure engineering fixes. They require a product or leadership call before the team can act.

- **UX-A01 return-type change** — Adding a context envelope to `list_runs` changes the response shape for both CLI and MCP consumers. Decide: (a) is this a breaking change requiring a MAJOR version bump, or (b) can the envelope be added as an additive wrapper (non-breaking)? The MCP shape is already an object, so (b) is viable for MCP; CLI output is currently a JSON array, so (a) applies there unless CLI output is switched to a wrapped object. Product needs to decide before Engineering implements.

- **CIO/trust_risk WRITTEN_FILES contract architecture** (Cross-2) — The CIO agent is the only one that sets `write_qa_report=False` and uses bare-stem artifact keys. The simplest contract is a per-agent constant; a more robust version is an agent capability flag checked at MCP tool registration time. The team needs to agree on which pattern before implementing so it doesn't need to be redesigned when the next divergence appears.

- **Gemini pricing table strategy** (ENG-S2-007) — The current `GEMINI_PRICING` dictionary approach requires a manual update every time Google releases a new sub-version. Alternatives: (a) prefix-match fallback with explicit gap logging, (b) fetch pricing from a config file outside the package (easier to update without a release), (c) accept the mismatch and require that the pricing table be updated with each Gemini SDK upgrade. Choose a strategy before ENG-S2-002 is closed so the fix is durable.

- **Path confinement enforcement tier** (ENG-S2-004) — Moving `check_path_confinement()` enforcement to intake (ENG-S2-004) changes when the error is raised: currently it's deferred to read time; after the fix it fires at manifest construction time. This is a user-visible behavior change for any operator who constructs manifests programmatically and handles path errors at read time. Product should decide whether this warrants a breaking-change entry in the CHANGELOG before the structural enforcement ships.

---

## Review cadence

Revisit this watchlist at:
- **Sprint 3 planning** — elevate TEST-S2-001 (delegation tests), ENG-S2-006 (frozen dataclasses), and Cross-3 (`_stage_to_status` consolidation) to the sprint if capacity allows — all are low-cost, high-protection items.
- **Sprint 4 planning** — the four structural/architectural items (ENG-S2-004, Cross-2, Cross-3, ENG-S2-006) should have a design decision by Sprint 4 even if implementation slips. Leaving them open into Sprint 5 risks entrenching the current pattern further.
- **Every MINOR release** — verify the Gemini pricing table covers all currently-supported model strings before tagging.
- **On any new agent addition** — re-read the Cross-2 CIO contract entry before writing the new agent's MCP tools.

---

## Items deferred from Sprint 2 punch list

These were considered for the Sprint 2 punch list and deliberately deferred:

| ID | Why deferred |
|---|---|
| ENG-S2-004 | Requires intake-stage redesign across 3+ agents — too large for a targeted remediation sprint |
| TEST-S2-001 | Requires new test infrastructure (`test_stages_spec_kernel.py`, `test_stages_qa_kernel.py`) — good Sprint 3 task, no current regression |
| TEST-S2-002 | Low risk today; high friction next time QA prompt text is tuned — flag before that happens |
| UX-A01 | Return-type change needs product decision on breaking-change classification before implementation |
| UX-A02 | CLI shape update; low risk; needs accompanying test update |
| DOC-S2-005 | After DOC-S2-003 ships, this is the remaining content gap — not urgent before v1.0.8 |

---

*Generated from the `audit-team` skill. Full detail for every ID in the matching role deep-dive (`sprint2-01-engineering-deepdive.md` through `sprint2-05-qa-deepdive.md`).*
