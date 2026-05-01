# Documentation Deep-Dive — AgentSuite v1.0.1 (closure pass)

**Audit date:** 2026-04-29
**Role:** Technical Writer
**Scope audited:** Closure verification of v1.0.0 documentation findings (DOC-S01, DOC-S02, DOC-001, DOC-006, DOC-009/S03, CR-03, DOC-S04, QA-009) against HEAD `de2a7a3`. CHANGELOG quality check. PDF cross-reference scan. 6-doc-artifact gate. v1.0.2 doc backlog.
**Writer mode:** audit-only
**Auditor posture:** Balanced
**HEAD:** `de2a7a3` — `chore: release v1.0.1 — sprint 1 audit-fix release`

---

## TL;DR

v1.0.1 closes the majority of v1.0.0 documentation findings cleanly: the PDF
moved into `docs/`, all four references resolve, MCP tool names are uniformly
`agentsuite_<agent>_<verb>`, `SECURITY.md` is in place with a real disclosure
policy, and the stale `agentsuite founder resume` example is gone from
`USER-MANUAL.md`. The CHANGELOG v1.0.1 entry is honest about scope and credits
the right finding IDs.

**However, DOC-001 is only half-closed.** The fix updated the v1.0.0rc1
"Compatibility" block to "five stages plus a kernel-managed approval
transition" but left the v1.0.0 entry's "Compatibility (carried forward from
1.0.0rc1)" block at `CHANGELOG.md:123` saying "**six stages
(intake → extract → spec → execute → qa → approval)**" — directly contradicting
the rc1 block 24 lines below. The compat-freeze is now self-inconsistent within
the same file. This is a Critical accuracy regression carried over from v1.0.0.

DOC-007 (two USER-MANUAL.md files) was not in v1.0.1's stated scope and remains
open: `docs/USER-MANUAL.md` is a 652-line stale duplicate of the 984-line root
`USER-MANUAL.md`.

## Severity roll-up (closure pass)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 1 |
| Minor | 1 |
| Nit | 0 |

---

## Per-ID closure verdict

| ID | Verdict | Evidence |
|---|---|---|
| DOC-S01 (UX overlap) | Closed | CHANGELOG entry, UX deep-dive accepts |
| DOC-S02 (UX overlap, stale CLI screenshot) | Closed | CR-02 ffd134f re-recorded `cli-founder-run.svg`; drift trap `test_readme_cli_invocations.py` now passes |
| **DOC-001 (5-vs-6 stage count)** | **Partially closed** | v1.0.0rc1 block fixed (`CHANGELOG.md:147`); v1.0.0 carry-forward block at `CHANGELOG.md:123` still says "six stages" — contradicts rc1 |
| DOC-006 (PDF 404) | Closed | `docs/README-FULL.pdf` exists (33 KB, Apr 27); the 4 references at `README.md:259`, `README.md:278`, `docs/index.html:127`, `docs/USER-MANUAL.md:652` all point at `docs/README-FULL.pdf` and resolve. CONTRIBUTING.md does not reference it (false positive in original audit). |
| DOC-009 / DOC-S03 / CR-03 (MCP tool names) | Closed | `README.md:96` lists 8 tools, all `agentsuite_<agent>_<verb>` form. Hyphenated `trust-risk` only appears as a Typer CLI subcommand name (correct per `base_agent.py:49` `cli_name`). New drift trap `tests/test_mcp_tool_names_documented.py` enforces this byte-for-byte. |
| DOC-S04 (no SECURITY.md) | Closed | `SECURITY.md` at repo root, 52 lines, includes disclosure channel (GitHub Security Advisories), 5/10-day SLA, in/out scope, supply-chain hygiene reference to pip-audit + CycloneDX SBOM. Reasonable. |
| QA-009 (`agentsuite founder resume` callable) | Closed | No remaining references in `USER-MANUAL.md`, `README.md`, or `CHANGELOG` outside the v1.0.1 fix-line itself. The CLI subcommand is queued for v1.0.x per CHANGELOG line 85. |

---

## Findings (new / regressions)

### [DOC-101] — Critical — Accuracy — CHANGELOG v1.0.0 Compatibility block contradicts rc1 block on stage count

**Evidence**
- `CHANGELOG.md:123` (v1.0.0 entry, "Compatibility (carried forward from 1.0.0rc1)"):
  > **Kernel pipeline:** six stages (`intake → extract → spec → execute → qa → approval`).
