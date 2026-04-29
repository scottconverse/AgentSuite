# AgentSuite v1.0.0 — Executive Audit

**Date:** 2026-04-29
**Tag audited:** `v1.0.0` at commit `9540957`
**Posture:** adversarial (user requested "tear it apart" feedback)
**Roles dispatched:** Principal Engineer, Senior UI/UX Designer, Technical Writer, Test Engineer, QA Engineer (5/5)
**Read this with:** `01-engineering-deepdive.md`, `02-uiux-deepdive.md`, `03-documentation-deepdive.md` (+ supplement), `04-test-deepdive.md`, `05-qa-deepdive.md`

---

## Executive summary

AgentSuite v1.0.0 has the engineering bones of a serious release — typed public surface, pinned schema, golden tests, ADRs, SBOM, no skipped tests, clean compat-freeze contract — and the quality of the kernel code itself is genuinely good. **But the public-facing surfaces shipped at GA do not match what the running code does.** The most-trafficked artifact — the rendered `brand-system.md` screenshot embedded on the GitHub Pages landing — literally displays the text "Mocked content." while presented as real Founder output. The CLI hero screenshot uses flags that don't exist. The README documents MCP tool names that aren't registered. On default Windows the first command (`agentsuite --help`) crashes on a unicode glyph in the help string. The audit team found 5 Blockers, 16 Criticals, 27 Majors across all five roles.

The pattern under almost every Blocker and Critical is the same: **public surfaces were authored against an idealized AgentSuite, not the running code, and the drift was not caught in CI**. The kernel works; the storefront lies. A v1.0.1 hotfix sprint that regenerates the demo from a real run, fixes the Windows crash, repairs the docs/screenshot drift, and adds CI checks that catch this class of regression will close out the GA debt. Every one of those fixes is well under a day of work.

What's working: kernel correctness (atomic state writes, stage-atomic resume, schema versioning all match ADR claims), test discipline (Hard Rule 4a holds, 689 / 0 skipped), the install-block drift check pattern (gold-standard — the audit's own recommendation is "extend it"), the compatibility-freeze framing (right shape, even if the prose has factual bugs), and the deterministic-mock LLM that makes everything reproducible.

---

## Severity roll-up

| Severity | Count |
|---|---|
| Blocker | 5 |
| Critical | 16 |
| Major | 27 |
| Minor | 24 |
| Nit | 10 |
| **Total** | **82** |

After cross-role deduplication (the same root issue surfaced by 2-3 roles independently), the unique-issue count is approximately **62**. The triple-tagged findings — three roles pointing at the same root — are the highest-leverage fixes; they are listed in **Cross-role findings** below.

---

## Top 10 findings (whole audit, priority order)

| # | ID(s) | Severity | Title |
|---|---|---|---|
| 1 | UX-001 + QA-002 + DOC-S01 | **Blocker** | `examples/sample-output/founder/` and the embedded landing-page SVG show "Mocked content." text presented as real Founder output |
| 2 | QA-001 | **Blocker** | `agentsuite --help` crashes with `UnicodeEncodeError` on default Windows cp1252 console (right-arrow + em-dash in `cli.py:18`) |
| 3 | DOC-S02 ≈ UX-003 + UX-004 + QA-004 | **Blocker** | Hero CLI screenshot on landing page uses flags that don't exist (`--user-request`, `--founder-voice-samples`) and ✔ stage-progress messages the CLI no longer emits |
| 4 | ENG-001 | **Critical** | MCP-exposed path traversal: unvalidated `run_id` / `project_slug` reach `mkdir`, `rglob`, `shutil.rmtree` without normalization |
| 5 | ENG-002 | **Critical** | Cost telemetry silently falls back to hardcoded rates on any model id not exact-keying the pricing table; aliased model strings never match. Cost numbers and cap enforcement are unreliable on real runs. |
| 6 | UX-002 + QA-007 + DOC-009 / DOC-S03 | **Critical** | MCP tool name drift: README documents `founder_run`, `trust-risk_run`; registry exposes `agentsuite_founder_run`, `agentsuite_trust_risk_run`. Documented happy path errors |
| 7 | DOC-001 | **Critical** | Compatibility-freeze block locks "six-stage pipeline" but code's `PIPELINE_ORDER` is five stages (approval is a kernel-managed transition, not a pipeline stage). Public contract states the wrong shape on day 1 |
| 8 | DOC-006 | **Critical** | `docs/README-FULL.pdf` is referenced from 4 places; the file lives at repo root, not `docs/`. Every link 404s |
| 9 | TEST-001 | **Critical** | `tests/integration/cassettes/` contains only `.gitkeep` — the vcr scaffold from v0.2 never landed cassettes. Zero real-provider integration coverage in CI; only mocks |
| 10 | TEST-002 | **Critical** | Live tier covers 1 of 7 agents (Founder + Ollama). Six agents have zero real-LLM coverage at any tier |

