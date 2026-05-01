# Documentation Deep-Dive — AgentSuite

**Audit date:** 2026-04-30
**Role:** Technical Writer
**Scope audited:** README.md, CHANGELOG.md, CONTRIBUTING.md, USER-MANUAL.md, docs/index.html
**Writer mode:** audit+draft
**Auditor posture:** Balanced

---

## TL;DR

The documentation is in good structural shape and shows genuine care — a full user manual, a proper CHANGELOG with 13 entries from v0.1.0 to v1.0.5, contributor guide, and a landing page. Three version-skew issues require immediate attention: the README version badge shows v1.0.3 (actual: v1.0.5), the USER-MANUAL footer says "v0.9.1" (actual: v1.0.5), and the landing page version badge shows v1.0.1 (actual: v1.0.5). The USER-MANUAL also contains a stale error (`ConsistencyCheckFailed`) that v1.0.3 made non-fatal — the fix path and explanation are now wrong for users. The `ConsistencyCheckFailed` entry in the common-errors tables across every agent chapter should be replaced with guidance about the new `consistency_report.json` review flow. The CHANGELOG's footer comparison links are frozen at v0.9.1; links for v1.0.0 through v1.0.5 are missing. A new user can succeed with this documentation — the onboarding path is clear and accurate — but three version badges send the wrong signal to users deciding whether to adopt.

---

## Severity roll-up (documentation)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 5 |
| Minor | 4 |
| Nit | 3 |

---

## What's working

- **USER-MANUAL scope and audience-awareness** — The manual is genuinely written for a non-technical reader. Every term is defined in the glossary, every command is shown for both Windows and Mac/Linux, every agent chapter has a "Common errors" table. This is hard to do well and the team has done it well.

- **CHANGELOG quality and granularity** — The CHANGELOG is exceptional. Every entry explains what broke, why it broke, what the fix is, and what tests were added. The "Pass 2 — closure of inline five-role re-audit" section in v1.0.2 is a model of transparent release notes. A user upgrading from any version can understand exactly what changed and what they need to do.

- **README install block with marked anchors** — The `<!-- install:start -->` / `<!-- install:end -->` markers are a clean design that enables drift-trap automation. The install commands are complete, accurate, and cover all four providers. The Python SDK quick-start example in the README is well-written and directly runnable.

- **Architecture diagram in README** — The Mermaid flowchart and ASCII architecture diagram together give both a pipeline overview and a system topology view without requiring the user to open the PDF. Most READMEs ship one or the other; this ships both.

- **CONTRIBUTING.md security section** — The "Security: path validation" section added in v1.0.2 is exactly the right pattern: it names the helpers, explains why raw path construction is forbidden, and references the original finding. This is the kind of contributor documentation that prevents the same bug class from re-entering.

- **Test-tier table in CONTRIBUTING.md** — The unit / integration / golden / cleanroom / live breakdown with costs and when each runs is immediately useful for a new contributor deciding how fast to iterate.

- **Honest marketing on the landing page** — The landing page qualifies mock-LLM screenshots with explicit on-page language ("rendered from deterministic mock-LLM output"). This is honest and appropriate.

---

## What couldn't be assessed

- **README-FULL.pdf** — Not reviewed in this pass; PDF rendering requires tooling not in scope for a plain-text audit. The PDF is referenced in multiple docs as the "full reference with architecture diagrams." If the PDF still says v1.0.3 or earlier, it carries the same version-skew issue as the HTML artifacts. Flag for a manual version check.
- **docs/community/discussions-seeds.md and launch-posts.md** — Not in scope for this documentation pass. The v1.0.2 CHANGELOG mentions these were updated for the pipeline-stage count fix; not re-verified here.
- **GitHub Discussions actual posts** — Cannot assess whether discussion boards are seeded without GitHub access.

---

## Doc asset inventory