- `CHANGELOG.md:147` (v1.0.0rc1 entry, "Compatibility"):
  > **Kernel pipeline:** five stages (`intake -> extract -> spec -> execute -> qa`) plus a kernel-managed approval transition.

The v1.0.1 fix-commit `b6c80bb` corrected the rc1 block but left the v1.0.0
GA entry's carry-forward block untouched. The two compat-freeze blocks now
disagree about the public contract within the same file, 24 lines apart.

**Why this matters**
DOC-001's load-bearing claim was "the public-contract compat-freeze states the
wrong pipeline shape on day 1." That claim is still true at the v1.0.0 GA tag,
which is the tag end-users will see on PyPI / GitHub releases as the freeze
event. A reader checking the GA-tag's compat block reads "six stages
(... → approval)" and writes a downstream MCP client expecting an `approval`
stage handler — and finds `BaseAgent._drive()` doesn't call one. This is the
exact failure mode the original DOC-001 described.

**Blast radius**
- Adjacent docs: none — all other "five stages" copy in `README.md:51`, `README.md:211`, `USER-MANUAL.md:203`, `USER-MANUAL.md:223`, `USER-MANUAL.md:941`, `docs/architecture/system-overview.mmd:5`, `scripts/generate_readme_pdf.py:1093` is now consistent.
- Migration: none.
- Tests: `tests/test_readme_cli_invocations.py` and `tests/test_mcp_tool_names_documented.py` are CLI/tool-name drift traps and would not catch a stage-count drift in CHANGELOG. A small grep-style trap (`assert "six stages" not in changelog_text`) would close this class.
- Related: DOC-001 (now partially closed; this is the residual half).

**Fix path**
One-line edit at `CHANGELOG.md:123`:
```
- **Kernel pipeline:** five stages (`intake -> extract -> spec -> execute -> qa`) plus a kernel-managed approval transition.
```
Worth a follow-up commit to v1.0.x or as v1.0.2's first item.

---

### [DOC-102] — Major — Hygiene — `docs/USER-MANUAL.md` is a stale 652-line duplicate of root USER-MANUAL.md (DOC-007 carryover)

**Evidence**
- `USER-MANUAL.md` at repo root: 984 lines, last modified during v1.0.1, covers all 7 agents.
- `docs/USER-MANUAL.md`: 652 lines, last touched 2026-04-29 17:19 (touched by build but content stale), references PDF at correct path but is otherwise an older version.

This was DOC-007 in the v1.0.0 audit and was not in v1.0.1's stated scope. It is
not a regression — it predates v1.0.1.

**Why this matters**
A reader who finds `docs/USER-MANUAL.md` (e.g., via the `docs/` directory
listing, or a dev who greps `docs/`) reads a less-complete version of the
manual. The `scripts/build-pdf.sh` pipeline reads from `docs/README-FULL.pdf`
sources, so the discrepancy is unlikely to ship into the PDF, but the file's
on-disk presence is a trust hazard.

**Fix path**
Delete `docs/USER-MANUAL.md` and add a `docs/README.md` redirect, or sync the
two by making `docs/USER-MANUAL.md` a symlink (Linux/Mac) or by deleting it
outright. Recommend deletion + grep trap.

---

### [DOC-103] — Minor — Hygiene — Drift traps don't cover CHANGELOG stage-count language

**Evidence**
The new drift traps (`tests/test_readme_cli_invocations.py`,
`tests/test_mcp_tool_names_documented.py`) are excellent for CLI invocations
and MCP tool names. They do not parse CHANGELOG prose for stage-count claims.
DOC-101 above slipped past them for that reason.

**Fix path**
A 5-line pytest in `tests/test_changelog_pipeline_consistency.py`:
```python
def test_changelog_does_not_claim_six_stages():
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert "six stages" not in text.lower(), "DOC-001/101 regression"
```
Trivial; prevents the entire class.

---

## CHANGELOG quality check

The v1.0.1 entry (lines 12–103) is well-structured:

- **Honest about scope.** Lead paragraph states "5 of 5 Blockers, 9 of 16 Criticals, 6 of 27 Majors" closed (line 99–100). Remaining items are explicitly deferred to `next-sprint-watchlist.md` (W-01..W-14). Doesn't overclaim.
- **Credits finding IDs.** Every Added/Fixed bullet ties back to a specific finding ID (CR-01..CR-04, ENG-001..005, UX-006, QA-001/005/009, DOC-001/006/S04, TEST-003/006). A reader can correlate the dev-reports audit to the line-item fix.
- **Doesn't credit specific commit hashes.** The Audit follow-up section names the audit folder but not the three closure commits (`b6c80bb`, `08a134d`, `de2a7a3`). This is fine — Keep a Changelog format doesn't require it — but if Scott wants commit-level traceability, those three hashes could be appended.
- **Structurally honest about CR-01.** Lines 69–74 explicitly call CR-01 "the structural half (regenerating bodies from a real LLM run) is queued for v1.0.2." That matches the Unreleased Roadmap entry on line 9.
- **One inconsistency** — the v1.0.0 carry-forward compat-freeze block (DOC-101 above) wasn't updated by the same hand that updated the rc1 block. Surgical fix.

Verdict: CHANGELOG quality is high; one residual line.

---

## 6 doc artifacts (Hard Rule 9)

| Artifact | Present | Status |
|---|---|---|
| `README.md` | Yes | Current, v1.0.1 surface |
| `CHANGELOG.md` | Yes | v1.0.1 entry present; one line residual (DOC-101) |
| `CONTRIBUTING.md` | Yes | Did not reference PDF; no changes needed |
| `LICENSE` | Yes | Present |
| `.gitignore` | Yes | Present |
| `docs/index.html` | Yes | PDF link points at `docs/README-FULL.pdf` (line 127) |

Plus: `SECURITY.md` (DOC-S04 closure), `USER-MANUAL.md`, `docs/README-FULL.pdf`. Gate clears.

---

## Doc cross-reference scan

| Reference | Resolves? |
|---|---|
| `README.md:259` → `docs/README-FULL.pdf` | Yes |
| `README.md:278` → `docs/README-FULL.pdf` | Yes |
| `docs/USER-MANUAL.md:652` → `docs/README-FULL.pdf` | Yes |
| `docs/index.html:127` → `docs/README-FULL.pdf` (via GitHub blob URL) | Yes |
| `USER-MANUAL.md:979` → `docs/README-FULL.pdf` | Yes |
| `CHANGELOG.md:501` → `README-FULL.pdf` (no path; v0.x history line, doesn't 404 since it's prose) | OK |

Note: `scripts/generate_readme_pdf.py:48` still writes to `REPO_ROOT / "README-FULL.pdf"` (root, not `docs/`). The `scripts/build-pdf.sh` script writes to `docs/README-FULL.pdf` (line 35). The two PDF-build scripts disagree about the output path. Not a doc-reference break (the `docs/`-located file is the one referenced) but a hygiene smell — if a contributor runs `generate_readme_pdf.py`, they'll regenerate the PDF in the wrong place and the repo will have two copies. Worth noting for v1.0.2 cleanup.

---

## v1.0.2 documentation backlog

Already on roadmap (CHANGELOG line 9):
- **CR-01 structural** — regen `examples/sample-output/founder/` bodies from a real Anthropic run (~$0.30). The README honesty pass shipped in v1.0.1; the regenerated artifacts are the structural close.

New from this closure pass (carry into v1.0.2):
- **DOC-101** — fix `CHANGELOG.md:123` six-stages line (1-line edit).
- **DOC-102** — delete or sync `docs/USER-MANUAL.md` duplicate (DOC-007 carryover).
- **DOC-103** — add CHANGELOG stage-count drift trap (~5 lines pytest).
- **PDF build-script discrepancy** — reconcile `scripts/generate_readme_pdf.py` (writes to root) and `scripts/build-pdf.sh` (writes to `docs/`). Pick one.

From `next-sprint-watchlist.md`: W-01 cassette tier and W-02 live-tier expansion are also tagged for v1.0.2 / v1.1.x.

---

## Appendix: docs reviewed in this pass

- `CHANGELOG.md` (full)
- `README.md` (selected ranges and full grep)
- `USER-MANUAL.md` (full grep)
- `docs/USER-MANUAL.md` (compared to root)
- `docs/index.html` (selected ranges)
- `docs/README-FULL.pdf` (existence + size only; not rendered)
- `SECURITY.md` (full)
- `CONTRIBUTING.md` (selected ranges)
- `docs/community/good-first-issues.md` (selected ranges)
- `docs/community/discussions-seeds.md` (existence only)
- `scripts/generate_readme_pdf.py` (selected ranges)
- `scripts/build-pdf.sh` (selected ranges)

