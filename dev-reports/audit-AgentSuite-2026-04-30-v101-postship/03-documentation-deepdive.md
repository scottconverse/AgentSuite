# Documentation Deep-Dive — AgentSuite v1.0.1

**Audit date:** 2026-04-30
**Role:** Technical Writer
**Scope audited:** README.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, USER-MANUAL.md (root 984-line + docs/USER-MANUAL.md 652-line), docs/index.html, docs/troubleshooting.md, docs/test-coverage.md, docs/rubric-audit.md, docs/adr/ (all 7 ADRs + index), docs/community/discussions-seeds.md, docs/community/launch-posts.md, docs/community/good-first-issues.md, SECURITY.md, pyproject.toml (version metadata). Six required doc artifacts and broader supplemental surface.
**Writer mode:** audit-only
**Auditor posture:** Balanced

---

## TL;DR

The v1.0.1 doc set is materially better than v1.0.0. The critical path errors from that release — MCP tool names, PDF location, `agentsuite founder resume` stale example, missing SECURITY.md — are all closed. What remains is a cluster of three items that the v1.0.1 closure pass already documented but did not fix: (1) a "six-stage pipeline" claim that persists in README, `docs/index.html`, and multiple community-launch drafts despite being corrected in CHANGELOG, (2) a stale 652-line `docs/USER-MANUAL.md` duplicate that predates v1.0 coverage of all seven agents, and (3) undocumented env vars (`AGENTSUITE_LLM_MAX_ATTEMPTS`, `AGENTSUITE_LLM_TIMEOUT_SECS`) that shipped in v1.0.1 but appear in no user-facing reference. A new finding in this pass: `README.md` MCP configuration blocks use `trust-risk` (hyphenated) in `AGENTSUITE_ENABLED_AGENTS`, which the registry tolerates via normalization but which contradicts the `trust_risk` (underscore) form documented everywhere else. First-time users copying the MCP config block may get unexpected behavior if the normalization path is not exercised.

A new user following the README will succeed at CLI installation and the Founder quick-start. They will not succeed at enabling all agents via MCP config copy-paste if the `trust-risk`/`trust_risk` inconsistency bites them. The six-stage claim in the README "Why AgentSuite" paragraph is the most-read accuracy error remaining — it contradicts the architecture diagram 200 lines later in the same file.

---

## Severity roll-up (documentation)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 2 |
| Major | 3 |
| Minor | 3 |
| Nit | 2 |
| **Total** | **10** |

---

## What's working

- **CHANGELOG v1.0.1 entry is honest and well-structured.** It explicitly states "5 of 5 Blockers, 9 of 16 Criticals, 6 of 27 Majors" — not "all issues fixed." Every bullet ties back to a finding ID. The lead paragraph is accurate. This is the standard other projects should follow.
- **Seven ADRs remain clean and current.** Short-form MADR, real content, linked from CONTRIBUTING with a workflow for new contributors. ADR-0004 (MCP tool naming) is directly useful to anyone reading the CHANGELOG and wondering why tool names changed.
- **`docs/troubleshooting.md`** explicitly calls out `trust_risk` (underscored) and warns that hyphenated is a common mistake. Exactly the right information in the right place.
- **SECURITY.md** (new in v1.0.1) covers a real disclosure SLA (5/10 days), GitHub Security Advisories channel, in/out-of-scope examples, and supply-chain hygiene reference. Not boilerplate.
- **Root `USER-MANUAL.md`** (984 lines) walks all seven agents end-to-end with Windows/Mac/Linux command variants, a full configuration reference, a glossary of 40+ terms, and a per-agent error table. The plain-language tone is sustained throughout — a genuine non-technical user could follow it.
- **`docs/test-coverage.md`** is transparent about its conditional `skipif` and explains precisely why it is not a Hard Rule 4a violation. Most projects don't bother to write this; this one does.
- **`docs/rubric-audit.md` cross-reference table** is the kind of artifact that pays for itself over time: it turns the ADR from an assertion into a documented position.
- **`docs/index.html`** Lighthouse scores (96/100/100/100) are honest, and the sample artifacts section now carries the correct "mock-LLM scaffold" qualifier added in v1.0.1. That was the right fix.
- **`CONTRIBUTING.md` "Adding a new agent"** — seven numbered steps with real file paths. A contributor could follow this without reading any other doc.

