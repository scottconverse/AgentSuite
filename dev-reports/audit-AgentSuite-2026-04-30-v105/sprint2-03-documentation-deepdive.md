# Documentation Deep-Dive — AgentSuite Sprint 2

**Audit date:** 2026-04-30
**Role:** Technical Writer
**Scope audited:** Sprint 2 documentation changes only — DOC-003 (USER-MANUAL.md ConsistencyCheckFailed replacement), DOC-004 (CHANGELOG footer links and [1.0.7] entry), version sync across USER-MANUAL.md, docs/index.html, docs/troubleshooting.md. Also reviewed README.md for version accuracy.
**Writer mode:** audit-only
**Auditor posture:** Balanced

---

## TL;DR

Sprint 2 made genuine and correct documentation improvements: all 7 agent error tables were updated to the new `consistency_report.json` flow, CHANGELOG footer links are complete, and docs/index.html plus docs/troubleshooting.md are at v1.0.7. However, the DOC-003 fix is only half-done — it updated the per-agent error tables but left the Troubleshooting section (Section 10) and the Glossary still describing `ConsistencyCheckFailed` as a live exception. The CHANGELOG [1.0.7] entry has a structural defect: two `### Fixed` sections appear in a single version block, violating Keep-a-Changelog format. README.md was not updated and still shows **v1.0.6**. Five new Sprint 2 behaviors (awaiting_approval status rename, project_slug filter on list_runs, check_path_confinement errors, malformed cost-cap error, cost warning on stderr) have no coverage in the Troubleshooting guide. The overall doc suite is close to correct but needs targeted fixes before v1.0.7 can be considered fully documented.

---

## Severity roll-up (documentation)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 0 |
| Major | 4 |
| Minor | 2 |
| Nit | 1 |

---

## What's working

- **DOC-003 agent error tables: fully updated across all 7 chapters.** Every per-agent "Common errors" table (Founder line 325, Design line 392, Product line 456, Engineering line 529, Marketing line 601, Trust/Risk line 675, CIO line 746) now reads "Consistency check failed | The consistency check failed; AgentSuite creates `consistency_report.json` in the run directory | Open it, review the gaps it identifies, address them in your inputs, and re-run the agent." The replacement text is clear, accurate, and consistent in phrasing across all 7 chapters. That is a clean, complete sweep of the error tables.

- **DOC-004 CHANGELOG footer links: complete and correctly ordered.** All 20 entries from [0.1.0] through [Unreleased] have footer comparison links. URLs follow the `compare/vX.Y.Z...vA.B.C` pattern throughout. The [1.0.0] anchor correctly compares from v0.9.1, matching the release sequence.

- **Version sync on troubleshooting.md and docs/index.html.** Both files show v1.0.7 (troubleshooting.md line 4 footer and line 212; docs/index.html line 49 `<span class="v">v1.0.7</span>`). No version drift on these two assets.

- **USER-MANUAL.md version header and footer both updated.** Line 3 reads `**Version 1.0.7**` and line 1016 reads `*AgentSuite v1.0.7 — User Manual*`. Both instances correctly updated, as required by the Sprint 1 audit finding DOC-004.

- **Pipeline approval explanation updated to current behavior.** Section 5 (line 222–225) now correctly describes the post-QA state as "awaiting approval" in plain language, matching the new `awaiting_approval` status value introduced in Sprint 2. This prose addition is accurate and helpful for new users.

---

## What couldn't be assessed

- Whether the CHANGELOG comparison links resolve to live GitHub URLs — the audit is offline and cannot verify that tags `v1.0.0` through `v1.0.7` exist on the remote. URL patterns are structurally correct.
- Whether `docs/README-FULL.pdf` was updated for v1.0.7 — this file is out of scope for the Sprint 2 doc changes listed, but it is a required documentation artifact and its currency was not verified in this pass.

---

## Doc asset inventory

| Asset | Exists? | Status | Finding(s) |
|---|---|---|---|
| README.md | Yes | Weak (version stale) | DOC-S2-001 |
| USER-MANUAL.md | Yes | Adequate (two gaps remain) | DOC-S2-002, DOC-S2-003 |
| CHANGELOG.md | Yes | Adequate (structural defect in [1.0.7]) | DOC-S2-004 |
| docs/index.html | Yes | Strong | — |
| docs/troubleshooting.md | Yes | Adequate (new behaviors undocumented) | DOC-S2-005 |
| CONTRIBUTING.md | Yes | Not audited this sprint | — |
| LICENSE | Yes | Not audited this sprint | — |
| docs/README-FULL.pdf | Yes (assumed) | Not verified this sprint | — |