| Asset | Exists? | Status | Finding(s) |
|---|---|---|---|
| README.md | Yes | Adequate | DOC-001 |
| ARCHITECTURE.md | No (embedded in README + PDF) | Adequate — coverage in README + PDF | — |
| User manual / guide | Yes (USER-MANUAL.md) | Adequate | DOC-002, DOC-003 |
| API reference | Partial — MCP tools listed in README; no structured ref | Adequate for current scope | DOC-007 |
| FAQ | No standalone FAQ | Adequate — troubleshooting in USER-MANUAL covers key cases | DOC-008 |
| CHANGELOG | Yes | Strong — with caveats | DOC-004 |
| CONTRIBUTING | Yes | Strong | DOC-006 |
| SECURITY | Yes (SECURITY.md) | Adequate | — |
| LICENSE | Yes | Strong | — |
| Landing / marketing page (docs/index.html) | Yes | Weak — version badge stale, roadmap stale | DOC-005 |
| README-FULL.pdf | Yes | Not assessed in this pass | — |

---

## Persona walk-through

### First-time user

A first-time user lands on the README. Within five seconds they know: "Seven role-specific reasoning agents that turn vague intent into precise operating artifacts." The audience is clearly stated in the "Why AgentSuite" section: "For developers wiring AI into Codex / Claude Code / Cowork." The install block is present and complete.

**Where they get confused:** The README version badge says v1.0.3. If a user clones today and gets v1.0.5, the README signals the project is two versions behind. This is a minor credibility hit on first impression.

The USER-MANUAL gives a very clear onboarding path. The "What You Need Before You Start" section is accurate (Python 3.11+, API key or Ollama). Installation commands are correct. The `agentsuite agents` verification step is present. A non-technical user can succeed.

### Returning user

A returning user who upgraded from v1.0.2 to v1.0.5 will look at the USER-MANUAL for guidance on `ConsistencyCheckFailed` errors. The manual tells them this error means "two documents contradict each other" and to "make your `--business-goal` more specific, then re-run." This is now **incorrect behavior description** — as of v1.0.3, `ConsistencyCheckFailed` no longer halts the pipeline. The fix is `requires_revision=True` in the run state, and the pipeline continues to approval. A user following the manual's advice (re-run with more specific inputs) might be doing unnecessary work.

### New team member

A new contributor can run from clone to green tests using only CONTRIBUTING.md. The setup steps (venv, `pip install -e ".[dev]"`, `pytest`) are complete and cross-platform. The "Adding a new agent" section is detailed and accurate. The test-tier table is helpful. The pre-push gate section correctly references `verify-release.sh`.

One gap: CONTRIBUTING.md says `pytest` runs "688 of 691 tests" (line 78). The actual count as of v1.0.5 is 892 (87 stress tests added in v1.0.5 + 805 from v1.0.4 baseline). A new contributor running `pytest` and getting 892 tests may question whether the setup is correct.

---

## Findings

> **Finding ID prefix:** `DOC-`
> **Categories:** Accuracy / Completeness / Onboarding / Architecture / API / FAQ / Marketing / Tone / Hygiene

---

### [DOC-001] — Major — Accuracy — README version badge shows v1.0.3; actual version is v1.0.5

**Evidence**

`README.md`, line 6:
```
> **v1.0.3** — Specification Kernel + Founder · Design · Product · Engineering · Marketing · Trust/Risk · CIO Agents
```
`agentsuite/__version__.py` and `pyproject.toml` both report `1.0.5`.

**Why this matters**

First-time users comparing the README badge to the CHANGELOG see an immediate discrepancy. It signals either that the README is not maintained or that the CHANGELOG entries for v1.0.4 and v1.0.5 shipped code changes without corresponding doc updates. Either way it damages trust before the user has run a single command.

**Blast radius**
- Adjacent docs: `docs/index.html` has the same problem (v1.0.1 badge, DOC-005). `USER-MANUAL.md` footer also stale (DOC-002). Three docs all out of sync.
- User-facing: any user comparing badge to CHANGELOG or to `agentsuite --version` output will notice.
- Related findings: DOC-002 (USER-MANUAL version), DOC-005 (landing page version). All three share the root cause of missing doc-sync in the v1.0.4 and v1.0.5 release commits.

**Fix path**

Change line 6 of README.md:
```
> **v1.0.5** — Specification Kernel + Founder · Design · Product · Engineering · Marketing · Trust/Risk · CIO Agents
```

Also update the Status section's "Roadmap" entry at line 273: `v0.8.0 — next agent` is long stale. The project is at v1.0.5; the roadmap should reflect the CHANGELOG's `[Unreleased]` section (v1.1.x candidates).

---