---

## What couldn't be assessed

- **`README-FULL.pdf`** (binary at `docs/README-FULL.pdf`, 33 KB) — content and diagram currency not assessable without rendering.
- **GitHub Discussions board** — `docs/community/discussions-seeds.md` notes that Discussions must be enabled manually. Whether it has been enabled post-v1.0.0 is not visible from the local clone. If it has been enabled, the seeded posts may carry the six-stage error.
- **GitHub release page copy and SBOM attachment** — not visible from local clone.
- **`docs/README-FULL.pdf` script discrepancy** — `scripts/generate_readme_pdf.py` writes to repo root; `scripts/build-pdf.sh` writes to `docs/`. The `docs/` copy is the one referenced. The correctness of the root-located script output was not tested.

---

## Doc asset inventory

| Asset | Exists? | Status | Finding(s) |
|---|---|---|---|
| README.md | Yes | Adequate; six-stage claim and trust-risk naming inconsistency | DOC-201, DOC-204 |
| CHANGELOG.md | Yes | Strong; one residual "six stages" line in v1.0.0 block (DOC-101, carried) | DOC-101 (carried from v1.0.1 audit) |
| CONTRIBUTING.md | Yes | Strong; test count (688/691) differs from test-coverage.md (689/692) | DOC-205 |
| LICENSE | Yes | Strong (MIT) | none |
| .gitignore | Yes | Present | not reviewed in depth |
| docs/index.html | Yes | Adequate; six-stage claim in "What it does" body; stale roadmap card | DOC-201, DOC-203 |
| README-FULL.pdf | Yes (docs/) | Binary; not assessable | — |
| USER-MANUAL.md (root, 984 lines) | Yes | Strong; missing --quiet flag and retry env vars | DOC-206 |
| docs/USER-MANUAL.md (652 lines) | Yes | Stale duplicate; predates v1.0 (covers only Founder + partial set); stale v0.2+ ref | DOC-202 |
| docs/troubleshooting.md | Yes | Strong; correctly flags trust_risk underscored form | none |
| docs/test-coverage.md | Yes | Adequate; test count 689/692 differs from CONTRIBUTING (688/691) | DOC-205 |
| docs/rubric-audit.md | Yes | Strong | none |
| docs/adr/ (7 ADRs + README) | Yes | Strong | none |
| SECURITY.md | Yes | Strong | none |
| docs/community/discussions-seeds.md | Yes | Six-stage claim persists in seeded post text | DOC-201 |
| docs/community/launch-posts.md | Yes | Six-stage claim in all three launch posts | DOC-201 |
| docs/community/good-first-issues.md | Yes | Strong | none |

---

## Persona walk-through

### First-time user

Lands on GitHub. Reads "AgentSuite" header, "Seven role-specific reasoning agents," and the "Why AgentSuite" paragraph. That paragraph says "six-stage pipeline (intake → extract → spec → execute → qa → approval)" — wrong. They proceed anyway. The install command is correct and the Founder quick-start works. If they attempt the MCP Codex quick-start and copy the `AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust-risk,cio"` block from the TOML example on README line 93, they will send `trust-risk` (hyphenated) to the registry. The registry normalizes it, so the agent loads — this actually works. But it's inconsistent with what `agentsuite agents` reports (`trust_risk`, underscored), confusing on first encounter. The six-stage count in the "Why AgentSuite" paragraph is the highest-visibility accuracy error for this persona.

### Returning user

Looking for the `--quiet` flag added in v1.0.1. It appears in CHANGELOG but is not in README's configuration table, and neither USER-MANUAL file documents it. Same for `AGENTSUITE_LLM_MAX_ATTEMPTS` and `AGENTSUITE_LLM_TIMEOUT_SECS`. A returning user who wants to tune retry behavior has to read the source code (or the CHANGELOG). This is a friction point, not a blocker.

A returning user who finds `docs/USER-MANUAL.md` instead of the root `USER-MANUAL.md` gets a 652-line doc covering only Founder, Product, and a few others at earlier version coverage. They see "Design, Marketing, etc., as those ship in v0.2+" — an actively misleading statement at v1.0.1 where all seven agents are shipped.

### New team member