---

## Persona walk-through

### First-time user

A new user reading the USER-MANUAL from top to bottom will encounter accurate installation steps, correct agent error tables, and a correct description of the approval state. If they hit a consistency failure, the per-agent error table sends them to `consistency_report.json` — correct. But if they later consult the Troubleshooting section (Section 10), they will find a `ConsistencyCheckFailed` entry (line 847) describing it as a fatal exception with a specific retry message, which contradicts reality since v1.0.3. The contradiction is confusing for anyone who reaches the troubleshooting section.

### Returning user

A returning user scripting against the CLI JSON output who reads the README will see v1.0.6 in the header. They may conclude they are already on the latest version and not realize the `status` field has been renamed. The CHANGELOG is the correct source of truth here, but the README version badge is a quick-check signal for tool integrators and it is wrong.

### New team member

The CHANGELOG [1.0.7] section has two `### Fixed` blocks. A contributor learning the project's changelog conventions will see an inconsistent pattern — every other version entry uses each section type exactly once. This is a minor contributor experience issue, but the format is the project's stated standard.

---

## Findings

> **Finding ID prefix:** `DOC-S2-`
> **Categories:** Accuracy / Completeness / Onboarding / Architecture / API / FAQ / Marketing / Tone / Hygiene

---

### [DOC-S2-001] — Major — Accuracy — README.md version badge not updated to v1.0.7

**Evidence**

`README.md`, line 5:
```
> **v1.0.6** — Specification Kernel + Founder · Design · Product · Engineering · Marketing · Trust/Risk · CIO Agents
```

All other version-bearing docs (`USER-MANUAL.md` line 3, `docs/index.html` line 49, `docs/troubleshooting.md` line 4) show v1.0.7. README.md was not included in the version-sync pass.

**Why this matters**

The README is the first page almost every user and integrator reads. A version badge stuck at v1.0.6 tells returning users and tool integrators they are already up to date. The `status` → `awaiting_approval` rename introduced in Sprint 2 is a breaking change for scripts parsing CLI JSON output. A developer who reads "v1.0.6" and decides they are current will not see the CHANGELOG entry warning them of the breaking change.

**Blast radius**
- Adjacent docs: README.md is typically the primary source of version truth; its staleness can mask the importance of reading the CHANGELOG.
- User-facing: any integrator or developer who checks the README version badge to assess upgrade necessity will undercount the release.
- Migration: the `awaiting_approval` rename is a breaking change for existing automation. Stale README reduces the chance the breaking change is discovered before scripts fail.
- Related findings: DOC-S2-004 (CHANGELOG [1.0.7] structural issues compound this if a user does read the changelog).

**Fix path**

Update README.md line 5: change `**v1.0.6**` to `**v1.0.7**`. Also verify that `pyproject.toml`, `agentsuite/__version__.py`, and any other version-bearing files in the repo were included in the Sprint 2 version-bump commit.

---

### [DOC-S2-002] — Major — Accuracy — DOC-003 fix is incomplete: Troubleshooting section and Glossary still describe `ConsistencyCheckFailed` as a live exception

**Evidence**

`USER-MANUAL.md`, Section 10 (Troubleshooting), lines 847–851:
```
**`ConsistencyCheckFailed`**

Two of the nine documents produced by the agent contradict each other — for example, the target audience described in one document does not match the target audience in another. This usually means your inputs were ambiguous.

Fix: make your required inputs more specific. ...
```

`USER-MANUAL.md`, Glossary, line 903:
```
**ConsistencyCheckFailed:** An error that occurs when two of the nine documents produced by an agent contradict each other. The fix is to make your inputs more specific and re-run.
```

Both entries describe `ConsistencyCheckFailed` as an error a user will receive at the terminal. Since v1.0.3 (CHANGELOG entry: "removed the `ConsistencyCheckFailed` class and raise from all 7 agents' `spec.py` files; replaced with `requires_revision=True`"), this exception is never raised. The pipeline continues to completion and surfaces findings in `consistency_report.json`.

The Sprint 2 DOC-003 fix updated all 7 per-agent error tables (confirmed by review) but did not update Section 10 or the Glossary.

**Why this matters**

A user who hits a consistency issue and consults the troubleshooting section will follow wrong instructions: they will think they received a fatal error and a specific exception message, and they will try to fix inputs and re-run rather than reviewing `consistency_report.json` in their completed run. This is a misdirected recovery path that wastes user time and may lead them to abandon a successful run.