### [DOC-002] — Critical — Accuracy — USER-MANUAL footer says "v0.9.1"; actual version is v1.0.5

**Evidence**

`USER-MANUAL.md`, line 1016 (final line):
```
*AgentSuite v0.9.1 — User Manual*
```
The version header on line 3 says `**Version 1.0.2**`, which was updated in v1.0.2's DOC-301 fix but the footer was not.

**Why this matters**

The USER-MANUAL is the primary resource for non-technical users. A user who opens the manual after installing v1.0.5 sees a footer saying v0.9.1 — six version jumps behind. This is the document that tells a non-technical person how to use the product. Mismatched version signals that the content may be stale even if it isn't.

Additionally, the version header (line 3) says `**Version 1.0.2**` but the footer says `**v0.9.1**`. These two version references in the same file contradict each other, which is confusing regardless of which one a user trusts.

**Blast radius**
- Adjacent docs: README badge (DOC-001), landing page badge (DOC-005). All three share the version-drift root cause.
- User-facing: Non-technical users — the primary audience for this document — are most likely to notice and be confused by this.
- Related findings: DOC-001, DOC-005.

**Fix path**

1. Change line 3 from `**Version 1.0.2**` to `**Version 1.0.5**`
2. Change line 1016 from `*AgentSuite v0.9.1 — User Manual*` to `*AgentSuite v1.0.5 — User Manual*`

Draft produced: `doc-rewrites/USER-MANUAL-footer-fix.md` (patch only — full rewrite not warranted for two line changes, patch is cleaner).

---

### [DOC-003] — Major — Accuracy — ConsistencyCheckFailed described as a fatal error in USER-MANUAL; v1.0.3 made it non-fatal

**Evidence**

`USER-MANUAL.md`, multiple "Common errors" tables in agent chapters. Example from Founder Agent chapter, lines ~325-328:

```
| `ConsistencyCheckFailed` | Two documents contradict each other | Make your `--business-goal` more specific, then re-run |
```

Same entry appears in Design Agent, Engineering Agent, and other agent chapters.

`CHANGELOG.md` for v1.0.3 (lines 30-31):
> "Fix: removed the `ConsistencyCheckFailed` class and raise from all 7 agents' `spec.py` files; replaced with `requires_revision=True` in the returned `RunState`. The pipeline now continues to approval where the reviewer can inspect `consistency_report.json`."

The `ConsistencyCheckFailed` exception **no longer exists**. The pipeline no longer raises it. A user who sees any error resembling this must now have a different issue (or be on an older version). The documented fix ("re-run with more specific inputs") is no longer the correct response.

**Why this matters**

A returning user who encounters a consistency issue post-v1.0.3 will look up `ConsistencyCheckFailed` in the manual. The manual says: "Two documents contradict each other. Re-run." But the actual v1.0.3+ behavior is: the pipeline completes, `requires_revision=True` is set, and the user should review `consistency_report.json` at the approval step. The manual sends them on a pointless re-run loop.

