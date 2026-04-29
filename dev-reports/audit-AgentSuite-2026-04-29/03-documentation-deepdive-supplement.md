# Documentation Deep-Dive SUPPLEMENT - AgentSuite v1.0.0 GA

**Audit date:** 2026-04-29
**Role:** Technical Writer (second pass)
**Relationship to primary report:** Supplements the primary `03-documentation-deepdive.md` already on disk. All findings in the primary report stand; this file adds findings the primary pass missed.
**Auditor posture:** Adversarial
**Writer mode:** audit+draft

---

## Why a supplement

A primary documentation deep-dive is on disk at `03-documentation-deepdive.md`. It is a strong audit (19 findings; captures the load-bearing accuracy errors: broken `docs/README-FULL.pdf` link [DOC-006], 5-vs-6-stage drift [DOC-001], MCP tool-name drift in compat freeze [DOC-002], test-count drift [DOC-005], `Development Status :: 3 - Alpha` classifier on a GA wheel [DOC-011], two divergent USER-MANUAL files [DOC-007]). I credit those findings without re-litigating.

This supplement adds **six findings** the primary pass missed, including **two Blockers** that materially affect the v1.0 launch surface, plus drafted replacements in `doc-rewrites/`.

## Severity rollup (this supplement only)

| Severity | Count |
|---|---|
| Blocker | 2 |
| Critical | 2 |
| Major | 1 |
| Minor | 1 |

Combined with the primary deep-dive, total documentation findings:

| Severity | Combined |
|---|---|
| Blocker | 2 |
| Critical | 5 |
| Major | 9 |
| Minor | 7 |
| Nit | 2 |
| **Total** | **25** |

---

## Supplemental findings

### [DOC-S01] Blocker — Marketing/Honesty — Landing page "Spec artifacts (rendered)" embeds a screenshot whose body literally says "Mocked content."

**Evidence**
- `docs/index.html` lines 78-80 embed `screenshots/brand-system-rendered.svg` and `screenshots/qa-report-rendered.svg` under heading "Spec artifacts (rendered)" with NO caption disclosing they are mock-LLM output.
- `docs/screenshots/brand-system-rendered.svg` line 71 contains styled-terminal text "Mocked content." That is the entire body of the rendered "brand system" the visitor sees.
- `examples/sample-output/founder/brand-system.md` confirms: full file is two lines, headline plus "Mocked content."
- `README.md` lines 211-215 ("Screenshots and sample output" table) embeds the same SVG with caption "`brand-system.md` rendered." — also no mock disclosure.

**Why this matters**
A first-time visitor on the GitHub Pages site reads "What you get on disk → Spec artifacts (rendered)" and sees a screenshot whose visible body is the word "Mocked." They conclude either (a) the product ships placeholder output, or (b) the project is sloppy. Both readings are launch-killing. The honest framing — "this is the on-disk file under our deterministic test fixture; live runs produce real LLM content with the same shape and layout" — is straightforward. The current framing is dishonest.

The UI/UX role flagged this; the primary documentation deep-dive on disk did not. Words on screen are a documentation accuracy concern as much as a UI one.

**Blast radius**
- Adjacent assets: `qa-report-rendered.svg`, `runs-tree.svg`, `kernel-tree.svg` all derive from the same mock fixture.
- Other surfaces: README "Screenshots and sample output" table.
- User-facing: every visitor of `scottconverse.github.io/AgentSuite` above the fold.
- Migration: replace SVGs and/or add captions; existing paths can stay.
- Tests to update: none.
- Related findings: primary DOC-003 (sample-output undercount), DOC-S02.

**Fix path**
Two acceptable options:
1. Re-render under a real LLM run at v1.0 GA, sanitize, re-export SVGs.
2. Add unambiguous captions on every embed: "Rendered from the deterministic mock LLM fixture; live runs produce real content with the same shape and file layout."

Recommend option 2 immediately and option 1 within v1.0.x. Drafted caption block at `doc-rewrites/index.html-sample-section.html`.

---

### [DOC-S02] Blocker — Accuracy — Hero CLI screenshot shows a flag that does not exist and progress markers the CLI does not emit

