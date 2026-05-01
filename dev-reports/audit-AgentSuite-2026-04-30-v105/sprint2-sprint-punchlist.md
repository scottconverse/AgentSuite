# Sprint Punch List — AgentSuite Sprint 2 Remediation

**Audit date:** 2026-04-30
**Applies to:** v1.0.7 (commit eb9c175); fix before v1.0.8

This list covers fixes that should ship before Sprint 3 (19 Minor findings) begins. All Criticals and the highest-leverage Majors are here. Items are ordered by suggested work sequence — see the Sequencing section.

---

## Must-fix (Criticals)

| # | ID | Severity | Role | What to do | Size |
|---|---|---|---|---|---|
| 1 | ENG-S2-001 | Critical | Engineering | In `agentsuite/agents/founder/stages/spec.py:_read_voice_samples`, call `check_path_confinement(Path(path), project_dir)` before each `path.read_text()`. Pass `project_dir` from caller (use run_dir parent or configured project root). Import `check_path_confinement` from `agentsuite.kernel.stages.spec`. Add a test asserting that an out-of-project path raises `ValueError`. | S |
| 2 | ENG-S2-002 | Critical | Engineering | In `agentsuite/llm/gemini.py:54–60`, extract `actual_model = getattr(result, 'model_version', None) or model` and use `actual_model` for both `LLMResponse.model` and `_cost_usd(actual_model, ...)`. Verify `GEMINI_PRICING` has a key that matches API-returned sub-version strings (e.g., `gemini-2.5-flash-preview-04-17`) or add prefix-match fallback before fixing. | S |
| 3 | QA-S2-001 | Critical | QA | Fix cleanroom script failing when run directly (outside pytest). **Option A (preferred):** Add `AGENTSUITE_ALLOW_MOCK_FACTORY` env var check to `cli.py:78` guard: `if factory and not os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("AGENTSUITE_ALLOW_MOCK_FACTORY"):`. Then add `export AGENTSUITE_ALLOW_MOCK_FACTORY=1` in the mocked-mode block of `scripts/run-cleanroom.sh`. **Option B:** Add `export PYTEST_CURRENT_TEST="cleanroom::mocked"` to the mocked-mode block in the script. Either option unblocks the cleanroom for direct invocation. | S |

---

## Should-fix (high-leverage Majors)

| # | ID | Severity | Role | What to do | Size |
|---|---|---|---|---|---|
| 4 | ENG-S2-003 / QA-S2-002 | Major | Eng + QA | Change `qa-scores.json` (hyphen) to `qa_scores.json` (underscore) at `cio/mcp_tools.py:198` AND `trust_risk/mcp_tools.py:194`. Both tools currently read a file that never exists. Fix both in one commit. Update any test that asserts "scores not yet available" for a completed run. | S |
| 5 | QA-S2-003 | Major | QA | In `agentsuite/agents/cio/mcp_tools.py`, update the `RevisionRequired` handler (lines 109–115) to return `qa_scores_path` pointing to `qa_scores.json` instead of `qa_report_path` pointing to `qa_report.md`. CIO sets `write_qa_report=False`; `qa_report.md` never exists for CIO runs. Fix the `action` message to say "Review qa_scores.json" not "qa_report.md". | S |
| 6 | DOC-S2-001 | Major | Docs | Update `README.md` line 5: change `**v1.0.6**` to `**v1.0.7**`. | XS |
| 7 | DOC-S2-002 | Major | Docs | Fix `USER-MANUAL.md` Troubleshooting §10 (lines 847–851) and Glossary (line 903): replace the `ConsistencyCheckFailed` exception description with the current `consistency_report.json` review flow. The per-agent error tables (7 chapters) were already fixed in Sprint 2; only §10 and the Glossary remain. See `sprint2-03-documentation-deepdive.md` for exact replacement text. | S |
| 8 | DOC-S2-003 | Major | Docs | Document five Sprint 2 behaviors in user-facing docs: (a) `awaiting_approval` status field value — add a `### ⚠ BREAKING` note in USER-MANUAL.md §5 or a new "Output reference" section with migration hint (`if status in ("approval", "awaiting_approval"):`); (b) `AGENTSUITE_COST_CAP_USD` malformed value error — add to USER-MANUAL.md §9 and `docs/troubleshooting.md` section 6; (c) `project_slug` filter on `list_runs` — add to CLI reference. Items (d) path confinement errors and (e) cost-warning-to-stderr change are lower priority and can go to next sprint. | M |
| 9 | DOC-S2-004 | Major | Docs | Merge the two `### Fixed` sections in `CHANGELOG.md [1.0.7]` into one. Rename `### Documentation` to `### Added`. Add a `### ⚠ BREAKING` header before the `awaiting_approval` rename bullet to match v0.9.0 and v0.8.2 format. See exact restructured entry in `sprint2-03-documentation-deepdive.md`. | S |