Can find CONTRIBUTING and follow the "Adding a new agent" recipe. ADRs give real context. The test-count discrepancy between CONTRIBUTING (688/691) and test-coverage.md (689/692) is minor friction — the team member will run `pytest` and see the actual count rather than one of the two conflicting documented counts. The `docs/adr/` set tells them why decisions were made without requiring them to read git history. Architecture is adequately covered in the README Mermaid diagram and the text-art component diagram.

---

## Findings

> **Finding ID prefix:** `DOC-`
> **Categories:** Accuracy / Completeness / Onboarding / Architecture / API / FAQ / Marketing / Tone / Hygiene

---

### [DOC-201] — Critical — Accuracy — "Six-stage pipeline" claim persists in README, index.html, and launch posts despite CHANGELOG fix

**Evidence**

The v1.0.1 CHANGELOG entry correctly describes the pipeline as "five stages plus a kernel-managed approval transition." This language was also fixed in CHANGELOG's rc1 block. However, the same error was not swept from the other docs and community copy:

- `README.md:15` — "Why AgentSuite" paragraph: `"seven role-specific agents that each walk a deterministic six-stage pipeline (intake → extract → spec → execute → qa → approval)"`
- `docs/index.html:55` — "What it does" body: `"Each agent walks a six-stage pipeline (intake → extract → spec → execute → qa → approval)"`
- `docs/community/discussions-seeds.md:15` — Welcome/Launch seeded post: `"Each agent walks a deterministic six-stage pipeline (intake → extract → spec → execute → qa → approval)"`
- `docs/community/launch-posts.md:44` and `:79` — two additional launch post drafts with identical error

The CHANGELOG v1.0.0 block at line 123 was already flagged as DOC-101 in the v1.0.1 closure pass. This finding covers the additional surfaces missed in that pass.

**Why this matters**

`README.md:15` is the most-read paragraph in the repository — it's what a developer skims in the first 10 seconds. It claims six stages; the architecture diagram 200 lines later (README lines 223–231) correctly shows five. The same reader sees contradictory information in one scroll. A developer building an MCP integration who reads "intake → extract → spec → execute → qa → approval" as the stage list may attempt to wire an `approval` stage handler, find no such hook in `BaseAgent`, and either file a bug or move on. The launch-post drafts compound this: if they are posted to HN, Reddit, or Discord without review, the error amplifies to a wider audience.

**Blast radius**
- Adjacent docs: `CHANGELOG.md:123` (DOC-101, carried), `docs/community/discussions-seeds.md:15`, `docs/community/launch-posts.md:44,79` — all carry the same wrong string.
- Shared state: the `PIPELINE_ORDER` constant in source code is the authoritative count. Any grep-based drift trap would catch future regressions.
- User-facing: first-time users reading the README hero section; any developer building against the pipeline contract.
- Migration: none — this is a pure doc correction, no code change.
- Tests to update: DOC-103 (from v1.0.1 audit) proposed a 5-line pytest for `CHANGELOG.md`. Extend it to cover `README.md` and `docs/index.html` as well.
- Related findings: DOC-101 (CHANGELOG six-stages line, v1.0.1 audit — still open), DOC-103 (drift-trap proposal).

**Fix path**

In `README.md:15`, replace `"six-stage pipeline (intake → extract → spec → execute → qa → approval)"` with `"five-stage pipeline (intake → extract → spec → execute → qa) plus a kernel-managed approval transition"`.

In `docs/index.html:55`, same replacement: `"Each agent walks a five-stage pipeline (intake → extract → spec → execute → qa) plus a kernel-managed approval step"`.

In `docs/community/discussions-seeds.md:15` and `docs/community/launch-posts.md:44,79`: same correction. These are draft posts; fix before posting. A `grep -r "six-stage" .` confirms no remaining instances after the sweep.

---

### [DOC-202] — Critical — Completeness / Accuracy — `docs/USER-MANUAL.md` is a stale 652-line duplicate covering only Founder + partial agent set

**Evidence**

- `docs/USER-MANUAL.md` — 652 lines. The "Iterating" section on line 139 says: `"…can be used by other AgentSuite agents (Design, Marketing, etc., as those ship in v0.2+)"`. At v1.0.1, all seven agents ship. This sentence is materially wrong — it tells a reader that Design and Marketing are not yet available.
- `docs/USER-MANUAL.md` is linked from `docs/index.html:127`, README line 277, and the root `USER-MANUAL.md` footer. A user who clicks the link in the GitHub Pages landing page (`docs/index.html`) is sent to this stale file.
- `USER-MANUAL.md` at repo root — 984 lines. Covers all seven agents with per-agent CLI sections, approve commands, and error tables. Version "0.9.1" banner is gone from the root copy (it was removed during the v1.0.1 pass).

