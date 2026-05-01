# AgentSuite v1.0.1 — Closure Audit Executive Report

**Date:** 2026-04-29
**Tag candidate:** v1.0.1 at HEAD `de2a7a3` (10 commits ahead of `v1.0.0`)
**Posture:** balanced (sanity check, not adversarial)
**Verdict:** **3 NEW Criticals + 2 NEW Majors. Fix before push.**

---

## Did the v1.0.1 sprint deliver?

**Yes, with caveats.** Every claimed audit-ID closure is genuine: ENG-001/002/003/004/005, UX-002/003/004/006, DOC-001/006/009/S04, TEST-003/004/006, QA-002/004/005/007, plus the prose-half of QA-009. Five of five v1.0.0 Blockers and nine of nine claimed Criticals close cleanly when verified against shipped code, runtime behavior, and the CR-04 drift-trap (5/5 green).

**But three new Criticals surfaced** during the closure audit, all in surfaces the v1.0.1 sprint *touched* but didn't fully clean up:

1. **DOC-101 (Critical):** CHANGELOG self-contradicts on pipeline-stage count. The DOC-001 fix landed the corrected language at CHANGELOG.md:147 (rc1 block) but the v1.0.0 GA "Compatibility (carried forward)" block at CHANGELOG.md:123 still says "six stages." The public contract document contradicts itself 24 lines apart in the same file.
2. **UX-101 (Critical):** The CR-01 disclaim landed on the docs/index.html "Spec artifacts" panel but README.md:217 and docs/index.html:73 still describe the screenshots as "every artifact a real Founder run produces" / "the full output of a real run." The honesty-pass is half-applied.
3. **QA-101 (Critical, NEW class):** `agentsuite-mcp --help` exits 0 with empty stdout — silent failure on the first command every Codex / Claude Code integrator types. Worse than the original cp1252 crash because the user has no signal anything's wrong.

Plus two Majors worth folding into the same fix-pass (TEST-101 environmental test fragility, TEST-102 CHANGELOG test-count drift).

## Severity roll-up (NEW findings only — closures excluded)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 3 |
| Major | 5 |
| Minor | 6 |
| Nit | 3 |
| **Total NEW** | **17** |

## Top findings

| # | ID | Severity | Title | Owner |
|---|---|---|---|---|
| 1 | DOC-101 | Critical | CHANGELOG v1.0.0 GA block still claims 6 stages (one-line fix, blocks tag) | Tech Writer |
| 2 | UX-101 | Critical | "real run" rhetoric persists at README:217 + index.html:73 | UX |
| 3 | QA-101 | Critical | `agentsuite-mcp --help` silently exits 0 with empty stdout | Engineering |
| 4 | TEST-101 | Major | `test_downstream_consumer.py` fails locally when ollama extra absent | Test Engineer |
| 5 | TEST-102 | Major | CHANGELOG claims 689→777 but actual is 781 passed | Tech Writer |
| 6 | UX-102 | Major | docs/index.html still has v0.8 Roadmap card on a v1.0.1 page | UX |
| 7 | UX-103 | Major | Stage progress fires after-completion only; live runs still go silent during a stage | UX/Eng (defer) |
| 8 | DOC-102 | Major | Two USER-MANUAL.md files (root vs docs/) — duplicate drift risk | Tech Writer (defer) |
| 9 | TEST-103 | Minor | No public-API surface-freeze test backs the v1.0 compat-freeze claim | Test Engineer (defer) |
| 10 | UX-106 | Minor | CLI summary JSON missing fields shown in stderr (cost_usd, qa_passed) | UX (defer) |

## What's working (specific)

- **Per-ID closure quality is high.** When v1.0.1 claims to close an audit ID, the fix is real, evidence-grounded, and tests pin the regression case. Engineering's defense-in-depth (validator + path-resolution containment check on `ArtifactWriter`) is praised independently.
- **CR-04 drift trap delivers as designed.** Both files (CLI and MCP) catch the originally-flagged class of bug; quality of the regex extractors holds up under stress-test (false-positive risk structurally avoided via `_extract_subcommand_path` returning `[]` for prose mentions).
- **Compat-freeze surface is intact.** No public API change, no `_state.json` schema bump, no MCP tool name change, no pipeline stage rename. Patch-release discipline holds.
- **CHANGELOG transparency.** Honestly cites every closed finding ID, distinguishes "closed" from "deferred to v1.0.2" (CR-01 structural piece), credits each commit hash. Future readers can audit-from-prose.

## v1.0.1-blocker fix list (must close before push)

The 3 Criticals are all single-touch fixes:

1. DOC-101 — One CHANGELOG.md line edit (~5 min).
2. UX-101 — Two text edits (README.md:217 + docs/index.html:73) (~5 min).
3. QA-101 — Add `--help` handling to `agentsuite/mcp_server.py::main` so it exits with the FastMCP help text instead of trying to start the server (~10 min).

Plus the 2 cheap Majors:

4. TEST-101 — Make `test_downstream_consumer.py` skip the `ollama.py` import path via mypy ignore-missing-imports for that one module, OR add `[ollama]` to dev install instructions (~10 min).
5. TEST-102 — Update CHANGELOG v1.0.1 entry to reflect actual count (781 passed, includes 1 pre-existing skipif and the +88 net new) (~2 min).

Total: ~30 min of work + verify-release re-run, then push the v1.0.1 stack with these fixes folded into a final commit.

## v1.0.2 backlog (deferred from this closure audit)

- UX-103 mid-stage silence (real Anthropic 30-90s gaps between `[OK]` lines)
- UX-102 v0.8 Roadmap card cleanup
- DOC-102 USER-MANUAL deduplication
- DOC-103 add CHANGELOG-prose drift trap (would have caught DOC-101)
- TEST-103 public-API surface-freeze test
- TEST-104 SVG extractor robustness against renderer changes
- UX-105 sample-output README leaks audit-internal vocabulary
- UX-106 CLI summary JSON field asymmetry
- QA-102 trust_risk + cio MCP tool surface diverge from other 5 agents
- The two `scripts/generate_readme_pdf.py` vs `scripts/build-pdf.sh` write-path disagreement

All folded into `next-sprint-watchlist.md` for v1.0.2 sprint planning.

## Honest disclosure

This closure audit found *more* in the v1.0.1 candidate than the v1.0.0 audit found in v1.0.0 by per-finding severity (3 Critical NEW vs 5 Blocker + 16 Critical original). That's a feature, not a bug:
- The v1.0.0 audit's Top-Level Crit count was inflated by cross-role triple-counts of the same root issue (mocked-content-as-real had 3 IDs).
- The v1.0.1 closure audit caught the *partial* fixes — the rhetoric that wasn't updated alongside the disclaim, the second CHANGELOG anchor that wasn't fixed alongside the first, the `agentsuite-mcp` binary that didn't get the same `--help` treatment as `agentsuite`.
- Closure audits are denser-per-finding than initial audits because they look for "did the surgery extend everywhere it should?" rather than "is anything wrong?". Both numbers are honest about their populations.

The v1.0.1 stack is good. It's not yet ship-ready.