---

## Cross-role findings (highest leverage)

These surfaced independently in 2-3 role audits. A single coordinated fix closes multiple findings.

### CR-01 — Mocked content shipped as real GA output (Blocker)
**Roles:** UX-001 + QA-002 + DOC-S01
**Root:** The Founder mock LLM produces stub strings ("Mocked content.") for free-text bodies. The v0.9.3 sample-output regenerator captured these stubs into `examples/sample-output/founder/` and the v0.9.3 SVG renderer embedded them in `docs/screenshots/brand-system-rendered.svg` and `qa-report-rendered.svg`. The landing page sells those screenshots as "real run" output and the directory's README says "exactly what a live `agentsuite founder run` produces."
**Fix:** Run a real LLM Founder pass against the patentforgelocal fixture (~$0.30 on Anthropic), commit the output, regenerate the two SVGs from the real markdown. Update `examples/sample-output/founder/README.md` to drop the "exactly what a live run produces" claim or qualify it precisely.
**Blast radius:** the same regenerator captures 29 files; all need the new run. Golden tests for Founder are mock-fixture-based and unaffected. README hero screenshot also needs regeneration alongside.

### CR-02 — Screenshot drift from running CLI (Blocker)
**Roles:** UX-003 + UX-004 + QA-004 + DOC-S02
**Root:** The hero screenshot was authored as a synthetic terminal SVG via `rich.Console.save_svg()` rather than recorded from a real CLI invocation. The composer wrote in flags they expected (`--user-request`, `--founder-voice-samples`) and stage markers (`✔ intake complete` etc.) that the actual `agentsuite founder run` does not produce. Real flags are `--business-goal --project-slug --inputs-dir --run-id --force`.
**Fix:** Record screenshot from a real CLI invocation. asciinema → svg-term, or rerun `rich` with the actual command. Same regeneration pass as CR-01.
**Blast radius:** also affects USER-MANUAL examples and any Discussions seed copy quoting CLI invocations.

### CR-03 — MCP tool name drift (Critical)
**Roles:** UX-002 + QA-007 + DOC-009 + DOC-S03
**Root:** README documents tool names like `founder_run`, `trust-risk_run`. The actual MCP registry exposes `agentsuite_founder_run`, `agentsuite_trust_risk_run` (note `agentsuite_` prefix; underscore in `trust_risk`). Six of seven agents are CLI-only despite README implying full MCP parity.
**Fix:** Either rename registered tools to match docs (breaks compat-freeze on day 1; not viable), or rewrite README + USER-MANUAL + Discussions seed Q&A to match registered names. The doc-rewrites/ directory contains a drafted `README-mcp-section.md` ready to drop in.
**Blast radius:** `docs/community/discussions-seeds.md` Q&A and `launch-posts.md` MCP Discord copy reference these names. Must be updated in the same pass before launch.

### CR-04 — No CI check pins docs/screenshot to running CLI (Major, but root cause for CR-02 and CR-03)
**Roles:** TEST-004
**Root:** No test asserts that documented CLI invocations or MCP tool names match the registered Typer commands / registry. The install-block drift check pattern (`tests/fixtures/install-block.md` + the regex check in `release.yml`) exists for one specific README block — but was never extended to other prose-vs-code surfaces.
**Fix:** Add `tests/test_readme_cli_invocations.py` that parses fenced bash blocks from README/USER-MANUAL, extracts `agentsuite ... run` lines, and validates flag names against the Typer command schema. Add `tests/test_mcp_tool_names_documented.py` that diffs registered tool names against names mentioned in README/USER-MANUAL.
**Blast radius:** no code change; pure test addition. Will retroactively flag every existing drift, which is the point.

---

## What's working well (specific, not filler)