**Why this matters**

The most visible link from the public landing page (`docs/index.html`) leads to the shorter, stale document. A first-time user clicking "USER-MANUAL.md" from the landing page arrives at a doc that says agents 2–7 are not yet available. This is an accuracy failure on the project's primary onboarding surface. The returning-user persona who discovers the docs/ version instead of the root version gets actively wrong guidance.

The `docs/index.html` and README link both point to `docs/USER-MANUAL.md`, not to the root. So the file the links resolve to is the stale one.

**Blast radius**
- Adjacent docs: `docs/index.html:127` links to `docs/USER-MANUAL.md`. `README.md:277` links to `docs/USER-MANUAL.md`. Both send users to the wrong file.
- User-facing: every first-time user who clicks the "USER-MANUAL" link from landing page or README.
- Migration: none — fix is either deletion + redirect or sync. Recommend deletion and updating the two links to point to the root `USER-MANUAL.md` (via GitHub blob URL pattern: `https://github.com/scottconverse/AgentSuite/blob/main/USER-MANUAL.md`).
- Tests to update: add a CI grep that asserts `docs/USER-MANUAL.md` does not exist (if deleted), or that it does not contain "v0.2+".
- Related findings: DOC-007 (v1.0.0 audit, unclosed). This is the same finding; severity stays Major in the previous report — upgrading to Critical here because the landing-page link makes it active-path.

**Fix path**

**Option A (recommended):** Delete `docs/USER-MANUAL.md`. Update `docs/index.html:127` and `README.md:277` to link to the root file. On GitHub, the raw link would be:
```
https://github.com/scottconverse/AgentSuite/blob/main/USER-MANUAL.md
```

**Option B:** Replace the contents of `docs/USER-MANUAL.md` with a redirect notice:
```markdown
# AgentSuite User Manual

This file has moved. The current user manual is at the repo root:
[USER-MANUAL.md](../USER-MANUAL.md)
```

---

### [DOC-203] — Major — Accuracy — `docs/index.html` roadmap card says "v0.8 Next Agent — Coming soon"

**Evidence**

`docs/index.html:120-121`:
```html
<div class="card"><h3>v0.8 Next Agent</h3><p>Coming soon.</p></div>
```

At v1.0.1, v0.8.x is shipped and the project is at v1.0.1. The roadmap section shows a single "v0.8 Next Agent — Coming soon" card that is multiple versions stale. The CHANGELOG's `[Unreleased]` roadmap is current (v1.0.2 CR-01 regeneration, v1.1.x candidates), but the landing page does not reflect it.

**Why this matters**

The landing page roadmap gives a new visitor the impression the project is at an early stage. A potential user seeing "v0.8 next agent" on a product labeled v1.0.1 in the header will assume the roadmap section is stale and lose trust in the site's currency. This is also the first doc a new visitor sees — it shapes their initial confidence.

**Blast radius**
- Adjacent docs: `README.md:272–273` also says `"v0.8.0 — next agent"` in its Roadmap section — the same stale content in the main readme.
- User-facing: all new visitors to the GitHub Pages site.
- Migration: none.
- Tests to update: extend the `docs-drift` CI job (from v0.8.1) to assert the landing page version badge matches `pyproject.toml`.
- Related findings: README roadmap section carries the same error (linked to DOC-203 for the fix sweep).

**Fix path**

Replace the `<div class="grid">` roadmap block in `docs/index.html` (lines 119–121) with current roadmap content from CHANGELOG `[Unreleased]`:
```html
<h2>Roadmap</h2>
<div class="grid">
  <div class="card"><h3>v1.0.2</h3><p>Real-LLM regen of sample-output/founder/ bodies (closes CR-01). Cassette tier (W-01).</p></div>
  <div class="card"><h3>v1.1.x</h3><p>8th agent, per-day cost cap, GPG signed tags (community vote).</p></div>
</div>
```

Also update `README.md:272–273` roadmap from "v0.8.0 — next agent" to current candidates.