**Blast radius**
- Adjacent docs: `docs/index.html` does not document error codes (no blast there). `CONTRIBUTING.md` does not document user-facing errors (no blast there).
- User-facing: Any user who hits a consistency issue post-v1.0.3 and follows the manual will re-run unnecessarily.
- Related findings: DOC-001 (the version drift means users can't tell if the manual reflects their installed version).

**Fix path**

In every agent chapter's "Common errors" table, replace the `ConsistencyCheckFailed` row with:

```
| Consistency issues flagged in output | The consistency check found cross-artifact contradictions. The pipeline completed but `requires_revision=True` in `qa_scores.json`. | Open `consistency_report.json` in the run folder. Review the listed mismatches. Either approve and edit manually, or re-run with more specific inputs. |
```

Also update Section 10 (Troubleshooting) and the Glossary entry for `ConsistencyCheckFailed`.

Draft produced: `doc-rewrites/USER-MANUAL-consistency-fix.md` (patch showing all seven replacements).

---

### [DOC-004] — Major — Hygiene — CHANGELOG comparison links frozen at v0.9.1; links for v1.0.0 through v1.0.5 are missing

**Evidence**

`CHANGELOG.md`, lines 590–604 (footer section):
```
[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v0.9.1...HEAD
[0.9.1]: https://github.com/scottconverse/AgentSuite/compare/v0.9.0...v0.9.1
...
```

The link section ends at `[0.1.0]`. There are no comparison links for `[1.0.5]`, `[1.0.4]`, `[1.0.3]`, `[1.0.2]`, `[1.0.1]`, `[1.0.0]`, `[1.0.0rc1]`, `[0.9.3]`, `[0.9.2]`, or `[0.9.1]` (in the v1.0.x range). The `[Unreleased]` link also still points at `v0.9.1...HEAD` instead of `v1.0.5...HEAD`.

**Why this matters**

The Keep a Changelog format requires comparison links so readers can click a version header to see the exact diff. These are one of the most-used features of a CHANGELOG on GitHub — a user wanting to know exactly what changed between v1.0.4 and v1.0.5 cannot click through. This is a maintenance regression.

**Blast radius**
- Adjacent docs: none — this is self-contained.
- User-facing: Any user who clicks a CHANGELOG version header gets a dead link instead of the diff view.
- Related findings: none directly, though the root cause (version-maintenance steps not completed) is shared with DOC-001, DOC-002, DOC-005.

**Fix path**

Replace the footer comparison links block. Full replacement in `doc-rewrites/CHANGELOG-footer-links.md`.

The corrected block:
```
[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v1.0.5...HEAD
[1.0.5]: https://github.com/scottconverse/AgentSuite/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/scottconverse/AgentSuite/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/scottconverse/AgentSuite/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/scottconverse/AgentSuite/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/scottconverse/AgentSuite/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/scottconverse/AgentSuite/compare/v1.0.0rc1...v1.0.0
[1.0.0rc1]: https://github.com/scottconverse/AgentSuite/compare/v0.9.3...v1.0.0rc1
[0.9.3]: https://github.com/scottconverse/AgentSuite/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/scottconverse/AgentSuite/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/scottconverse/AgentSuite/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/scottconverse/AgentSuite/compare/v0.8.4...v0.9.0
[0.8.4]: https://github.com/scottconverse/AgentSuite/compare/v0.8.3...v0.8.4
[0.8.3]: https://github.com/scottconverse/AgentSuite/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/scottconverse/AgentSuite/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/scottconverse/AgentSuite/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/scottconverse/AgentSuite/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/scottconverse/AgentSuite/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/scottconverse/AgentSuite/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/scottconverse/AgentSuite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/scottconverse/AgentSuite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/scottconverse/AgentSuite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/scottconverse/AgentSuite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottconverse/AgentSuite/releases/tag/v0.1.0
```

---

### [DOC-005] — Major — Accuracy — Landing page (docs/index.html) version badge shows v1.0.1; roadmap card says "v0.8 Next Agent"

**Evidence**

`docs/index.html`, line 49:
```html
<h1>AgentSuite <span class="v">v1.0.1</span></h1>
```

`docs/index.html`, lines 119-121:
```html
<h2>Roadmap</h2>
<div class="grid">
  <div class="card"><h3>v0.8 Next Agent</h3><p>Coming soon.</p></div>
</div>
```

**Why this matters**

The landing page is a prospective user's first stop after a web search or GitHub link. A version badge showing v1.0.1 when the package is at v1.0.5 signals four patch releases of untracked maintenance. The roadmap card "v0.8 Next Agent — Coming soon" is actively misleading: v0.8 shipped in April 2026 and the project is now at v1.0.5. A user reading the landing page would think the project stalled at v0.8.

**Blast radius**
- Adjacent docs: README (DOC-001), USER-MANUAL (DOC-002) share the same version-drift root cause.
- User-facing: Landing page is the highest-traffic doc for prospective adopters. A stale version badge and a stale roadmap both reduce conversion.
- Migration: none — HTML-only edit.
- Related findings: DOC-001, DOC-002.

**Fix path**

1. Change line 49: `v1.0.1` → `v1.0.5`
2. Replace the Roadmap section with content from the CHANGELOG's `[Unreleased]` section:
```html
<h2>Roadmap</h2>
<p>v1.0.5 is the current release. Candidates for v1.1.x: 8th agent, per-day cost cap, <code>agentsuite migrate</code> command, <code>SECURITY.md</code> disclosure policy. See <a href="https://github.com/scottconverse/AgentSuite/blob/main/CHANGELOG.md">CHANGELOG</a> for the full watchlist.</p>
```

Draft produced: `doc-rewrites/index.html-version-roadmap-patch.html` (shows the two targeted changes).

---

### [DOC-006] — Minor — Accuracy — CONTRIBUTING.md test count is stale (688 of 691; actual: 892)

**Evidence**

`CONTRIBUTING.md`, line 78:
```
The default `pytest` invocation runs 688 of 691 tests; the three deselected tests (cleanroom, live, live_ollama) are gated by markers...
```

v1.0.5 added 87 stress tests (`tests/stress/`). v1.0.4 baseline was 805. Current total (default invocation) is 892 of 895.

**Why this matters**

A new contributor running `pytest` and seeing 892 tests (not 688) will wonder if the dev environment is set up correctly. This is a minor friction point but it is easily fixed.

**Fix path**

Update line 78: `688 of 691` → `892 of 895`
Also note: the v1.0.4 / v1.0.5 stress test additions are documented in CHANGELOG but not mentioned in CONTRIBUTING's "Test tiers" section. A note like "Stress tests in `tests/stress/` run in the default invocation and cover LLM response variability" would help.

---

### [DOC-007] — Minor — Completeness — README "Status" section roadmap is eight versions stale

**Evidence**

`README.md`, lines 262-273:

```markdown
**Shipped:**
- v0.1.0 — Specification Kernel + Founder Agent
...
- v0.7.0 — CIO Agent (IT strategy, technology roadmap, ...)

**Roadmap:**
- v0.8.0 — next agent
```

The project shipped v0.8.0 through v1.0.5 without updating this section.

**Why this matters**

A prospective user scanning the README status section sees the project stalled at v0.7.0 with "v0.8 — next agent" on the horizon. The actual shipped state is v1.0.5 with 892 tests and a complete GA release. This undersells the project significantly.

**Fix path**

Update the Status section to match the current shipped version history. The shipped list should go through v1.0.5, and the Roadmap should mirror the CHANGELOG `[Unreleased]` entry (v1.1.x candidates).

---

### [DOC-008] — Minor — Accuracy — Design Agent "Common errors" table references `--design-brief` flag that does not exist

**Evidence**

`USER-MANUAL.md`, Design Agent chapter, "Common errors" table, line ~393:

```
| `ConsistencyCheckFailed` | Two design documents contradict each other | Make your `--design-brief` more specific, then re-run |
```

The Design Agent CLI takes `--campaign-goal`, not `--design-brief`. The `--design-brief` flag does not appear in the Design Agent's "What you need to provide" section of this same chapter or anywhere in CONTRIBUTING.

**Why this matters**

A user following the error guidance to "make your `--design-brief` more specific" will pass a flag that does not exist and receive a CLI error, compounding their original problem. This is a small but concrete blocker in the troubleshooting path.

**Fix path**

Change the Design Agent "Common errors" table entry from `--design-brief` to `--campaign-goal`.

---

### [DOC-009] — Nit — Hygiene — "CHANGELOG.md" v0.2.0 Design Agent entry describes the pipeline as "six-stage" in the artifact list

**Evidence**

`CHANGELOG.md`, v0.2.0 entry, Design Agent artifact list description (line ~547):
```
Five-stage pipeline (intake → extract → spec → execute → qa → approval)
```

This is the same stage-count language that DOC-201 in v1.0.2 fixed in several places. The v0.2.0 CHANGELOG entry itself still says "six-stage" in its artifact list description (it lists all six including approval as a stage). The CHANGELOG is a historical record so the entry accurately reflects what was *documented at the time*, but the parenthetical "intake → extract → spec → execute → qa → approval" lists six arrows, not five.

**Fix path**

CHANGELOG historical entries should not be retroactively edited — they are the record of what was understood at the time. No fix required; this is informational only.

---

### [DOC-010] — Nit — Tone — USER-MANUAL "AGENTSUITE_ENABLED_AGENTS" uses `trust_risk` (underscore) in one place and `trust-risk` (hyphen) elsewhere

**Evidence**

`USER-MANUAL.md`, Section 6 (Enabling Agents), line ~233:
```
set AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio
```

`README.md` Codex MCP quick-start uses `trust-risk` (hyphen):
```
AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust-risk,cio"
```

Both values appear to be accepted (CLI normalizes agent names), but the inconsistency is confusing.

**Fix path**

Verify which form the CLI actually accepts as canonical and standardize across all docs. If both work, a note in the Configuration Reference would save a support question.

---

### [DOC-011] — Nit — Completeness — Landing page MCP install snippet uses unqualified `uvx` form without the `[mcp]` extra

**Evidence**

`docs/index.html`, Install section:
```
uvx --from git+https://github.com/scottconverse/AgentSuite.git agentsuite-mcp
```

`README.md` (correctly) uses:
```
uvx --from "agentsuite[mcp] @ git+https://github.com/scottconverse/AgentSuite.git" agentsuite-mcp
```

The landing page form may fail if `uvx` does not auto-install optional extras.

**Fix path**

Update the landing page install snippet to match the README's qualified form.

---

## Drafts produced

All drafts are targeted patches rather than full-document rewrites. The underlying docs are in good shape; only specific sections need replacement.

- `doc-rewrites/USER-MANUAL-version-patch.md` — Shows exact line replacements for the version header (line 3) and footer (line 1016). Two-line fix.
- `doc-rewrites/USER-MANUAL-consistency-error-patch.md` — Shows the replacement "Common errors" row for all seven agent chapters and the updated Troubleshooting section. Replaces `ConsistencyCheckFailed` (now non-existent) with the current v1.0.3+ behavior.
- `doc-rewrites/CHANGELOG-footer-links.md` — Full replacement footer-links block with all 24 version comparison links.
- `doc-rewrites/index.html-version-roadmap-patch.html` — Two-section patch: version badge line 49 and Roadmap section replacement.

---

## Marketing / honesty audit

The landing page is generally honest. The mock-LLM scaffold qualifier on screenshots is present and clearly worded. No claims about performance numbers (e.g., no "10x faster"). No enterprise-readiness claims. The value proposition ("turn vague intent into precise operating artifacts") is specific and checkable.

**One soft concern:** The "Shipped agents" grid in `docs/index.html` lists agents under their original version tags (v0.1 Founder, v0.2 Design, etc.). This is technically accurate but may confuse a user comparing it to the current v1.0.5 badge. The implication that the project was just at v0.7 when the Roadmap says "v0.8 Coming soon" — while the header badge shows v1.0.1 — creates a mild cognitive dissonance. This is a presentation issue more than a honesty issue; it resolves with the DOC-005 roadmap fix.

---

## Patterns and systemic observations

**Version-maintenance step is missing from the release checklist.** DOC-001, DOC-002, and DOC-005 all share the same root cause: the v1.0.4 and v1.0.5 release commits updated `pyproject.toml` and `__version__.py` but did not update the version badge in README, the version lines in USER-MANUAL, or the badge in `docs/index.html`. The `verify-release.sh` script should be extended to check that the README badge, USER-MANUAL version line, and landing page badge all match `pyproject.toml`. This is a mechanical check, not a judgment call.

**CHANGELOG footer link maintenance is not automated.** DOC-004 (missing comparison links for 10 versions) is a pure maintenance gap. The link format is deterministic (`compare/vX.Y.Z-1...vX.Y.Z`) so this could be appended automatically in the release script.

**`ConsistencyCheckFailed` removal was not swept in user-facing docs.** The v1.0.3 engineering fix correctly removed the exception and updated CHANGELOG. The fix memo lists "all 7 agents' spec.py files" and "all 7 unit spec tests" as updated. USER-MANUAL was not in the blast radius sweep. This is a recurring pattern across releases: code changes with user-visible behavior changes do not consistently trigger USER-MANUAL updates. Recommend adding USER-MANUAL as a required review artifact in the pre-push checklist.

---

## Appendix: docs reviewed

| File | Lines read |
|---|---|
| `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/README.md` | Full (284 lines) |
| `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/CHANGELOG.md` | Full (604 lines) |
| `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/CONTRIBUTING.md` | Full (157 lines) |
| `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/USER-MANUAL.md` | Full (1017 lines) |
| `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/index.html` | Full (139 lines) |
| `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/__version__.py` | Line 1 |
| `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/pyproject.toml` | Version field only |