**Evidence**
- `README.md` line 7 embeds `docs/screenshots/cli-founder-run.svg` as the hero. `docs/index.html` line 72 embeds the same SVG.
- The SVG (line 128) shows the literal arg: `--founder-voice-samples examples/patentforgelocal/voice-sample.txt`
- `agentsuite/agents/founder/agent.py` lines 73-79 (`build_cli_spec`): the only Founder run flags are `--business-goal`, `--project-slug`, `--inputs-dir`, `--run-id`, `--force`. **There is no `--founder-voice-samples` flag.**
- The SVG (lines 130-134) shows progress lines `intake complete` through `qa complete` with checkmark prefixes. The current `run_cmd` in `agent.py` echoes only the final JSON block via `typer.echo(json.dumps(...))`. **No checkmark markers are emitted.**
- CHANGELOG v0.8.1 line 254 confirms the markers were once shipped: "Stage progress markers (D1) — checkmark stage complete printed after each pipeline stage before the final JSON." Either the feature was lost between v0.8.1 and v1.0 without a CHANGELOG entry, or the screenshot was generated against a non-production code path.

**Why this matters**
The hero screenshot — the single image first-time users see above the install fold — depicts a CLI invocation the current product cannot run. A user who copies the command verbatim gets `Error: No such option: --founder-voice-samples`. Even after fixing that, they will not see the checkmark lines. Documentation accuracy Blocker because it directly contradicts shipping code.

**Blast radius**
- Adjacent: same SVG embedded in two places.
- User-facing: every first-time visitor.
- Migration: re-render the SVG; pin the rendering script.
- Tests to update: add screenshot regeneration check to `scripts/verify-release.sh`.
- Related findings: DOC-S01.

**Fix path**
1. Regenerate `cli-founder-run.svg` from a real command matching README quick-start exactly: `agentsuite founder run --business-goal "Launch PatentForgeLocal v1" --project-slug pfl --inputs-dir ./examples/patentforgelocal`.
2. Decide whether the checkmark markers should be restored (per v0.8.1 CHANGELOG) — restore in code if yes; update screenshot if no.
3. Add deterministic-mock screenshot regeneration to the release pipeline.

---

### [DOC-S03] Critical — Accuracy — README MCP env example uses `trust-risk` (hyphen); registry uses `trust_risk` (underscore)

**Evidence**
- `README.md` line 93 (Codex example): `AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust-risk,cio"`
- `README.md` line 108 (Claude Code/Cowork example): same hyphen.
- `agentsuite/mcp_server.py` line 24: registry key is `"trust_risk"` (underscore).
- `docs/index.html` lines 93, 101 use the correct `trust_risk` form.
- `docs/troubleshooting.md` lines 67-71 explicitly: "Note that `trust_risk` uses an underscore, not a hyphen. **This is a common mistake.**"

**Note vs primary DOC-009:** Primary deep-dive flagged this generally as Major and characterized it as "not a bug — just inconsistency" because the registry "normalizes hyphens to underscores." Re-reading `agentsuite/agents/registry.py` and `mcp_server.py`, I do not find env-var hyphen-normalization for `enabled_names()`. If hyphen-normalization happens it is on a path I did not find; if it does not, this is a hard accuracy bug warranting Critical.

**Why this matters**
A user who copies the README MCP snippet — the documented happy path — risks `UnknownAgent: trust-risk` on first start. Troubleshooting explicitly identifies this as the common mistake; the README is the source of the common mistake.

**Blast radius**
- 2 README occurrences; `docs/index.html` is correct.
- User-facing: every reader of the README MCP section.
- Migration: text fix; verify the registry behavior.
- Related findings: primary DOC-009.

**Fix path**
Replace both README MCP `trust-risk` instances with `trust_risk`. Add a one-line note about the CLI hyphen vs identifier underscore convention. Drafted replacement at `doc-rewrites/README-mcp-section.md`.

---

### [DOC-S04] Critical — Hygiene — No SECURITY.md

**Evidence**
- `ls AgentSuite/SECURITY.md` → does not exist.
- `ls AgentSuite/.github/SECURITY.md` → does not exist.
- README does not state how to report a vulnerability privately.
- Product has supply-chain hygiene: CHANGELOG v0.8.3 added `pip-audit --strict` plus a CycloneDX SBOM attached to each Release. Maintainer cares about security; the public-disclosure pathway is unstated.

**Why this matters**
A v1.0 GA OSS project without SECURITY.md is hygiene-incomplete. A researcher who finds a vulnerability has nowhere to report privately and may default to a public issue. GitHub flags repos without SECURITY.md as a repo-health signal.

**Fix path**
Add `SECURITY.md` (drafted at `doc-rewrites/SECURITY.md`): supported versions, GitHub Security Advisories private-disclosure channel, response-time commitments, scope.

---

### [DOC-S05] Major — Hygiene — No CODE_OF_CONDUCT.md