**Blast radius**
- Adjacent code: `README.md:272-273` — same stale roadmap content.
- User-facing: first-time visitors assessing project maturity.
- Migration: none.
- Related findings: DOC-201 (index.html accuracy pass).

---

### [DOC-204] — Major — Accuracy — README MCP config blocks use `trust-risk` (hyphenated) in `AGENTSUITE_ENABLED_AGENTS`; correct form is `trust_risk` (underscore)

**Evidence**

`README.md:93` (Codex MCP TOML block):
```
AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust-risk,cio"
```

`README.md:108` (Claude Code / Cowork JSON block):
```json
"env": {"AGENTSUITE_ENABLED_AGENTS": "founder,design,product,engineering,marketing,trust-risk,cio"}
```

These are the two copy-paste blocks a new user follows to wire up MCP. They both use `trust-risk` (hyphenated).

The authoritative registered name is `trust_risk` (underscore, per `agentsuite/agents/registry.py:79` and `agentsuite/agents/trust_risk/agent.py:28`). The registry's `enabled_names()` normalizes hyphens to underscores (line 44), so `trust-risk` in `AGENTSUITE_ENABLED_AGENTS` does resolve correctly. However:

1. `docs/troubleshooting.md:67–71` explicitly warns: `"Note that trust_risk uses an underscore, not a hyphen. This is a common mistake."` — directly contradicted by the README copy-paste blocks.
2. `agentsuite agents` reports `"all_registered": ["...", "trust_risk", "..."]` with underscores. A user who copies the hyphenated form from README and then runs `agentsuite agents` sees a different form than what they typed, which is confusing.
3. Every other doc that lists the env var (`USER-MANUAL.md`, `docs/troubleshooting.md`, `docs/index.html`) uses the underscore form.

**Why this matters**

The README MCP config blocks are the highest-traffic copy-paste surface in the repo. Copy-pasting `trust-risk` and then seeing `trust_risk` in `agentsuite agents` output creates unnecessary confusion. The troubleshooting guide's "this is a common mistake" note becomes actively ironic when the README models the mistake. If normalization were removed in a future refactor, the copied configs would break silently.

**Blast radius**
- Adjacent docs: `README.md:93` and `README.md:108` are the only two instances of the hyphenated form in user-facing docs. All others correctly use underscore.
- Shared state: `agentsuite/agents/registry.py:44` normalization code. If that line is ever removed, all users who copied the hyphenated form will experience `UnknownAgent` errors.
- User-facing: all users who follow the MCP quick-start in README.
- Migration: none required for the fix (pure doc correction). If normalization is ever removed, this doc fix becomes critical for existing users.
- Tests to update: `tests/test_mcp_tool_names_documented.py` covers tool names; a separate assertion that `AGENTSUITE_ENABLED_AGENTS` examples in the README use underscore form would close this class.
- Related findings: none.

**Fix path**

In `README.md:93` and `README.md:108`, replace `trust-risk` with `trust_risk` in both MCP config blocks.

---

### [DOC-205] — Major — Accuracy — Test count in CONTRIBUTING.md (688/691) contradicts test-coverage.md (689/692)

**Evidence**

`CONTRIBUTING.md:78`:
> "The default `pytest` invocation runs **688 of 691** tests; the three deselected tests (cleanroom, live, live_ollama) are gated by markers…"

`docs/test-coverage.md:19`:
> "…that leaves **689 of 692** tests in the default run, with **0 skipped**"

CHANGELOG v1.0.1 states "Net +93 tests vs v1.0.0 (689 -> 782 passing in the default invocation)." The CHANGELOG implies 782 is the current default count, which matches neither CONTRIBUTING nor test-coverage.md.

**Why this matters**

A new team member who runs `pytest` and sees 782 tests (post-v1.0.1) will see the CONTRIBUTING count of 688/691 and the test-coverage count of 689/692 both appear wrong. The discrepancy sends a signal that the documentation is not maintained. More practically, if a team member accidentally breaks a marker gate, the documented count won't match and they may not notice the regression.

**Blast radius**
- Adjacent docs: three docs carry three different counts (688, 689, 782). The CHANGELOG count (782) is the post-v1.0.1 number and is probably the most accurate; the other two predated v1.0.1 and were not updated.
- User-facing: new contributors running `pytest` for the first time.
- Migration: none.
- Tests to update: none — this is a doc-update task. Recommend adding the test-count refresh to the pre-push checklist.
- Related findings: none.

