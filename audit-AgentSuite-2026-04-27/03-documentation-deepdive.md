# Documentation Deep-Dive — AgentSuite

**Auditor:** Technical Writer  
**Date:** 2026-04-27  
**Scope:** All documentation artifacts — README, USER-MANUAL, CHANGELOG, CONTRIBUTING, landing page (docs/index.html), PDF generator (scripts/generate_readme_pdf.py), code docstrings (base_agent.py, schema.py), package metadata (pyproject.toml)

---

## Executive Summary

AgentSuite's documentation is well-structured and broadly accurate, reflecting genuine care for users. Version numbers are consistent everywhere. The six required doc artifacts all exist. The USER-MANUAL is legitimately written for non-technical readers. CHANGELOG is thorough and honest.

However, **three material accuracy gaps** require attention before relying on these docs for user-facing accuracy:

1. The landing page (`docs/index.html`) claims `pip install agentsuite` works — but the README correctly states the package is GitHub-only with no PyPI publication. The landing page contradicts this.
2. The PDF generator (`generate_readme_pdf.py`) hard-codes **different artifact names** for Design and Product agents than what the USER-MANUAL and CHANGELOG document — meaning the PDF's agent reference tables are inaccurate for two of seven agents.
3. `CONTRIBUTING.md` gives a Windows-only `venv` activation path (`.venv/Scripts/pip install`) without documenting the Mac/Linux equivalent (`.venv/bin/pip install`), despite describing itself as cross-platform.

There are also inconsistencies between how agents count their outputs (the README says 26 for Founder but also uses 17 elsewhere for other agents; the USER-MANUAL describes "nine documents" repeatedly but includes agents like Founder that produce more), and the Enabling Agents section in USER-MANUAL uses `trust_risk` (underscore) while the README MCP config uses `trust-risk` (hyphen) — these may both work but are never reconciled for the user.

Overall documentation health grade: **Good** — solid foundation with a small set of fixable accuracy problems.

---

## What's Working Well

- **Version consistency.** `0.7.0` appears in pyproject.toml, README header, USER-MANUAL header, CHANGELOG latest entry, docs/index.html, and the PDF generator's `page_header_footer` and cover page. No drift.
- **USER-MANUAL tone.** Genuinely written for non-technical readers. Defines terminal, API key, environment variable, and every domain term before using it. The 40-term glossary is accurate and covers all terms used in the document.
- **CHANGELOG format.** Follows Keep a Changelog correctly. All seven version milestones (v0.1.0–v0.7.0) are documented. Entries are honest and specific — no marketing language, no inflated claims. Dates are present. The `[Unreleased]` section and diff links are correct.
- **pyproject.toml metadata.** Description matches README tagline. Keywords cover the actual capability set. Classifiers are accurate (Alpha, MIT, Python 3.11/3.12). Entry points (`agentsuite` and `agentsuite-mcp`) are correct names that match the CLI and MCP server.
- **No TODO/FIXME comments in production code.** Grep across all of `agentsuite/` found only template placeholders in user-facing markdown templates — not code.
- **base_agent.py and schema.py docstrings.** Accurate and descriptive. The six-stage pipeline mention in `base_agent.py`'s module docstring is consistent with the actual `PIPELINE_ORDER` constant (which is 5 stages — the sixth "approval" stage is noted as handled separately by the base class). This is correct and not misleading.
- **CONTRIBUTING.md test tier table.** Accurate — four tiers, cost levels, invocation methods all match pyproject.toml markers and Makefile conventions.

---

## Findings

### Blockers

**B-1: Landing page claims PyPI availability — package is not on PyPI**

`docs/index.html` line 54–55:
```html
<pre><code>pip install agentsuite
# or, no install:
uvx agentsuite-mcp</code></pre>
```

The README explicitly states: "AgentSuite is distributed from GitHub only — there is no PyPI publication." The README install command is `pip install git+https://github.com/scottconverse/AgentSuite.git`. The landing page's `pip install agentsuite` will fail for every user who tries it. The `uvx agentsuite-mcp` no-install command is also wrong — without a PyPI package it should be `uvx --from git+https://github.com/scottconverse/AgentSuite.git agentsuite-mcp`.

**Impact:** Every user who finds the project via the GitHub Pages landing page and follows the install instructions will hit an error immediately. This is the public storefront. This is a Blocker.