---

## Suggested sequencing

**Start with the Criticals — in this order:**

1. **QA-S2-001 first** (30 minutes) — cleanroom must be working before any other changes can be verified via cleanroom. Fix the script + guard, then run `./scripts/run-cleanroom.sh` directly to confirm it passes.

2. **ENG-S2-001 second** (1–2 hours) — the security gap is the highest-risk item. After fixing `_read_voice_samples`, run the full test suite to confirm no regressions, and add the out-of-project path test.

3. **ENG-S2-002 third** (1 hour) — requires checking `GEMINI_PRICING` key coverage first. If keys need updating, that's scope to confirm before editing `gemini.py`.

**Then the CIO fixes together:**

4. **Items 4 and 5** (30 minutes combined) — `ENG-S2-003/QA-S2-002` and `QA-S2-003` are in the same file and the same agent. Fix both `qa-scores.json` filename bugs and the `approve` error path in one commit. Run the CIO test suite after.

**Then documentation (can be parallelized):**

5. **Items 6, 7, 8, 9** — these are independent of code changes and can be done in any order. README.md (item 6) is 30 seconds. CHANGELOG restructure (item 9) is 15 minutes. DOC-S2-002 (item 7) and DOC-S2-003 (item 8) together are about 1–2 hours.

**Dependencies:**
- Items 4 and 5 share the same file (`cio/mcp_tools.py`) — do them in one edit session to avoid conflicts.
- ENG-S2-002 depends on checking `GEMINI_PRICING` first — don't fix `gemini.py` until you've confirmed key coverage.
- Item 8 (DOC-S2-003 breaking change doc) should be done before any public communication about v1.0.7, since integrators who read the release notes need the migration hint.

---

## Items deferred to next sprint

These are Majors from this audit that are structural or require planning rather than a targeted fix:

- **ENG-S2-004** — Path confinement structural enforcement at intake (moving enforcement to the trust boundary). Requires redesigning the intake stage for 3+ agents. See `sprint2-next-sprint-watchlist.md`.
- **TEST-S2-001** — Add thin-wrapper delegation tests for the 14 kernel stage wrapper files. Requires new test infrastructure (`test_stages_spec_kernel.py`, `test_stages_qa_kernel.py`). Good Sprint 3 task.
- **TEST-S2-002** — Decouple revision cycle test key from hardcoded QA `system_msg` string. Low risk today, high friction next time the prompt text is tuned.
- **UX-A01** — Add context envelope to `list_runs` when `project_slug` filter yields no matches. Involves a return-type change that needs cross-surface consistency planning (CLI + MCP).
- **UX-A02** — Add `started_at` to CLI `list-runs` output to match MCP `RunSummary` shape. Requires updating CLI output shape and any tests asserting the current shape.
- **DOC-S2-005** — Update `docs/troubleshooting.md` content for remaining Sprint 2 behaviors (cost warning stderr behavior, path confinement errors). After DOC-S2-003 is done, this is the remaining content gap.

---

## Sign-off gate

The sprint is not done until:

- [ ] All 3 Criticals fixed, tested, and verified by running `./scripts/run-cleanroom.sh` directly
- [ ] ENG-S2-001 fix verified: out-of-project path raises `ValueError` in `_read_voice_samples`
- [ ] ENG-S2-002 fix verified: Gemini cost summary shows consistent model string and cost
- [ ] QA-S2-001 fix verified: cleanroom passes both via `pytest -m cleanroom` AND via direct script invocation
- [ ] Items 4 and 5 (CIO filename fixes) verified: `agentsuite_cio_get_qa_scores` returns actual scores for a completed run
- [ ] Full test suite passes: 1064+ tests, 0 failures
- [ ] Cleanroom GREEN
- [ ] README.md, USER-MANUAL.md, CHANGELOG.md, docs/troubleshooting.md updated
- [ ] Version bump committed if docs-only changes warrant one (otherwise batch into next code commit)

---

*Generated from the `audit-team` skill. Full detail for every ID in the matching role deep-dive (`sprint2-01-engineering-deepdive.md` through `sprint2-05-qa-deepdive.md`).*