**Fix path**

Run `pytest --collect-only -q` to get the authoritative current count. Update both CONTRIBUTING.md line 78 and docs/test-coverage.md line 19 to match. Consider adding a comment in CONTRIBUTING that the count is updated on each release.

---

### [DOC-206] — Minor — Completeness — v1.0.1 env vars and `--quiet` flag missing from README config table and USER-MANUAL

**Evidence**

v1.0.1 Added:
- `--quiet` / `-q` flag on all agent `run` commands (silences per-stage progress emitter)
- `AGENTSUITE_LLM_MAX_ATTEMPTS` env var (default 3; from `agentsuite/llm/retry.py:76`)
- `AGENTSUITE_LLM_TIMEOUT_SECS` env var (default 120s; from `agentsuite/llm/retry.py:77`)

`README.md:199–206` configuration table does not include these three. `USER-MANUAL.md:802–811` configuration table does not include them either. The CHANGELOG mentions `--quiet` in the v1.0.1 Added section (line 45) and `AGENTSUITE_LLM_MAX_ATTEMPTS` / `AGENTSUITE_LLM_TIMEOUT_SECS` in the v0.8.2 Changed section (line 318), but the docs tables were not updated.

**Why this matters**

A returning user who wants to silence progress output or tune retry behavior reads the README config table and finds neither option. They must grep the source or read the CHANGELOG to discover these. Low friction but real — especially `--quiet` which affects the standard CLI experience.

**Fix path**

Add to `README.md` configuration table:

| Env var | Default | Purpose |
|---|---|---|
| `AGENTSUITE_LLM_MAX_ATTEMPTS` | `3` | Max LLM call attempts per stage (includes first try) |
| `AGENTSUITE_LLM_TIMEOUT_SECS` | `120.0` | Wall-clock seconds budget across all retry attempts |

Add `--quiet` / `-q` to the quick-start CLI example note and to the configuration reference in `USER-MANUAL.md`.

---

### [DOC-207] — Minor — Accuracy — `docs/USER-MANUAL.md:139` says Design + Marketing agents "ship in v0.2+"

**Evidence**

`docs/USER-MANUAL.md:139`:
> "This copies the approved artifacts to `.agentsuite/_kernel/my-product/` where they live permanently and can be used by other AgentSuite agents (Design, Marketing, etc., as those ship in v0.2+)."

At v1.0.1, Design shipped at v0.2.0 and Marketing at v0.5.0. The statement implies these agents are future/unreleased.

This finding is absorbed by DOC-202 (delete or replace `docs/USER-MANUAL.md`), but is called out separately because the text is actively misleading — not just stale — and would warrant a fix even in an otherwise adequate document.

**Fix path**

Resolved by DOC-202. If Option B (redirect file) is chosen, this line does not need separate treatment. If the file is synced rather than deleted, remove this sentence.

---

### [DOC-208] — Minor — Completeness — README Status section repeats v0.x version history rather than linking CHANGELOG

**Evidence**

`README.md:261–273` — "Status" section lists v0.1.0 through v0.7.0 in detail as "Shipped," then says:

```
**Roadmap:**
- v0.8.0 — next agent
```

At v1.0.1, listing v0.1.0 through v0.7.0 as the shipped surface is accurate history but gives no signal about the current version (v1.0.1). A reader scanning this section would think the project is at v0.7 / v0.8.

There is no mention of v0.8.0 through v1.0.1 in this section — these versions are only accessible in the CHANGELOG. The README hero (line 5) correctly says "v1.0.1" but the Status section contradicts it.

**Why this matters**

Minor because the version badge at the top of the README is correct. But a reader who scrolls to "Status" for a quick project-state check sees v0.7 as the last shipped version. It sends a confusing signal about maturity.

**Fix path**

Replace the detailed version-by-version bullet list with a one-line current-state summary and a CHANGELOG link:
```markdown
## Status

v1.0.1 — General availability. Seven agents shipped. Full release history: [CHANGELOG.md](CHANGELOG.md).
```

---

### [DOC-209] — Nit — Tone — `docs/USER-MANUAL.md` Iterating section links into `dev-reports/` (internal path)

**Evidence**

`docs/USER-MANUAL.md:145`:
> "Re-running the QA stage from the CLI is on the v1.0.x roadmap (see `dev-reports/audit-AgentSuite-2026-04-29/next-sprint-watchlist.md` W-09)"