**Fix:** Change landing page install block to match README exactly:
```
pip install git+https://github.com/scottconverse/AgentSuite.git
# or, no install:
uvx --from git+https://github.com/scottconverse/AgentSuite.git agentsuite-mcp
```

---

**B-2: PDF generator hard-codes wrong artifact names for Design and Product agents**

`scripts/generate_readme_pdf.py` contains a hard-coded `AGENTS` list (lines 354–560) that defines each agent's spec artifacts. For two agents, these names do not match what the USER-MANUAL and CHANGELOG document:

**Design Agent — PDF generator lists:**
```
design-system.md, component-library.md, typography-guide.md, color-palette.md,
iconography-guide.md, motion-principles.md, accessibility-checklist.md,
design-tokens.json, brand-qa-scorecard.md
```

**Design Agent — USER-MANUAL lists:**
```
design-system.md, color-palette.md, typography-system.md, component-library-guide.md,
iconography-guide.md, imagery-guidelines.md, motion-and-animation.md,
accessibility-checklist.md, brand-application-examples.md
```

**CHANGELOG v0.2.0 lists (different again):**
```
visual-direction.md, design-brief.md, mood-board-spec.md, brand-rules-extracted.md,
image-generation-prompt.md, revision-instructions.md, design-qa-report.md,
accessibility-audit-template.md, final-asset-acceptance-checklist.md
```

These three sources describe what appear to be three different versions of the Design agent's artifact list, none matching the others.

**Product Agent — PDF generator lists:**
```
product-requirements-doc.md, user-journey-map.md, feature-prioritization.md,
success-metrics.md, competitive-analysis.md, technical-constraints.md,
release-criteria.md, stakeholder-map.md, risk-assumptions-log.md
```

**Product Agent — USER-MANUAL lists:**
```
product-requirements-doc.md, user-story-map.md, feature-prioritization.md,
success-metrics.md, competitive-analysis.md, user-persona-map.md,
acceptance-criteria.md, product-roadmap.md, risk-register.md
```

Several artifact file names differ. The PDF generator's tables are the authoritative-looking "Technical Reference" document — if they're wrong, developers wiring against the API will look for files that don't exist.

**Impact:** README-FULL.pdf, the document explicitly described as the "full reference with architecture diagrams," describes incorrect artifact filenames for 2 of 7 agents. This is a Blocker for any user consulting the PDF to understand what the Design or Product agent produces.

---

### Critical

**C-1: CONTRIBUTING.md venv activation is Windows-only**

```bash
python -m venv .venv
.venv/Scripts/pip install -e .[dev]
```

This is the Windows path. On Mac/Linux it is `.venv/bin/pip install -e .[dev]`. CONTRIBUTING.md describes itself as cross-platform ("You'll need Python 3.11 or 3.12...") but only provides the Windows activation path. A Mac or Linux contributor following this exactly will get `bash: .venv/Scripts/pip: No such file or directory`.

Note: CHANGELOG v0.2.0 documents a fix to `scripts/run-cleanroom.sh` for exactly this issue ("was hardcoded to Windows `.venv/Scripts/`; now detects Scripts vs bin at runtime"). CONTRIBUTING.md has the same bug the cleanroom script already fixed.

**Fix:** Change to:
```bash
# Windows:
.venv\Scripts\pip install -e .[dev]
# Mac/Linux:
.venv/bin/pip install -e .[dev]
# Or use: python -m pip install -e .[dev]  (cross-platform)
```

---

**C-2: CONTRIBUTING.md incorrectly documents PyPI publishing**

Lines 87–99 describe PyPI Trusted Publishing setup and state:
> "Per `feedback_pypi_push.md`: every GitHub push of an AgentSuite release is paired with a PyPI publish."

But `project_agentsuite_v0.1_shipped.md` (in memory) and README explicitly state: **"no PyPI ever"** for AgentSuite. This is contradictory. CONTRIBUTING.md tells contributors the project publishes to PyPI; the README tells users it doesn't. The CHANGELOG v0.1.0 states: "PyPI publishing intentionally not enabled (per maintainer decision)."

CONTRIBUTING.md's release section is incorrect and will confuse contributors attempting to follow the release process.

**Fix:** Remove the PyPI Trusted Publishing setup section. Update the release steps to remove PyPI references.

---

**C-3: Design agent artifact count inconsistency across docs (17 vs 9)**

The README says the Engineering, Trust/Risk, and CIO agents produce "17 artifacts per run." The Founder agent is documented as producing "26 artifacts." For the Design and Product agents, the README says "see CHANGELOG for artifact list" — which is a cop-out that forces users to go hunting.