**Evidence**
- `ls AgentSuite/CODE_OF_CONDUCT.md` → does not exist.
- CONTRIBUTING.md does not link a CoC.
- The repo has Discussions seeded; community presence is intentional.

**Why this matters**
Standard OSS hygiene at v1.0. GitHub flags repos without a CoC. Once Discussions is enabled and people show up, the CoC is the doc you want before you need it.

**Fix path**
Add `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1). Link from CONTRIBUTING.md.

---

### [DOC-S06] Minor — Accuracy — README "Roadmap: v0.8.0 — next agent" is stale at v1.0.0 GA

**Evidence**
- `README.md` line 273 (Status section) shows "v0.8.0 — next agent" as roadmap.
- Project shipped through v0.9.3 into v1.0.0; v0.8.0 is in the past.
- CHANGELOG `[Unreleased]` is current.

**Note vs primary DOC-013:** Primary flagged the parallel staleness on `docs/index.html`. Same staleness exists on README — same source-of-truth issue, two surfaces.

**Fix path**
Replace README Roadmap section with current `[Unreleased]` content (v1.0.x patches, v1.1.x first-minor candidates).

---

## Drafts produced

Locations under `dev-reports/audit-AgentSuite-2026-04-29/doc-rewrites/`:

- `doc-rewrites/index.html-sample-section.html` — Honest captioned "Sample run" section. Addresses DOC-S01.
- `doc-rewrites/README-mcp-section.md` — Replacement README MCP env examples using correct `trust_risk` form, with naming-conventions note. Addresses DOC-S03 + primary DOC-009.
- `doc-rewrites/SECURITY.md` — Standard OSS SECURITY.md pointing to GitHub Security Advisories. Addresses DOC-S04.
- `doc-rewrites/verify-release-link-check.sh` — Shell snippet for `scripts/verify-release.sh` validating every doc-internal link. Prevents primary DOC-006 + DOC-S02 class regressions.

---

## Marketing / honesty audit (cumulative)

Single root cause across DOC-S01, DOC-S02, primary DOC-006, DOC-008, DOC-013: **the doc-asset generation pipeline was not re-run against v1.0 reality before the GA tag**.

1. `cli-founder-run.svg` was rendered from an older or fictional CLI surface and never re-rendered against current `agent.py`.
2. Mock-derived spec/qa/tree screenshots were never captioned to disclose source.
3. README-FULL.pdf was placed at repo root, never moved into `docs/` where the docs reference it.
4. `[Unreleased]` and Roadmap sections in README and `index.html` were not bumped at the GA tag.

A pre-push `verify-release.sh` block running (a) link-existence on every internal Markdown/HTML link, (b) screenshot regeneration with deterministic-mock and checksum diff, and (c) "no doc claim contradicts code" grep would have caught all four. Maintainer's CLAUDE.md priorities (UX > docs/QA > code) are well-stated and the code seems to honor them; the doc-verification automation does not yet — that is the highest-leverage fix in the audit.

---

## Patterns and systemic observations (additive)

- **Pattern: screenshot assets are static, not regenerated.** SVG screenshots ship without a regeneration script tied to release. This is what allowed `cli-founder-run.svg` to drift past the actual CLI without anyone noticing.
- **Pattern: docs lie about what is "rendered" output vs. a fixture.** Mock-derived screenshots are passed off as rendered real output across multiple surfaces.
- **Pattern: missing standard OSS hygiene files at GA.** SECURITY.md and CODE_OF_CONDUCT.md absent — both are GitHub repo-health signals. Maintainer's discipline elsewhere (ADRs, pip-audit, SBOM attach, Discussions seeds drafted) is high; these two missing files are out of character.

---

## Appendix: additional artifacts cross-checked for this supplement

- `agentsuite/agents/founder/agent.py` lines 60-115 — confirmed CLI flag set
- `agentsuite/agents/founder/mcp_tools.py` lines 127-147 — confirmed registered tool names
- `agentsuite/agents/cio/mcp_tools.py` lines 212-236
- `agentsuite/agents/trust_risk/mcp_tools.py` lines 208-232
- `agentsuite/mcp_server.py` lines 18-26 — registry keys use underscore
- `agentsuite/cli.py` lines 142-165 — agent module list
- `docs/screenshots/cli-founder-run.svg` (full grep for flag and checkmarks)
- `docs/screenshots/brand-system-rendered.svg` (full grep for "Mocked")
- `examples/sample-output/founder/brand-system.md` (full file)
- `examples/sample-output/founder/README.md`
- File-presence checks: `SECURITY.md`, `CODE_OF_CONDUCT.md`, `docs/README-FULL.pdf` (all absent)