This is an internal dev-report path, not a public docs path. A user reading this at `docs/USER-MANUAL.md` cannot navigate to this path from GitHub Pages.

**Fix path**

Resolved by DOC-202 (delete `docs/USER-MANUAL.md`). If the file is retained, replace this internal reference with "tracked in GitHub Issues / next-sprint planning."

---

### [DOC-210] — Nit — Formatting — `docs/index.html` install block missing `[mcp]` extra

**Evidence**

`docs/index.html:58–61` install block:
```
pip install "agentsuite[anthropic] @ git+https://github.com/scottconverse/AgentSuite.git"
# other providers: [openai]  [gemini]  [ollama]  [all]
# or, no install:
uvx --from git+https://github.com/scottconverse/AgentSuite.git agentsuite-mcp
```

The comment lists four extras but omits `[mcp]`, which is a distinct extra documented in README and USER-MANUAL. The `uvx` no-install option does not explain that it requires `[mcp]`.

**Fix path**

Update the comment to: `# other providers: [openai]  [gemini]  [ollama]  [mcp]  [all]`. Minor; the `uvx` path works without specifying a separate extra because uvx handles it, but the inline comment is incomplete.

---

## Marketing / Honesty Audit

The v1.0.1 pass (UX-101 fix) removed overbroad "Your AI creative and product team" framing and added the mock-LLM scaffold qualifiers to the spec-artifact screenshots. The current `docs/index.html` copy is honest about the project's scope and limitations. No new overclaims were found in this pass.

The six-stage claim (DOC-201) is an accuracy error, not an overclaim — the actual pipeline is, if anything, more technically precise than "six stages." No feature is claimed that does not exist.

The community launch-post drafts (docs/community/launch-posts.md) are appropriately scoped and do not make unsubstantiated performance claims. The per-run cost estimates in discussions-seeds.md ($0.05–$0.40 range by provider) are consistent with the CHANGELOG pricing notes and appear honest.

---

## Patterns and Systemic Observations

**The six-stage claim is a copy-paste propagation pattern.** The same phrase appears word-for-word in README, index.html, discussions-seeds.md, and launch-posts.md. This is the classic copy-paste propagation: a paragraph written once got pasted into four surfaces, then one surface got corrected (CHANGELOG) without sweeping the others. The DOC-103 drift-trap proposal (from the v1.0.1 audit) is the right structural fix — a grep-based CI assertion would make this class impossible to re-introduce.

**Config table staleness pattern.** Both README and USER-MANUAL config tables were not updated when v1.0.1 added `--quiet` and the retry env vars. This suggests the "update config table when shipping a flag" step is not in the release checklist. Consider adding it to `scripts/verify-release.sh` as a note or lint check.

**Two-file USER-MANUAL pattern.** The root `USER-MANUAL.md` and `docs/USER-MANUAL.md` are functionally the same document at different vintages. The landing page links to the docs/ version, which is the stale one. This pattern is a trap: whoever writes or updates the root file naturally forgets the docs/ copy. Deletion is cleaner than sync discipline.

**Roadmap sections drift.** The `README.md` Status/Roadmap and `docs/index.html` Roadmap card were not updated past v0.7/v0.8. The CHANGELOG `[Unreleased]` section is the project's actual living roadmap, but it's not linked from either doc's roadmap section. A one-line link from both would close this permanently.

---

## Drafts produced

Writer mode is audit-only; no drafts produced in this pass.

---

## Appendix: Docs reviewed

- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\README.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\CHANGELOG.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\CONTRIBUTING.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\USER-MANUAL.md` (root, 984 lines)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\SECURITY.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\LICENSE`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\USER-MANUAL.md` (652 lines)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\index.html`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\troubleshooting.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\test-coverage.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\rubric-audit.md` (referenced; not re-read in full)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\adr\README.md` (index + confirmed status)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\community\discussions-seeds.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\community\launch-posts.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\docs\community\good-first-issues.md`
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\dev-reports\audit-AgentSuite-2026-04-29-v101\03-documentation-deepdive.md` (closure-pass audit for carry-over finding status)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\agentsuite\agents\registry.py` (trust-risk name normalization)
- `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\agentsuite\llm\retry.py` (env var names for DOC-206)