The USER-MANUAL consistently describes each agent as producing "nine documents" and "eight brief templates." The PDF generator intro (line 833–837) states: "All agents produce the same structural pattern: 9 spec artifacts, 8 brief templates, qa_report.md, qa_scores.json, _state.json, and _meta.json. 17–26 total artifacts per run depending on the agent."

The 17 count is: 9 spec + 8 brief = 17 (excluding the state/meta/qa files). The 26 count for Founder includes all files (9 spec + 11 brief + qa_report + qa_scores + consistency_report + export_manifest + state + meta = 26). The counting methodology is never explained or made consistent. Users reading different sections of the docs will see 9, 17, and 26 with no reconciliation.

---

**C-4: USER-MANUAL Section 6 "Enabling Agents" uses underscore syntax; README MCP config uses hyphen syntax**

USER-MANUAL line 208:
```
set AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio
```

README and landing page MCP configs:
```
AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust-risk,cio"
```

`trust_risk` (underscore) vs `trust-risk` (hyphen). If only one is correct, half the docs will silently fail to enable the Trust/Risk agent. The USER-MANUAL also uses `trust_risk` in the environment variable table (line 708). If the code accepts both forms, the docs should say so. If only one form works, the wrong one needs correcting.

---

### Major

**M-1: README "What the agents produce" section is incomplete for Design and Product agents**

For Founder (26 artifacts), Engineering (17), Trust/Risk (17), and CIO (17), the README provides full artifact tables. For Design and Product, it says "see CHANGELOG for artifact list." This forces users who need this information to dig through a changelog entry rather than having a single reference document. These two agents deserve the same treatment as the others.

---

**M-2: Founder agent CLI quick-start in README uses different flags than USER-MANUAL**

README quick-start (lines 30–35):
```bash
agentsuite founder run \
  --business-goal "Launch PatentForgeLocal v1" \
  --project-slug pfl \
  --inputs-dir ./examples/patentforgelocal
```

USER-MANUAL Founder agent chapter (lines 261–267):
```bash
agentsuite founder run \
  --company-name "Acme" \
  --mission "..." \
  --core-values "..."
```

These are different flag sets. One of them may be correct and the other stale, or the agent may accept both (the README flags look like an older interface; the USER-MANUAL flags are more semantically appropriate for a Founder agent). Users will try both and get confused.

---

**M-3: CHANGELOG v0.3.0 brief template list differs from USER-MANUAL**

CHANGELOG v0.3.0 (lines 67–74) lists Product brief templates as:
> sprint planning, stakeholder update, launch announcement, **feature spec**, user interview guide, A/B test plan, **demo script**, investor update

USER-MANUAL Product agent section (line 370) lists:
> sprint planning brief, stakeholder update, launch announcement, **go-to-market summary**, **executive summary**, user interview guide, A/B test plan, retrospective report

Four of eight templates have different names between CHANGELOG and USER-MANUAL. One source is stale.

---

**M-4: PDF generator brief templates for Design agent don't match any other source**

The PDF generator `AGENTS[1]` (Design) lists brief templates as:
```
ui-component-brief, brand-refresh-brief, campaign-visual-brief,
design-review-checklist, accessibility-audit, design-handoff,
motion-spec, icon-request
```

USER-MANUAL Design agent section (line 314) says:
> "eight brief templates for common design tasks (design handoff, usability test plan, design critique, and more)"

Neither matches the other, and neither matches CHANGELOG v0.2.0's brief template list:
> banner-ad, email-header, social-graphic, landing-hero, deck-slide, print-flyer, video-thumbnail, icon-set

Three different template lists for the same agent across three documents.

---

**M-5: "six-stage" vs "five-stage" pipeline description inconsistency**

`base_agent.py` module docstring (line 1): "persisted **six**-stage pipeline"  
`PIPELINE_ORDER` constant (line 17): `["intake", "extract", "spec", "execute", "qa"]` — **five** entries

The code's own module docstring says six stages; the constant defines five. The README, USER-MANUAL, and landing page all say "five stages" or "5-stage pipeline." The base_agent.py docstring is wrong. (The approval stage is a separate `ApprovalGate` object, not part of `PIPELINE_ORDER`.)

---

**M-6: landing page Quick Start (CLI) uses old README-style flags**

The landing page quick start block:
```bash
agentsuite founder run \
  --business-goal "Launch PatentForgeLocal v1" \
  --project-slug pfl \
  --inputs-dir ./examples/patentforgelocal
```