The Glossary is referenced by the layperson audience this manual explicitly targets. Stale glossary entries corrode the "you can trust this doc" contract.

**Blast radius**
- Adjacent docs: the Glossary entry for `ConsistencyCheckFailed` at line 903 perpetuates the same inaccuracy.
- User-facing: any user who reads Section 10 or the Glossary for guidance on a consistency issue will follow a recovery path that no longer applies.
- Related findings: DOC-S2-002 is the same root cause as what DOC-003 set out to fix. The fix was scoped to the error tables and did not sweep the full document.

**Fix path**

Section 10 (lines 847–851): replace the `ConsistencyCheckFailed` subsection with guidance matching the current behavior:

```markdown
**Consistency issues flagged in `consistency_report.json`**

If the agent's spec stage detects conflicts between the documents it produced, the run continues to completion but flags the issues in `consistency_report.json` in the run directory. This is not a fatal error — you will receive all output.

Open `consistency_report.json` in any text editor. It lists the specific mismatches found. You have two options:
1. Review the mismatches and decide they are acceptable, then approve normally.
2. Make your inputs more specific to resolve the conflicts, and re-run.
```

Glossary (line 903): remove the `ConsistencyCheckFailed` entry or update it to:
```
**ConsistencyCheckFailed:** (historical, v1.0.3 and earlier) An exception raised when documents contradicted each other. As of v1.0.3 this exception is no longer raised. Consistency findings are now surfaced in `consistency_report.json` in the run directory without stopping the pipeline.
```

---

### [DOC-S2-003] — Major — Completeness — Five Sprint 2 behaviors have no coverage in USER-MANUAL.md or docs/troubleshooting.md

**Evidence**

Sprint 2 introduced or changed the following user-visible behaviors. None appear in the user manual's troubleshooting section (Section 10) or in `docs/troubleshooting.md`:

1. **`awaiting_approval` status rename** (Sprint 2 `### Changed`): CLI JSON output `status` field now emits `awaiting_approval` instead of `approval`. The USER-MANUAL Section 5 correctly describes the concept (line 222) but does not document the specific `status` field value or warn that scripts expecting `"approval"` will break.

2. **`AGENTSUITE_COST_CAP_USD` malformed value error** (QA-003): setting this variable to a non-numeric value now produces an actionable error. This new error message is not documented anywhere in the user-facing docs. Users who misconfigure the variable will hit an undocumented error.

3. **Path confinement errors** (ENG-004): user-supplied file paths that escape the kernel scope now produce a specific error. This error is not documented in the troubleshooting guides.

4. **Cost warning now on stderr** (ENG-005): the cost warning behavior changed. Advanced users piping stdout to files and monitoring stderr will see different output. Not documented.

5. **`project_slug` filter on `list_runs`** (UX-006): the MCP `list_runs` tool now accepts `project_slug` for filtering. The CLI flags reference and the MCP documentation do not mention this parameter addition.

**Why this matters**

Items 1 and 2 directly affect user troubleshooting workflows. A user who sets `AGENTSUITE_COST_CAP_USD=ten` (a common typo pattern) will receive an error they cannot find in any doc. A developer whose script checks `state["status"] == "approval"` will silently break on upgrade.

**Blast radius**
- Adjacent docs: `docs/troubleshooting.md` lists only 5 failure modes and was not updated in Sprint 2. All 5 new behaviors fall outside its coverage.
- User-facing: `awaiting_approval` rename affects every script, automation, and MCP tool consumer that parses run status. Undocumented breaking changes are the highest practical risk for integrators.
- Migration: `awaiting_approval` rename is explicitly marked "(breaking change for scripts parsing this field)" in the CHANGELOG. A breaking change without a migration path documented in user-facing docs puts the burden entirely on users discovering the CHANGELOG before their automation breaks.
- Related findings: DOC-S2-001 (README version badge not updated compounds this — integrators who skip the README version check are also less likely to find the CHANGELOG breaking-change note).

**Fix path**

`docs/troubleshooting.md`: add a section 6 covering the malformed `AGENTSUITE_COST_CAP_USD` error with the correct value format and an example.

`USER-MANUAL.md` Section 9 (Configuration Reference): add a note under `AGENTSUITE_COST_CAP_USD` that the value must be a valid decimal number (e.g., `5.00` or `10`) and that non-numeric values produce an error.

