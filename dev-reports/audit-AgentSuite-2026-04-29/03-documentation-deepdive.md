# Documentation Deep-Dive — AgentSuite v1.0.0

**Audit date:** 2026-04-29
**Role:** Technical Writer
**Scope audited:** README.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, USER-MANUAL.md (root + docs/), docs/index.html, docs/troubleshooting.md, docs/test-coverage.md, docs/rubric-audit.md, docs/lighthouse-rc1.md, all 7 ADRs, docs/community/*, docs/press-kit/README.md, examples/sample-output/founder/README.md, examples/patentforgelocal/README.md, agentsuite/__init__.py, agentsuite/kernel/schema.py.
**Writer mode:** audit+draft (one Critical replacement produced in `doc-rewrites/`)
**Auditor posture:** Adversarial

---

## TL;DR

The doc set is broad and shows real care — seven ADRs, a press kit, launch-posts file, 650-line USER-MANUAL, three rubric/coverage cross-references, sample output committed for browsing without install. But the load-bearing public-contract claims in CHANGELOG, README, and the launch copy are wrong on two specific facts: **the pipeline is 5 stages, not 6**, and **MCP tools are named `agentsuite_<agent>_<verb>`, not `<agent>_<verb>`**. Both errors propagate into the press kit, the HN/Reddit/Discord launch drafts, and the GitHub Discussions seeds. Several smaller accuracy errors compound the trust risk: test-count drift across CONTRIBUTING / test-coverage / press-kit, a `Development Status :: 3 - Alpha` classifier on a v1.0.0 GA wheel, a wheel-size claim off by 1.7×, two diverging USER-MANUAL files, and a `docs/test-coverage.md` page that contradicts itself within 50 lines about whether `@pytest.mark.skipif` is used. **Fix the compatibility-freeze block first** (drop-in replacement provided in `doc-rewrites/compatibility-freeze.md`); everything else can land in a doc-only patch release.


## Severity roll-up (documentation)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 3 |
| Major | 8 |
| Minor | 6 |
| Nit | 2 |
| **Total** | **19** |

## What's working

- **ADR set is genuinely good.** Seven concise, well-formatted ADRs covering rubric design (0001), RunState (0002), retry policy (0003), MCP naming (0004), cost split (0005), no-PyPI choice (0006), and resume idempotency (0007). The MADR-shortened format is consistent. ADR-0001 even ships a self-correcting "2026-04-28 update" note rather than rewriting history.
- **`docs/rubric-audit.md` cross-reference table** is exactly the kind of artifact most projects don't bother to write. Turns ADR-0001 from an opinion into a defended position.
- **`examples/sample-output/founder/`** committed to the repo is a great onboarding hack — reviewers can see real output without installing, and `TREE.txt` lets them grep without cloning.
- **`docs/troubleshooting.md`** covers the 5 most likely failure modes with Windows + Mac/Linux commands side by side. Tone is patient and actionable.
- **`docs/USER-MANUAL.md`** (the docs/ copy) is patiently written for non-technical readers and walks every agent end-to-end. The glossary is a thoughtful touch.
- **`CONTRIBUTING.md` "Adding a new agent" recipe** is concrete — seven numbered steps with file paths, not vague encouragement.
- **`docs/index.html`** earned its Lighthouse 96/100/100/100 score honestly; inline favicon, `<main>` landmark, robots.txt are all small details that show care.
- **`scripts/verify-release.sh` enumeration in CONTRIBUTING** ("8 checks: doc artifacts, version sync, CHANGELOG entry, lint, tests, cleanroom, build, secrets scan") makes the gate concrete.

## What couldn't be assessed

- **`README-FULL.pdf`** — binary blob; quality of architecture diagrams, currency vs. v1.0 surface, link-from-docs reachability not assessable without rendering.
- **GitHub Discussions board** — referenced as if enabled at launch but not yet enabled per `docs/community/discussions-seeds.md` line 3.
- **GitHub release page copy / SBOM artifact attached to the release** — not visible from local clone.


---

## Doc asset inventory

| Asset | Exists? | Status | Finding(s) |
|---|---|---|---|
| README.md | Yes | Adequate; factually wrong on stage count and MCP tool names | DOC-001, DOC-002, DOC-006, DOC-009 |
| CHANGELOG.md | Yes | Strong format; wrong on compat-freeze claims | DOC-001, DOC-002, DOC-008, DOC-016 |
| CONTRIBUTING.md | Yes | Strong, with one stale test count | DOC-005 |
| LICENSE | Yes | Strong (MIT, dated 2026) | none |
| .gitignore | Yes | Adequate | not reviewed in depth |
| docs/index.html | Yes | Solid landing; six-stage error + stale roadmap card + broken PDF link + 26-vs-14 artifact contradiction | DOC-001, DOC-006, DOC-012, DOC-013 |
| README-FULL.pdf | Yes (at repo root, not docs/) | Could not render | DOC-006 |
| USER-MANUAL.md | Yes — twice (root + docs/, divergent) | Confusing | DOC-007 |
| docs/troubleshooting.md | Yes | Strong | DOC-019 (nit) |
| docs/test-coverage.md | Yes | Self-contradicting on `@pytest.mark.skipif` | DOC-004 |
| docs/rubric-audit.md | Yes | Strong | none |
| docs/lighthouse-rc1.md | Yes | Strong | none |
| docs/adr/ (7 ADRs + README) | Yes | Strong | DOC-014 (minor narrative drift in 0001) |
| docs/community/discussions-seeds.md | Yes | Wrong stage count, wrong MCP tool names | DOC-001, DOC-002 |
| docs/community/good-first-issues.md | Yes | Strong | none |
| docs/community/launch-posts.md | Yes | Wrong stage count, wrong tool names, stale test count | DOC-001, DOC-002, DOC-005 |
| docs/press-kit/README.md | Yes | Wrong stage count, wrong wheel size, "Alpha" classifier | DOC-001, DOC-010, DOC-011 |
| examples/sample-output/founder/README.md | Yes | Wrong artifact counts (claims 7 spec + 8 templates; actual 9 spec + 11 templates) | DOC-003 |
| examples/patentforgelocal/README.md | Yes | Adequate (it's a fixture) | none |

---

## Persona walk-through

### First-time user

Lands on the GitHub README. Within 60 seconds reads "seven role-specific reasoning agents," "Python package and MCP server," install with `pip install "agentsuite[anthropic] @ git+..."`. The install path is unambiguous and the quick-start CLI command is concrete — they will succeed at install. Then they hit the MCP quick-start (line 96), restart Codex, and try to call `founder_run` — and the tool name is wrong. They will either guess the prefix, fall back to docs, or assume the install is broken. The latter is the trust-killer.

For non-technical users, the docs/USER-MANUAL.md is well-pitched. They will mostly succeed because it doesn't ask them to use the MCP surface at all. But the **root** USER-MANUAL.md says "Version 0.9.1" and uses a different layout, so a user who finds the wrong copy gets a stale doc.

### Returning user

Comes back to look up cost cap env var, run-id format, or how to add a new agent. Will succeed: troubleshooting.md, README's Configuration table, CONTRIBUTING's "Adding a new agent" recipe, and the ADR set are easy to navigate. Friction point: duplicated USER-MANUAL.md — a returning user might read either copy.

### New team member

Following CONTRIBUTING.md will succeed at setting up the dev env, running `pytest`, and understanding the test tiers. test-coverage.md will then confuse them: it says "the repo has zero `@pytest.mark.skipif`" while simultaneously documenting one. The seven ADRs combined are probably the best onboarding doc in the project. The "Adding a new agent" recipe is good. The blocker on adoption is more likely to be: which of the two USER-MANUAL.md files do I update when I touch a user-facing flag?


---

## Findings

### [DOC-001] — Critical — Accuracy — "Six-stage pipeline" is wrong; it's five

**Evidence**

`agentsuite/kernel/base_agent.py:20` defines:

```python
PIPELINE_ORDER: list[Stage] = ["intake", "extract", "spec", "execute", "qa"]
```

The base_agent.py module docstring (line 1) is correct: "Abstract base agent with persisted **five-stage** pipeline (intake, extract, spec, execute, qa) **with a separate approval gate**."

But the public docs say six:

- `README.md:15` — "deterministic six-stage pipeline (intake → extract → spec → execute → qa → approval)"
- `CHANGELOG.md:30` and `:54` — "six stages" under v1.0.0 + v1.0.0rc1 compat freezes
- `CHANGELOG.md:401` — same under v0.1.0
- `docs/index.html:55` — same in landing page
- `docs/community/launch-posts.md:44, :79` — r/LocalLLaMA + Show HN drafts
- `docs/community/discussions-seeds.md:15` — Welcome announcement
- `docs/press-kit/README.md:15, :21` — two-sentence + five-paragraph descriptions

README is itself internally inconsistent — `:51` says "five stages," `:221` says "five-stage pipeline," and the Mermaid diagram at `:223–232` correctly draws five stages.

`approval` is a kernel-managed gate after the pipeline loop completes, not a pipeline stage. Agents don't implement an `approval` handler — `base_agent._drive()` enters the gate after the QA stage when scores are below threshold. The `Stage` literal in `agentsuite/kernel/schema.py:24` includes seven values (`intake, extract, spec, execute, qa, approval, done`) for state-typing purposes; that does not make them all pipeline stages.

**Why this matters**

This is the load-bearing claim of the v1.0.0 compatibility freeze ("Stage names are part of the public contract"). A reader who notices loses trust in the rest of the freeze. Worse, anyone building against the documented "six stages" assumption (e.g., implementing an `approval` handler in a downstream agent) finds their code broken because `BaseAgent._drive()` doesn't call agent-level `approval` handlers.

**Blast radius**
- Adjacent code: 11 distinct doc locations carry "six-stage" wording. All need the same edit. The Mermaid diagram in README (correct) and the system-overview/founder-pipeline `.mmd` files in `docs/architecture/` should be cross-checked.
- Shared assumption: the v1.0.0 *compatibility contract*. Locking the wrong contract is worse than locking nothing.
- User-facing: HN / r/LocalLLaMA / Discord drafts will go out with the wrong claim if posted as written. Discussion seeds will be wrong from day one.
- Migration: none — code is correct.
- Tests to update: none — the test suite already pins the 5-stage `PIPELINE_ORDER`.
- Related findings: DOC-002, DOC-003, DOC-008.

**Fix path**

Drop in `doc-rewrites/compatibility-freeze.md` for the README compat block, both CHANGELOG compat blocks, and the index.html "What it does" paragraph. Sweep all 11 grep hits in one pass. Recommend a doc-only `1.0.1` patch release that calls out the correction explicitly.

---

### [DOC-002] — Critical — Accuracy — MCP tool names in compatibility freeze are wrong

**Evidence**

CHANGELOG `[1.0.0]` line 29 and `[1.0.0rc1]` line 53 both say:

> **MCP tool naming:** `<agent>_run`, `<agent>_resume`, `<agent>_approve` (per ADR-0004).

But the actual registrations in `agentsuite/agents/founder/mcp_tools.py:127–131` (and the analogous module for every other agent) are:

```python
server.add_tool("agentsuite_founder_run", founder_run)
server.add_tool("agentsuite_founder_resume", founder_resume)
server.add_tool("agentsuite_founder_approve", founder_approve)
server.add_tool("agentsuite_founder_get_status", founder_get_status)
server.add_tool("agentsuite_founder_list_runs", founder_list_runs)
```

ADR-0004 itself is correct: "All MCP tools are namespaced as `agentsuite_<agent>_<verb>`." CHANGELOG v0.8.2 documented the rename correctly. But the v1.0.0/rc1 compatibility-freeze blocks were written referencing the *pre-rename* pattern, freezing a contract that the code retired four versions ago.

The error propagates further:

- `README.md:96` — "Tools `founder_run`, `founder_approve`, `founder_get_status`, `founder_list_runs`, `founder_resume`, plus the cross-agent `agentsuite_list_agents`..."
- `docs/community/launch-posts.md:20` — "each agent is a `<agent>_run` / `<agent>_resume` / `<agent>_approve` triplet."

**Why this matters**

The compatibility freeze is the marketing and engineering contract of v1.0.0. Stating the wrong tool names locks the wrong contract: a reader copying from the freeze block into their MCP host config gets `founder_run`, restarts the host, and the tool doesn't exist. They debug for 20 minutes, find the right name in the source, and conclude the docs are unreliable.

**Blast radius**
- Adjacent code: README line 96, launch-posts.md line 20, both CHANGELOG compat sections. ADR-0004 is correct. `docs/architecture/mcp-flow.mmd:8` shows `founder_run(...)` in a sequence diagram — needs the prefix.
- Shared assumption: ADR-0004 is the source of truth; CHANGELOG/README must match it. Centralize the canonical tool-name table in CONTRIBUTING or ADR-0004 and link from CHANGELOG/README rather than restating.
- User-facing: every MCP host config example in the repo.
- Migration: none in code — the v0.8.2 rename already shipped clean.
- Tests to update: there's a test that the registered tool list contains the prefixed names (per CHANGELOG v0.8.2). No test changes needed.
- Related findings: DOC-001, DOC-009.

**Fix path**

Use `doc-rewrites/compatibility-freeze.md`. Replace CHANGELOG lines 29, 53; README line 96; launch-posts.md line 20.


---

### [DOC-003] — Critical — Accuracy — Sample-output README undercounts artifacts; "26 artifacts" claim is Founder-specific but used project-wide

**Evidence**

`examples/sample-output/founder/README.md:14–15`:

> - 7 founder spec artifacts (`brand-system.md`, `founder-voice-guide.md`, etc.).
> - `brief-template-library/` — 8 reusable brief templates for downstream agents.

On-disk reality (verified via `ls`):
- 9 spec markdown files: `brand-system.md`, `founder-voice-guide.md`, `product-positioning.md`, `audience-map.md`, `claims-and-proof-library.md`, `visual-style-guide.md`, `campaign-production-workflow.md`, `asset-qa-checklist.md`, `reusable-prompt-library.md`.
- 11 brief templates in `brief-template-library/`.

Compounding error: README, CHANGELOG, press-kit, launch-posts, and discussions-seeds all repeat "**persists 26 artifacts**" as a project-wide claim. But 26 is the **Founder count only**. Other agents produce 17 (Engineering, Trust/Risk, CIO per their respective tables) or unspecified counts (Design, Product). Readers will think every agent produces 26.

`docs/index.html:73` makes a third claim: "the full output of a real run — **14 artifacts**, no install required." Same sample-output directory, three different counts (14 / 26 / 7+8=15) depending on doc.

**Why this matters**

A claim like "26 artifacts per run" is a headline number that lands in posts, podcasts, and HN comments. If a reader counts the actual files in `examples/sample-output/founder/` and finds 29 entries, or 9 spec markdowns, or 17 if they pick a different agent, they conclude the marketing copy is sloppy. Sample-output README undercounts the *exact* directory it describes.

**Blast radius**
- Adjacent code: every doc with "26 artifacts" — README, CHANGELOG, press-kit, launch-posts, discussions-seeds, index.html (which says 14). At least 7 hits.
- User-facing: every reader of the sample-output README.
- Migration: none.
- Related findings: DOC-001, DOC-013.

**Fix path**

Two-step:
1. Update `examples/sample-output/founder/README.md` to "9 founder spec artifacts" and "11 reusable brief templates," and quote the *actual* artifact total. Pick one definition and use it consistently.
2. Across the rest of the docs, change "26 artifacts" to either (a) "26 artifacts per Founder run; 17 per Engineering / Trust-Risk / CIO; varies per agent" or (b) drop the headline number. Option (b) is cleaner.

---

### [DOC-004] — Major — Accuracy — `docs/test-coverage.md` self-contradicts on `@pytest.mark.skipif`

**Evidence**

Line 5: "there are zero `pytest.skip()` calls and zero `@pytest.mark.skip` (unconditional) markers in the repo. ... one additional test uses a conditional `@pytest.mark.skipif`..."

Line 53–54: "**The repo has zero `@pytest.mark.skipif`.**"

Both can't be true. Actual count via grep on `tests/`:
- `tests/integration/test_founder_pipeline.py:16` — skipif (the one acknowledged on line 38–42)
- `tests/integration/test_design_pipeline.py:17`
- `tests/integration/test_cio_pipeline.py:18, :42, :78`
- `tests/integration/test_engineering_pipeline.py:17`
- (Same pattern in marketing, product, trust_risk integration tests)

Repo has at least **7 `@pytest.mark.skipif` markers**, not zero. The audit-honesty pass that CHANGELOG 1.0.0rc1 mentions ("Documented the existing conditional `@pytest.mark.skipif` in `test_founder_pipeline.py`") missed the parallel skipifs in the other six integration tests.

**Why this matters**

Credibility issue for the test discipline pitch. Press-kit, CHANGELOG, launch-posts, and CONTRIBUTING all advertise "Hard Rule 4a satisfied — no skipped tests." Press-kit specifically says "**0 skipped**" (line 46). A reader who checks the source finds seven skipifs.

**Blast radius**
- Adjacent code: launch-posts "0 skipped," press-kit "0 skipped," README implicit via Hard Rule 4a reference.
- Shared assumption: the audit-honesty pass was complete. It wasn't.
- Migration: none.
- Tests to update: none — skipifs are intentional and documented (just not all of them).
- Related findings: DOC-005.

**Fix path**

Rewrite `docs/test-coverage.md` lines 53–54: change "**The repo has zero `@pytest.mark.skipif`.**" to "**The repo has 7+ `@pytest.mark.skipif` markers, all conditional gates between mock-vs-record or live-vs-mock paths. None unconditionally skip.**" Then enumerate each marker. Sweep all marketing copy that says "0 skipped" to clarify that "skipped" means *unconditionally skipped via `pytest.skip()` or `@pytest.mark.skip`*.

---

### [DOC-005] — Major — Accuracy — Test count claim drifts across 5+ docs

**Evidence**

- `CONTRIBUTING.md:78` — "688 of 691"
- `docs/test-coverage.md:19` — "689 of 692"
- `CHANGELOG.md:45` (v1.0.0rc1) — "689 of 692"
- `docs/press-kit/README.md:46` — "689"
- `docs/community/launch-posts.md:55, :89` — "689 tests"

CONTRIBUTING is one off. Either someone added 3 tests after CONTRIBUTING was last touched, or CONTRIBUTING was never updated.

**Why this matters**

A new contributor reads CONTRIBUTING, runs `pytest`, gets 689 — not 688. Anyone fact-checking the press kit's "689" against CONTRIBUTING's "688" sees an inconsistency in 30 seconds.

**Blast radius**
- 5+ doc locations.
- Fix path: Drop the absolute count and say "~690 tests" everywhere, or automate via a script that runs `pytest --collect-only -q` and substitutes at release time. Sweep all five locations in one edit.

---

### [DOC-006] — Major — Accuracy / Hygiene — Broken link to README-FULL.pdf

**Evidence**

- `README.md:259` — "see `docs/README-FULL.pdf`"
- `README.md:278` — `[README-FULL.pdf](docs/README-FULL.pdf)`
- `docs/index.html:126` — `<a href="...docs/README-FULL.pdf">README-FULL.pdf</a>`

Actual location: `README-FULL.pdf` at the **repo root**, not under `docs/`. Verified `docs/README-FULL.pdf` does NOT exist.

**Why this matters**

Three public links to the deep-dive doc all 404 on GitHub. This is the single doc README pitches for "full architecture diagram with all agents."

**Blast radius**
- 3 link sites.
- Fix path: Move `README-FULL.pdf` into `docs/` or update the three links. Recommend moving so the linked location matches convention.


---

### [DOC-007] — Major — Hygiene — Two USER-MANUAL.md files diverge

**Evidence**

```
/AgentSuite/USER-MANUAL.md         ← header says "Version 0.9.1"
/AgentSuite/docs/USER-MANUAL.md    ← no version stamp; different layout
```

`diff` shows substantial divergence from line 3 onward. README links to `docs/USER-MANUAL.md` (line 277). The root copy is referenced from `docs/troubleshooting.md:207` ("`USER-MANUAL.md` (or the `docs/` folder)") implying *either* is canonical.

**Why this matters**

A reader updating user-facing docs has to guess which copy is canonical. Updating one and not the other widens the divergence. The root copy carrying "Version 0.9.1" three days after a v1.0.0 GA tag is a credibility hit.

**Blast radius**
- 2 files diverge.
- Migration: pick one, delete the other, fix the troubleshooting reference.
- Related findings: DOC-016.

**Fix path**

Delete `USER-MANUAL.md` at the repo root. Update `docs/troubleshooting.md:207` to reference `docs/USER-MANUAL.md` only. Add `**Version 1.0.0**` to the docs header.

---

### [DOC-008] — Major — Accuracy — CHANGELOG mixes "five-stage" and "six-stage" within itself

**Evidence**

CHANGELOG hits via grep:
- v0.1.0 (line 401): "**six-stage pipeline** (intake → extract → spec → execute → qa → approval)"
- v0.3.0 (line 358): "**five-stage pipeline**"
- v0.4.0 through v0.7.0 (lines 348, 338, 320, 302): all "**5-stage pipeline** (intake → extract → spec → execute → qa)"
- v1.0.0 + 1.0.0rc1 (lines 30, 54): "**six stages**"

Same code described as 5-stage in v0.3 through v0.7, then 6-stage in v1.0. Nothing in code changed between v0.7 and v1.0 to justify the rename.

**Why this matters**

A reader walking the CHANGELOG history sees a stage count that randomly flips. Combined with DOC-001, this looks like the freeze copy was written without re-reading prior entries.

**Blast radius**
- 2 directly contradictory sections within CHANGELOG.
- Fix path: Use `doc-rewrites/compatibility-freeze.md`. Optionally edit v0.1.0 entry to match the 5-stage convention.

---

### [DOC-009] — Major — Accuracy — README MCP example uses outdated tool names

**Evidence**

`README.md:96`:

> Restart Codex. Tools `founder_run`, `founder_approve`, `founder_get_status`, `founder_list_runs`, `founder_resume`, plus the cross-agent `agentsuite_list_agents`, `agentsuite_kernel_artifacts`, `agentsuite_cost_report` are now callable.

Actual tool names are `agentsuite_founder_run`, etc. (verified in `agentsuite/agents/founder/mcp_tools.py:127`).

**Why this matters**

A user follows the quick-start exactly, restarts Codex, tries to call `founder_run`. Either the host returns "tool not found" or it dispatches to a different MCP server. Either way, broken first-run experience.

The registry normalizes hyphens to underscores (`agentsuite/agents/registry.py:36`), so `trust-risk` vs. `trust_risk` between README and `docs/index.html` is *not* a bug — just inconsistency.

**Blast radius**
- 1 README hit.
- Migration: none in code.
- Related findings: DOC-001, DOC-002.
- Fix path: Edit README line 96 to prefix all five tool names with `agentsuite_`.

---

### [DOC-010] — Major — Accuracy — Press kit wheel-size claim off by 1.7×

**Evidence**

`docs/press-kit/README.md:44`:
> - **Package size:** ~190 KB wheel, ~95 KB sdist

Actual on disk (`ls -la dist/`):
- `agentsuite-1.0.0-py3-none-any.whl` — 327130 bytes (~327 KB)
- `agentsuite-1.0.0.tar.gz` — 220087 bytes (~220 KB)

Press kit claims wheel 190 KB — actual 327 KB (1.72×). sdist claim 95 KB — actual 220 KB (2.32×).

**Why this matters**

Press kit goes to journalists. They quote numbers verbatim. A wheel size nearly 2× the claim is a small embarrassment that appears in any 30-second `pip download` check.

**Blast radius**
- 1 hit.
- Fix path: Replace with current numbers measured at release time, or drop the size claim entirely (not load-bearing).

---

### [DOC-011] — Major — Hygiene — `pyproject.toml` ships `Development Status :: 3 - Alpha` classifier on a v1.0.0 GA wheel

**Evidence**

`pyproject.toml:11`:

```toml
classifiers = [
    "Development Status :: 3 - Alpha",
    ...
]
```

This is package metadata that ships in the .whl and is read by `pip show`, deps.dev, Libraries.io, etc. CHANGELOG `[1.0.0]` line 12: "**General availability.** First public release."

**Why this matters**

A v1.0.0 GA wheel marked "Alpha" is an internal contradiction. A reader running `pip show agentsuite` sees "Development Status: 3 - Alpha" and concludes the v1.0.0 number doesn't mean what the project says. Meta-credibility hit: project shipped a version it doesn't believe in.

**Blast radius**
- 1 file (pyproject.toml).
- Distribution: wheel + sdist metadata.
- Fix path: Change to `Development Status :: 5 - Production/Stable` (matches GA) or `Development Status :: 4 - Beta`. 5 is the honest read of "we just locked the compatibility surface." Change in next doc patch and rebuild wheel.

---

### [DOC-012] — Major — Accuracy — `docs/index.html` says "26 artifacts" and "14 artifacts" of the same sample run

**Evidence**

- `docs/index.html:55`: "persists **26 artifacts** to disk"
- `docs/index.html:73`: "Browse the full output of a real run — **14 artifacts**, no install required"

Both about the same Founder sample-output directory. Actual directory has 20 top-level entries plus 11 brief templates inside `brief-template-library/` = 29 files.

**Why this matters**

Landing page contradicts itself within 20 lines.

**Blast radius**
- 1 page, 2 hits.
- Related findings: DOC-001, DOC-003.
- Fix path: Pick one count (recommend "29 files" since verifiable) and use everywhere on the landing page.

---

### [DOC-013] — Minor — Hygiene — index.html roadmap card still says "v0.8 Next Agent" after v1.0 GA

**Evidence**

`docs/index.html:117–120`:

```html
<h2>Roadmap</h2>
<div class="grid">
  <div class="card"><h3>v0.8 Next Agent</h3><p>Coming soon.</p></div>
</div>
```

Project shipped through v0.9.3 into v1.0.0. The placeholder is months stale.

**Fix path**

Replace with actual roadmap from CHANGELOG `[Unreleased]`: "v1.0.x — patch releases for any post-launch friction. v1.1.x — first minor: candidates from rc1 Discussions Ideas board (8th agent, per-day cost cap)."

---

### [DOC-014] — Minor — Tone / Hygiene — ADR-0001 narrative still describes pre-`2b1dda0` state in body, then update note refutes it

**Evidence**

ADR-0001 lines 6–17 describe rubric asymmetry (Founder=7, others=9) as if current. Lines 26–31 add a 2026-04-28 update note saying Founder is now 9. Rubric-audit page (line 13) explicitly flags this as "minor follow-up — not a code change."

**Fix path**

Fold the update note into the body. Move the original asymmetry-resolved narrative into a "## History" section at the bottom.

---

### [DOC-015] — Minor — Accuracy — CHANGELOG v0.2.0 references `google-generativeai`; pyproject and code use `google-genai`

**Evidence**

CHANGELOG `[0.2.0]` line 386: "**`google-generativeai>=0.8`**"

But `pyproject.toml:30`: `gemini = ["google-genai>=1.0,<2"]` and `agentsuite/llm/gemini.py:24`: `from google import genai`.

Modern wheel uses `google-genai`. CHANGELOG entry is historically accurate (v0.2.0 may have used the older lib) but reading sequentially could mislead.

**Fix path**

Add a parenthetical to v0.2.0: "(superseded by `google-genai` in v0.X)." Or leave alone — historical CHANGELOG entries are by convention not edited.

---

### [DOC-016] — Minor — Hygiene — CHANGELOG `[Unreleased]` link footer shows v0.9.1, not v1.0.0

**Evidence**

`CHANGELOG.md:422`:

```
[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v0.9.1...HEAD
```

Should be `v1.0.0...HEAD` after the GA tag lands.

**Fix path**

Bump in the post-GA doc patch.

---

### [DOC-017] — Minor — Onboarding — `discussions-seeds.md` uses relative links that won't resolve on the GitHub Discussions site

**Evidence**

`docs/community/discussions-seeds.md:137–141` uses relative paths (`../USER-MANUAL.md`, `../../CONTRIBUTING.md`). Inside the repo browsing, these resolve correctly. But once posted into the GitHub Discussions web UI, relative paths from a Discussions post don't resolve to repo files.

**Fix path**

Convert all relative links in the discussion seed posts to absolute GitHub URLs (e.g., `https://github.com/scottconverse/AgentSuite/blob/main/CONTRIBUTING.md`) before pasting. Local copy can keep relative links for in-repo navigation.

---

### [DOC-018] — Minor — Accuracy — Sample-output README says "8 reusable brief templates"; should be 11

See DOC-003. Listed separately for fix-tracking parity.

---

### [DOC-019] — Nit — Tone — USER-MANUAL uses "AI brain" as a pedagogical metaphor

`docs/USER-MANUAL.md` step-2b uses "AI brain" twice. Mildly cutesy for v1.0.0 reference doc; not technically wrong. Optional cleanup.

---

### [DOC-020] — Nit — Hygiene — `pyproject.toml` description repeats README hero verbatim

`pyproject.toml:5` repeats the same one-liner that appears in README hero, USER-MANUAL, and press kit. Reusing is fine; flagging that single-source-of-truth (e.g., extract from `__init__.py.__doc__` at metadata-build time) would prevent drift.