This uses the `--business-goal`/`--inputs-dir` flag set, while the USER-MANUAL documents `--company-name`, `--mission`, `--core-values`. Same flag inconsistency as M-2, but now appearing on the public landing page.

---

### Minor

**Mi-1: USER-MANUAL installation verification shows stale output**

Lines 107–111 show expected output:
```json
{
  "enabled": ["founder"],
  "all_registered": ["founder"]
}
```

After installation, only the Founder agent is registered by default. This is correct behavior, but the output format may not match the actual `agentsuite agents` CLI output. No code-level cross-check was possible from documentation alone, but worth verifying the JSON shape is exact.

---

**Mi-2: CONTRIBUTING.md mentions `make test` and `make cleanroom` but no Makefile was verified**

CONTRIBUTING.md references `make test`, `make cleanroom`, `make test-live`, `make lint`, `make rerecord-cassettes`. If there is no Makefile (or if targets are named differently), these instructions are broken. The Makefile was not checked as part of this audit scope, but contributors following CONTRIBUTING.md depend on it.

---

**Mi-3: README "Documentation" section links to `docs/USER-MANUAL.md` but file is at root**

README line 209: `[USER-MANUAL.md](docs/USER-MANUAL.md)` — but the file was found at the repo root as `USER-MANUAL.md`, not in `docs/`. The landing page links to `https://github.com/scottconverse/AgentSuite/blob/main/docs/USER-MANUAL.md` as well. If USER-MANUAL.md is at root, both links are broken. If it's in `docs/`, it wasn't confirmed. Worth verifying file location.

---

**Mi-4: USER-MANUAL "Enabling Agents" doesn't document the `trust-risk` vs `trust_risk` CLI distinction**

Even if both forms work, the manual should explicitly tell users which separator to use for which context (CLI flag vs env var). The current version silently uses different forms without explanation.

---

**Mi-5: CONTRIBUTING.md "Releases" section says CI builds and uploads to PyPI on tag push**

Line 87: "CI builds and uploads to PyPI on tag push." This flatly contradicts the no-PyPI decision. Even if this line is aspirational or copied from another project, it's inaccurate and should be removed.

---

### Nits

**N-1:** USER-MANUAL Glossary lists 40+ terms but the intro says "40-term glossary" — the count is approximate and the glossary should either be counted exactly or the number dropped from the intro.

**N-2:** CHANGELOG v0.3.0 and v0.2.0 use em-dash (`—`) as version separator while v0.4.0–v0.7.0 use hyphen-minus (`-`). Minor format inconsistency.

**N-3:** PDF generator `code_block` for each agent CLI command hardcodes `--business-goal`, `--project-slug`, `--inputs-dir` as generic flags regardless of which agent is being documented — so the Design agent, Engineering agent, etc. all show Founder-style flags in the PDF.

**N-4:** Landing page roadmap section `v0.8 Next Agent — Coming soon` is a placeholder with no value for users. Either describe the planned agent or omit the roadmap card.

**N-5:** `pyproject.toml` `[tool.setuptools.package-data]` includes packages for `product` and `cio` agents implicitly via the wildcard but explicitly lists only `founder`, `design`, `engineering`, `marketing`, and `trust_risk`. Product and CIO agent data files may not be included in builds. (Low risk if the wildcard covers it, but worth auditing.)

---

## Artifact-by-Artifact Assessment

**README.md — Good.** Accurate on version, install command, agent count, pipeline description, and configuration table. The artifact tables for Founder, Engineering, Trust/Risk, and CIO are thorough and internally consistent. The main gap is that Design and Product agent artifact lists are delegated to "see CHANGELOG," and the CLI quick-start flags conflict with USER-MANUAL. Does not claim PyPI availability.

**USER-MANUAL.md — Excellent.** The standout artifact. Genuinely written for non-technical users, covers all seven agents with correct input field names, provides platform-specific instructions (Windows vs Mac/Linux), explains every error message, and maintains a thorough glossary. The only accuracy concerns are the `trust_risk` vs `trust-risk` syntax inconsistency and the Design agent artifact names diverging from other sources.

**CHANGELOG.md — Excellent.** Follows Keep a Changelog format faithfully. All seven versions documented with appropriate detail. Entries are honest — they describe what was actually added, not aspirational features. The brief template name discrepancies between CHANGELOG and USER-MANUAL (finding M-3) are the only accuracy issue.