`USER-MANUAL.md` Section 5 (or a new "Output format" note): document the `awaiting_approval` value specifically as the `status` field value emitted after the five stages complete, so script authors can rely on it.

---

### [DOC-S2-004] — Major — Hygiene — CHANGELOG [1.0.7] contains two `### Fixed` sections in one version block

**Evidence**

`CHANGELOG.md`, lines 11–29:
```markdown
## [1.0.7] - 2026-04-30

### Fixed
- ENG-002: ...
- ENG-004: ...
- ENG-005/UX-003: ...
- QA-003: ...
- QA-004: ...
- QA-005: ...

### Changed
- CLI JSON output: `status` field now emits `awaiting_approval`...

### Fixed
- UX-006: `list_runs` MCP tool now correctly filters by `project_slug` parameter

### Documentation
- DOC-003: ...
- DOC-004: ...
```

Keep-a-Changelog format (the project's stated standard, per line 3) specifies that each section type appears at most once per version entry. The v1.0.7 entry has `### Fixed` at line 13 and again at line 24. Every other version entry (v1.0.6, v1.0.5, v1.0.4, etc.) uses each section type exactly once.

Additionally, the `### Documentation` section (line 27) is not a standard Keep-a-Changelog section type. Standard types are: Added, Changed, Deprecated, Removed, Fixed, Security.

**Why this matters**

The CHANGELOG is the primary record of breaking changes. The `awaiting_approval` rename (the one breaking change in this release) sits in a `### Changed` section sandwiched between two `### Fixed` sections. A reader scanning for breaking changes may miss it because the section order is disruptive. Tools that parse Keep-a-Changelog format (release note generators, dependency bots) may also malfunction on duplicate section headers.

**Blast radius**
- Adjacent docs: the Unreleased section uses a non-standard `### Roadmap` section — this is a pre-existing pattern, but the `### Documentation` section in [1.0.7] compounds the inconsistency.
- User-facing: the breaking-change notice for `awaiting_approval` is harder to find.
- Related findings: DOC-S2-003 (breaking change underdocumented in user-facing docs — the CHANGELOG structural issue reduces the chance an integrator encounters the warning at all).

**Fix path**

Merge the two `### Fixed` sections into one. Move `UX-006` into the first `### Fixed` block. Move `DOC-003` and `DOC-004` into an `### Added` section or fold them into `### Changed`. Keep-a-Changelog does not have a `### Documentation` category — documentation-only changes are conventionally listed under `Changed` or `Added` depending on whether they add content or correct existing content.

Suggested restructured [1.0.7] entry:

```markdown
## [1.0.7] - 2026-04-30

### Changed
- CLI JSON output: `status` field now emits `awaiting_approval` instead of `approval` when a run is pending review (breaking change for scripts parsing this field)
- USER-MANUAL.md consistency failure instructions updated to reference `consistency_report.json` review flow (DOC-003; exception no longer raised since v1.0.3)

### Fixed
- ENG-002: AGENTSUITE_LLM_PROVIDER_FACTORY env var documented as TEST-ONLY; production guard added
- ENG-004: Path confinement for user-supplied file paths in kernel spec stage
- ENG-005/UX-003: Cost warning surfaced to stderr; zero-cost stage progress no longer shows $0.0000
- QA-003: AGENTSUITE_COST_CAP_USD now reports an actionable error on malformed values
- QA-004: Gemini LLMResponse.model field now reflects actual model version used by the API
- QA-005: Unknown agent name now exits with code 1 and lists valid agent names
- UX-006: `list_runs` MCP tool now correctly filters by `project_slug` parameter

### Added
- CHANGELOG footer links for v1.0.0 through v1.0.6 (DOC-004)
```

---

### [DOC-S2-005] — Minor — Completeness — `docs/troubleshooting.md` covers 5 failure modes and was not updated for Sprint 2

**Evidence**

`docs/troubleshooting.md` lists exactly five failure modes:
1. `NoProviderConfigured`
2. `UnknownAgent`
3. Run directory already exists
4. Ollama connection refused
5. `HardCapExceeded`

The file version header (line 4) reads `Version 1.0.7` — correctly updated. But the content was not updated: Sprint 2 added at least one new user-facing error (`AGENTSUITE_COST_CAP_USD` malformed value, QA-003) and changed the behavior of cost warnings (ENG-005). Neither appears in the guide.

The overlap between this finding and DOC-S2-003 is intentional — the two docs should be cross-updated together. This finding specifically flags that `docs/troubleshooting.md` has a version number that implies currency, which it does not fully have.

**Why this matters**

A version number of 1.0.7 on a troubleshooting guide implies the guide covers v1.0.7 failure modes. A user on v1.0.7 who consults it for a cost-cap misconfiguration error will find nothing. The mismatch between the version stamp and the content is a credibility gap.

**Fix path**

Add a section 6 to `docs/troubleshooting.md` covering the malformed `AGENTSUITE_COST_CAP_USD` error. The fix is small — about 15 lines following the same pattern as the `HardCapExceeded` section.

---

### [DOC-S2-006] — Minor — Accuracy — CHANGELOG breaking-change notation inconsistent across versions

**Evidence**

`CHANGELOG.md`:
- v0.9.0 (line 323) marks breaking changes with `### ⚠ BREAKING` header.
- v0.8.2 (line 425) marks breaking changes with `### ⚠ BREAKING` header.
- v1.0.7 (line 21) marks its breaking change inline in a `### Changed` bullet: "(breaking change for scripts parsing this field)".

The inline `(breaking change...)` notation is less visible than the dedicated `### ⚠ BREAKING` header used in earlier releases.

**Why this matters**

A developer scanning the CHANGELOG for breaking changes across multiple releases uses visual pattern matching. The inconsistency means the v1.0.7 breaking change is harder to find than the v0.9.0 and v0.8.2 ones.

**Fix path**

Add `### ⚠ BREAKING` as a section header in [1.0.7], moving the `awaiting_approval` rename bullet under it:

```markdown
### ⚠ BREAKING
- CLI JSON output: `status` field now emits `awaiting_approval` instead of `approval` when a run is pending review. Scripts that check `status == "approval"` must be updated.
```

This is a Minor because the information is present — it just needs better visual prominence.

---

### [DOC-S2-007] — Nit — Hygiene — `### Documentation` is a non-standard Keep-a-Changelog section type

**Evidence**

`CHANGELOG.md`, line 27: `### Documentation`

Keep-a-Changelog 1.1.0 (the project's stated format per line 3) defines six section types: Added, Changed, Deprecated, Removed, Fixed, Security. `Documentation` is not one of them.

This is a nit because the meaning is clear and it does not block a reader from understanding the release notes. It is worth fixing as part of the DOC-S2-004 restructure.

**Fix path**

Fold DOC-003 and DOC-004 bullets into `### Changed` (corrections to existing content) or `### Added` (new content). Resolved as part of the DOC-S2-004 fix path above.

---

## Drafts produced

Writer mode is audit-only; no drafts produced in this pass.

---

## Marketing / honesty audit

Not in scope for this sprint audit. The landing page (docs/index.html) feature claims were reviewed only for version accuracy; no new marketing accuracy findings emerged. The page accurately represents all 7 agents as shipped. The roadmap section ("multi-agent pipelines and per-day cost controls") is consistent with the CHANGELOG [Unreleased] roadmap entry.

---

## Patterns and systemic observations

**The DOC-003 fix illustrates a recurring partial-sweep pattern.** The fix correctly identified the 7 per-agent error tables as the primary location and updated all of them. But it did not sweep the full document for other references to `ConsistencyCheckFailed` — the Troubleshooting section and Glossary were missed. This same pattern appeared in Sprint 1 (ENG-001 path traversal fix scoped too narrowly). The fix strategy for any "remove reference X from the docs" task should include a full-document grep before declaring done.

**Version sync is almost complete but not quite.** Four of five version-bearing assets were updated (USER-MANUAL.md ×2, docs/index.html, docs/troubleshooting.md). README.md was missed. A mechanical pre-push version check (`grep -r "v1.0\." *.md docs/`) would catch this class of miss automatically.

**The CHANGELOG is strong in breadth but needs format discipline.** 20 entries with detailed per-finding descriptions is genuinely helpful to integrators. The structural issues in [1.0.7] (duplicate sections, non-standard type, inconsistent breaking-change notation) are fixable in one editorial pass and worth doing before the [Unreleased] entries accumulate.

---

## Appendix: docs reviewed

- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\USER-MANUAL.md` — full (1017 lines)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\CHANGELOG.md` — full (652 lines)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\index.html` — full (138 lines)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\troubleshooting.md` — full (213 lines)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\README.md` — lines 1–280 (version badge, configuration section)
- Reference files: `technical-writer.md`, `severity-framework.md`, `blast-radius.md`, `03-documentation-deepdive.md` (template)