- **Kernel correctness.** ENG audit verified: atomic state writes via temp-file rename, stage-atomic resume, `schema_version: 2` enforcement with a clear remediation message, cost-tracker boundary semantics (caps exclusive, not inclusive). All ADR claims hold against the code.
- **Test discipline is real, not performative.** Hard Rule 4a is satisfied (zero `pytest.skip()`, zero unconditional `@pytest.mark.skip`). The conditional `skipif` in `test_founder_pipeline.py` is documented in `docs/test-coverage.md` with rationale. 689 tests, 0 skipped, 3 deselected by marker.
- **The install-block drift check is gold-standard.** The pattern that catches README install-block drift via `tests/fixtures/install-block.md` is exactly what should exist for every prose-vs-code surface. The audit's own recommendation is "extend this pattern" not "invent something new."
- **Schema-version coverage pins the v1.0 compat freeze.** `tests/unit/kernel/test_run_state_schema_version.py` will refuse to load a `_state.json` without `schema_version: 2`, with a clear error message. Future migration work has a documented entry point (ADR-0007).
- **Golden helpers type-enforce the text-vs-numeric tolerance split.** `assert_qa_within_tolerance` rejects non-numeric input by signature; future contributors physically cannot loosen text comparisons by accident.
- **Resume idempotency uses a billable mock.** The integration test for ADR-0007 exercises real cost-carry-forward semantics via the deterministic mock, not by faking the cost ledger.
- **Lighthouse 96/100/100/100.** Performance / Accessibility / Best Practices / SEO. The single accessibility issue caught in the audit (link-color-only) was already fixed during the rc1 → GA bake.
- **ADRs match the code.** ADRs 0002/0004/0006/0007 verified against current implementation. ADR-0001 was refreshed during v0.9.2 to match `2b1dda0`.

---

## This-sprint punch list

See [`sprint-punchlist.md`](sprint-punchlist.md) for the actionable list. **5 Blockers + 9 Critical fixes** belong in v1.0.1. Most are sub-day fixes; the heaviest is CR-01 (regenerate sample-output) which is ~1 hour and a $0.30 LLM bill.

---

## Next-sprint watchlist

See [`next-sprint-watchlist.md`](next-sprint-watchlist.md) for forward-looking items. Headline items: cassette discipline (TEST-001), live-tier expansion to all 7 agents (TEST-002), MockLLMProvider keyword-matcher hardening (TEST-003), Ollama HEAD-vs-GET probe fix (ENG-004), CLI progress indication design (UX-006 / QA-005).

---

## Drafted replacements

The Technical Writer role produced these in `doc-rewrites/`:

- `SECURITY.md` — addresses the missing security policy (DOC-S04). New file; drop into repo root.
- `README-mcp-section.md` — replaces README MCP examples with registered tool names. Addresses CR-03.
- `index.html-sample-section.html` — replaces the landing-page Sample-run section. Addresses CR-01.
- `verify-release-link-check.sh` — snippet for `scripts/verify-release.sh` to catch broken links like DOC-006 in pre-push.
- `compatibility-freeze.md` — corrected stage-count narrative for ADR-0001-style framing. Addresses DOC-001.

These are drafts. Review before merging.

---

## Tensions between roles (honest disclosure)

Per the orchestration guide: when roles disagree, the audit states the tension rather than papering over it.

- **Engineering says: kernel is solid; the cost-telemetry fallback (ENG-002) is a Critical data-provenance bug but not a Blocker.** **QA says: the user-facing impact is silent — operators read a number that's wrong but consistent-looking.** Resolution: the audit treats it as Critical (not Blocker) because the cap is enforced on the same wrong number — i.e. the cap *does* fire even if the number is mis-priced; data integrity is broken but data loss is not. Engineering wins on severity; QA's user-facing concern is correct and lands in the v1.0.1 punch list.
- **Test Engineering says: the suite is genuinely strong by community-Python standards.** **QA says: the suite missed the ENTIRE class of doc/code drift bugs.** Both are true. The suite is excellent at what it tests; what it tests does not include the prose-vs-code drift surface, which is exactly the gap CR-04 fills.
- **UX role flagged Major-severity silent CLI (UX-006) as worth Critical given user impact.** **QA role rated the same finding Critical (QA-005).** Both reasoned independently; same conclusion. The synthesis takes Critical.

---

## Verdict

**v1.0.0 GA shipped with Blockers.** Recommend a v1.0.1 hotfix release within one sprint that closes Blockers + the 4 cross-role Critical findings. The kernel is solid; the storefront needs work. The drift-detection gap (CR-04) is the highest-leverage single fix in the audit — close it and the class of "v1.0 storefront says X, code says Y" doesn't recur.

Continue to v1.1 only after v1.0.1 ships clean. The launch posts in `docs/community/launch-posts.md` should not be posted until v1.0.1 — the screenshots and tool names they reference are wrong as of v1.0.0.

The audit findings are evidence-grounded. Every Blocker and Critical has a file path and a runnable verification step in the deep-dive. Pick up any item and start working.