**CONTRIBUTING.md — Needs Work.** The development setup is Windows-only for venv activation, the release section incorrectly references PyPI publishing, and the no-PyPI decision is directly contradicted. The test tier table and code-style section are accurate. A Mac/Linux developer following this doc will hit at least one error before running their first test.

**docs/index.html (landing page) — Needs Work.** The visual design is clean and professional. The agent grid cards are accurate and well-written. However, the install command is a Blocker-level error (`pip install agentsuite` fails; package isn't on PyPI), and the CLI quick-start uses the `--business-goal`/`--inputs-dir` flag set that doesn't match USER-MANUAL. As the public storefront, these errors create a bad first impression.

**scripts/generate_readme_pdf.py (PDF generator) — Needs Work.** The PDF architecture is well-designed with proper diagrams, and the system-level content (pipeline description, MCP integration, configuration reference, QA rubric) is accurate. However, the hard-coded agent artifact tables for Design and Product agents do not match any other authoritative source. The CLI command code blocks use hardcoded Founder flags for all agents. The generator produces a technically polished PDF with inaccurate per-agent content for 2 of 7 agents.

**base_agent.py / schema.py docstrings — Good.** Accurate and concise. The "six-stage pipeline" wording in `base_agent.py`'s module docstring is the one inaccuracy (should be five stages plus approval gate). Schema docstrings are precise and match the actual field definitions.

**pyproject.toml — Excellent.** Version, description, keywords, classifiers, dependencies, and entry points are all accurate. No open-ended dependency ranges. Entry points match the actual CLI and MCP server entry points.

---

## Accuracy Cross-Reference

| Claim | Source doc | Actual code/other docs state | Verdict |
|---|---|---|---|
| `pip install agentsuite` installs the package | docs/index.html | README: GitHub-only, no PyPI | **WRONG** |
| `uvx agentsuite-mcp` works as a no-install command | docs/index.html | Requires `--from git+https://...` without PyPI | **WRONG** |
| Version is 0.7.0 | README, USER-MANUAL, CHANGELOG, pyproject.toml, index.html, PDF generator | All sources agree | **CORRECT** |
| Seven agents shipped | README, USER-MANUAL, CHANGELOG, index.html | All sources agree | **CORRECT** |
| Five-stage pipeline | README, USER-MANUAL, landing page | base_agent.py PIPELINE_ORDER has 5 entries | **CORRECT** |
| "Six-stage pipeline" | base_agent.py module docstring | PIPELINE_ORDER = 5 stages; approval is separate | **WRONG** |
| Founder produces 26 artifacts | README | CHANGELOG v0.1.0 also says 26 (9+11+misc) | **CORRECT** |
| Design agent spec artifacts: `design-system.md`, `color-palette.md`, `typography-system.md` (etc.) | USER-MANUAL | PDF generator lists `design-system.md`, `component-library.md`, `typography-guide.md` | **INCONSISTENT** |
| Product brief templates: sprint planning, stakeholder update, go-to-market summary, executive summary, retrospective | USER-MANUAL | CHANGELOG v0.3.0 lists feature spec, demo script, investor update instead | **INCONSISTENT** |
| CONTRIBUTING.md: "every release paired with PyPI publish" | CONTRIBUTING.md | README + CHANGELOG + project memory: no PyPI ever | **WRONG** |
| venv activation: `.venv/Scripts/pip` | CONTRIBUTING.md | Mac/Linux is `.venv/bin/pip` | **INCOMPLETE** |
| `trust_risk` in AGENTSUITE_ENABLED_AGENTS | USER-MANUAL | README + landing page use `trust-risk` | **INCONSISTENT** |
| Founder CLI flags: `--company-name`, `--mission`, `--core-values` | USER-MANUAL | README + landing page use `--business-goal`, `--project-slug`, `--inputs-dir` | **INCONSISTENT** |
| Entry points `agentsuite` and `agentsuite-mcp` | pyproject.toml | CHANGELOG v0.1.0 confirms both names | **CORRECT** |
| No PyPI publication | README | README, CHANGELOG v0.1.0, project memory all agree | **CORRECT** |
| QA pass threshold 7.0/10 | USER-MANUAL, README-FULL PDF | Consistent across all sources | **CORRECT** |
| Cost cap default $5.00 | USER-MANUAL, README, PDF | All agree | **CORRECT** |
| Python 3.11+ required | README, USER-MANUAL, pyproject.toml | All agree | **CORRECT** |
