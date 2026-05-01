# UI/UX Deep-Dive — AgentSuite v1.0.1 (closure audit)

**Audit date:** 2026-04-29
**Role:** Senior UI/UX Designer
**Scope audited:** v1.0.1 fix surfaces — `docs/index.html`, `docs/screenshots/cli-founder-run.svg`, `docs/screenshots/brand-system-rendered.svg`, `docs/screenshots/qa-report-rendered.svg`, `examples/sample-output/founder/README.md`, `README.md` MCP tool names, `agentsuite/kernel/base_agent.py` stage progress emitter, `agentsuite/cli.py` `--quiet` flag. Closure verdict against the v1.0.0 audit's UX-001 / UX-002 / UX-003 / UX-004 / UX-006.
**Auditor posture:** Balanced — verify closure honestly, give credit where the fix lands, name what's still open.
**HEAD audited:** `de2a7a3` (chore: release v1.0.1 — sprint 1 audit-fix release)

---

## TL;DR

Three of the five named UX findings are genuinely closed; the Blocker is half-closed and the closure is structurally honest in the right places but rhetorically inconsistent in the most-trafficked place; UX-005 (placeholder Roadmap) was not in scope for v1.0.1 and remains open. The CLI stage-progress emitter is a real win — the implementation is small, the format is stable across plain consoles and `rich.save_svg` exports, and `--quiet` works exactly as designed when verified end-to-end against the mock provider. The remaining UX debt is no longer about the product lying; it's about the landing page and the README still using the word "real run" three lines above the new "mock-LLM scaffold" disclaimer they added — that is the v1.0.2 must-fix.

## Severity roll-up (UX, v1.0.1 closure pass)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 2 |
| Minor | 3 |
| Nit | 2 |

(Down from v1.0.0: 1 Blocker, 3 Critical, 5 Major, 6 Minor, 3 Nit.)

## Per-ID closure verdict

| ID | v1.0.0 severity | v1.0.1 verdict | Why |
|---|---|---|---|
| UX-001 | Blocker | **Partially closed → downgraded to Critical** | Disclaim copy added at `docs/index.html:78-79` and an honest `examples/sample-output/founder/README.md` rewrite. The Blocker (representing mock output as a real run) is no longer a Blocker. But: `docs/index.html:73` still reads "Browse the full output of **a real run** — 14 artifacts," and `README.md:217` still reads "every artifact **a real Founder run produces**." Both paragraphs sit *above* the new "(rendered, mock-LLM scaffold)" subsection on the landing page. A reader scanning top-to-bottom sees "real run" first and the qualifier 30+ words later. New finding **UX-101** below. |
| UX-002 | Critical | **Closed** | `README.md:96` and `README.md:129` now use the prefixed `agentsuite_founder_*` names. `USER-MANUAL.md` has no per-agent tool-name strings (verified with grep — zero hits for the unprefixed pattern). Drift-detection tests are present per the `75301f9` test-CR-04 commit. |
| UX-003 | Critical | **Closed** | `docs/screenshots/cli-founder-run.svg` was regenerated from a real CLI invocation (commit `ffd134f`). The SVG now shows `[OK] intake complete  (0.0s, $0.0000)` etc. — exactly what `_emit_stage_progress` writes to stderr. Verified by running the CLI against the mock provider end-to-end; emitted lines match the SVG byte-for-byte (modulo timing). The screenshot is no longer fictional. |
| UX-004 | Critical | **Closed** | The non-existent `--user-request` and `--founder-voice-samples` flags have been removed from the screenshot. Current SVG shows only `--business-goal`, `--project-slug`, `--inputs-dir` — all of which exist on `run_cmd`. Grep for the bogus flag names in the SVG returns zero hits. |
| UX-006 | Major | **Closed** | `_emit_stage_progress` writes one stderr line per completed stage with elapsed seconds and cumulative cost; runtime verification: `[OK] intake complete  (0.0s, $0.0000)` … through `[OK] qa complete  (0.0s, $0.0000)` while stdout receives only the JSON summary. `--quiet` / `AGENTSUITE_QUIET=1` correctly suppresses (verified: stderr empty under `--quiet`). The 5 tests in `tests/test_cli_progress.py` cover the contract. |

---

## What's working in v1.0.1

- **Stage-progress emitter is exemplary in three ways at once.** (a) Output goes to stderr while JSON stays on stdout — `agentsuite founder run | jq` still works; verified empirically. (b) ASCII-only `[OK]` sigil renders identically on cp1252 Windows consoles, on UTF-8 terminals, and inside `rich.Console.save_svg()` exports — that last property is what lets the SVG screenshot be regenerated honestly. (c) The cost field is *cumulative* not delta, which matches what an operator running against the `AGENTSUITE_COST_CAP_USD` cap actually wants to see. This is a small, careful piece of UX engineering.
- **`--quiet` semantics are clean.** Single env var (`AGENTSUITE_QUIET`) is the source of truth; the CLI flag just exports it; case-insensitive truthy parse covers `1`, `true`, `yes`, `True`, `YES`. End-to-end run with `--quiet` produced an empty stderr — the contract holds.
- **`examples/sample-output/founder/README.md` reads as adult honesty, not apology.** "What this is, exactly … What this is not … Want to see real LLM content?" with a copy-pasteable command and a $0.20–0.40 price quote. It does not over-explain or grovel. The "v1.0.2 follow-up" footer is the right shape — it names the deferred work, points at `dev-reports/.../next-sprint-watchlist.md`, and tells the reader exactly what changed in v1.0.1 vs. what's coming. This is the right reference for how every "we shipped the disclaim, the regen is queued" doc should read.
- **Re-recorded CLI screenshot is visually coherent.** The terminal frame, the dimmed `(0.0s, $0.0000)` parens, the JSON summary block — all of it reads as a real session. The `[OK]` color (`#98a84b`, a muted olive-green) is less visually loud than a green check `✔` would be, which is appropriate for a screenshot the user will see immediately above their own terminal output. Not a regression — a deliberate restraint.
- **Drift-detection tests in `75301f9`** institutionalize the UX-002 fix. README MCP tool names are now backed by an asserting test, not just author-discipline.

---

## Findings (v1.0.1 → v1.0.2)

### [UX-101] — Critical — Copy — Landing-page lede paragraph still says "real run" three lines above the new "mock-LLM scaffold" disclaim

**Evidence**
`docs/index.html:73` (unchanged from v1.0.0):
> Browse the full output of a real run — 14 artifacts, no install required — at examples/sample-output/founder/.

`docs/index.html:78-79` (added in `5ee2f00`, v1.0.1):
> ### Spec artifacts (rendered, mock-LLM scaffold)
> *The screenshots below are rendered from **deterministic mock-LLM output** — the artifact shape is real, but the body text is scaffold strings. To see real LLM-generated content, run the agent yourself with a configured provider; see the sample-output README.*

`README.md:217` (unchanged):
> Browse a complete sample run on GitHub at `examples/sample-output/founder/` — every artifact a real Founder run produces, no install required.

`docs/screenshots/brand-system-rendered.svg` still contains 10 occurrences of the literal string "Mocked"; `qa-report-rendered.svg` still contains 10 instances of `8.00` rubric scores (mock-stub signature).

**Why this matters**
A reader scans top-to-bottom. The "real run — 14 artifacts" claim lands first; the qualifier lands 30 words later under a different `<h3>`. The disclaim *fixes the legal/ethical exposure* (the project no longer represents mock output as real), but it does not fix the *first-impression UX*. A skim-reader who only reads the bolded claim still walks away thinking they're about to see real Claude output, clicks through, and discovers stubs. The Blocker that was UX-001 is downgraded — the page no longer baldly lies — but the surface still misleads on first read. Same problem at `README.md:217`.

**Blast radius**
- Adjacent: `docs/index.html:73`, `README.md:217`, `docs/press-kit/README.md:27` ("a real run on GitHub without installing anything"), `dev-reports/2026-04-28-handoff-v0.9.1-shipped.md:54` (internal but mirrors the same phrasing).
- User-facing: every visitor to the landing page or README who scans rather than reads.
- Migration: zero. Two-line copy edit until the v1.0.2 regen lands.
- Tests to update: none — but adding a one-line CI check that greps `docs/index.html` and `README.md` for the substring `real run` and fails until v1.0.2 ships the regen would prevent the next regression.
- Related findings: UX-001 (this is the unfixed *rhetorical* half of the v1.0.0 Blocker; the v1.0.1 fix was the *structural* half).

**Fix path (v1.0.2 hotfix copy edit, 5 minutes)**

Replace `docs/index.html:73` with:
> Browse a complete sample run — every artifact AgentSuite's Founder produces, generated under the deterministic mock LLM so it works without an API key. See the [sample-output README](https://github.com/scottconverse/AgentSuite/tree/main/examples/sample-output/founder) for what's authentic vs. scaffold; or run the agent yourself with a real provider.

Replace `README.md:217` with the same shape:
> Browse a complete sample run on GitHub at `examples/sample-output/founder/` — every artifact AgentSuite's Founder produces, generated under the deterministic mock LLM. See that directory's README for what's authentic vs. scaffold.

Better fix (v1.0.2 structural): regenerate the sample against Claude Sonnet ($0.30, queued per `examples/sample-output/founder/README.md:34`). Once committed, change "deterministic mock LLM" → "Claude Sonnet (run YYYY-MM-DD, $0.31)" with attribution under each rendered SVG. That closes UX-001 *and* UX-101 in one PR.

---

### [UX-102] — Major — Copy/Pattern — "v0.8 Next Agent — Coming soon" card still on a v1.0.1 landing page

**Evidence**
`docs/index.html:118-121` (unchanged from v1.0.0; this is the v1.0.0 UX-005 finding rolled forward):
```html
<h2>Roadmap</h2>
<div class="grid">
  <div class="card"><h3>v0.8 Next Agent</h3><p>Coming soon.</p></div>
</div>
```

The page H1 reads `<h1>AgentSuite <span class="v">v1.0.1</span></h1>`. A v1.0.1 page whose only roadmap card is titled "v0.8" reads as either a stale page or a backwards version scheme.

**Why this matters**
The v1.0.0 audit flagged this at Major. v1.0.1 was scope-locked to the four named CR fixes plus engineering hardening; UX-005 was deferred. That's a defensible scope choice, but as v1.0.2 follow-up it should be top of the list along with UX-101 — both are 5-minute copy fixes and they reinforce each other (the page's "GA wasn't groomed" feel is what UX-005 + UX-009 + UX-014 + UX-017 collectively point at; closing UX-101 raises the bar on the others).

**Blast radius**
- Adjacent: `README.md:272-273` had the same problem in v1.0.0; verify state in v1.0.1.
- User-facing: every visitor reading top-to-bottom.
- Tests: none.
- Related: v1.0.0 UX-005, UX-009 (voice drift between landing and README — also unfixed in v1.0.1).

**Fix path**
Either name the next agent ("v1.1 — Operations Agent: incident response, runbook automation"), reframe as a status panel ("Stable: v1.0.x · Next minor: 1.1.x — additional agent TBD"), or remove the Roadmap section. The current state — a 0.x card on a 1.x page — is the worst option.

---

### [UX-103] — Major — State — Stage progress doesn't show *during* a stage, only at completion

**Evidence**
`agentsuite/kernel/base_agent.py:175` emits the `[OK]` line *after* `handlers[stage](state, ctx)` returns. There is no in-flight indicator — no `[..] spec running…`, no spinner. End-to-end run against mock provider finishes in <1s so this is invisible there, but on a real Anthropic Sonnet run the `spec` stage can be 30–90s of silence between two `[OK]` lines.

**Why this matters**
The v1.0.1 fix closes the UX-006 *acute* problem (the CLI no longer appears hung for the entire run). But the underlying issue — silent gaps between stages — remains. A user watching `[OK] extract complete (3.1s, $0.043)` followed by 60 seconds of nothing before `[OK] spec complete` will still wonder if the process hung. The v1.0.0 audit's UX-006 fix path option 2 (Rich `Status` per stage) addresses this; the v1.0.1 fix path option 1 was chosen instead, which is the right tradeoff for a hotfix release but leaves the better UX on the table.

**Blast radius**
- Adjacent: same emitter, same `_drive` loop.
- User-facing: every CLI user on a real-LLM run.
- Migration: stdout/stderr discipline already established by v1.0.1, so a `rich.status.Status` upgrade is purely additive.
- Tests: extend `tests/test_cli_progress.py` to assert a "running" line appears.
- Related: v1.0.0 UX-008 (token tick during run — still missing).

**Fix path**
v1.0.2 or v1.1: wrap the `handlers[stage](state, ctx)` call in a `rich.status.Status(stderr=True)` and emit `[..] {stage} running…` while in-flight, replaced by `[OK] {stage} complete (…)` on return. Keep the ASCII-fallback path for `AGENTSUITE_QUIET` and for non-TTY stderr (CI logs). Suppress the spinner when `not sys.stderr.isatty()` so CI logs don't get terminal escape sequences.

---

### [UX-104] — Minor — Copy — `[OK]` is less visually clear than `✔` for keyboard-glance scanning

**Evidence**
The v1.0.1 emitter writes `[OK]` (commit `50eda4c` rationale: cp1252 console safety on Windows, plus identical render in `rich.save_svg`).

**Why this matters**
ASCII `[OK]` is unambiguously the right *engineering* call — it survives the worst-case console encoding and the screenshot pipeline. But `[OK]` is two characters wider than `✔`, more visually noisy, and reads as "OK button" to a developer who's been trained on web UI patterns. The screenshot loses a small amount of polish for a large amount of correctness. Net: this is a Minor "we made the right tradeoff but acknowledge what was lost" finding, not a regression.

**Fix path**
Optional v1.x: detect `sys.stderr.isatty()` AND `sys.stderr.encoding.lower() in {"utf-8", "utf8"}` and emit `✔` only when both are true; fall back to `[OK]` otherwise. The `rich.save_svg` rendering path can still use `[OK]` because it's a recorded session, not a live tty. Adds 5 lines, removes the visual cost on modern terminals, keeps the Windows safety. Not worth a sprint, worth a paragraph in CONTRIBUTING.

---

### [UX-105] — Minor — Copy — Sample-output README's "v1.0.2 follow-up" section is project-internal in tone

**Evidence**
`examples/sample-output/founder/README.md:32-34`:
> Replacing the mock-LLM bodies in this directory with content from a real Anthropic Sonnet run is queued for v1.0.2 (cost ~$0.30, requires maintainer credentials). Tracked in `dev-reports/audit-AgentSuite-2026-04-29/next-sprint-watchlist.md` as the v1.0.1 deferred half of CR-01. The honesty fix above (this README) closes the v1.0.0 audit Blocker that conflated mock output with real run output.

**Why this matters**
"CR-01," "audit Blocker," "next-sprint-watchlist.md" — all of this is project-internal vocabulary. A first-time visitor to `examples/sample-output/founder/` is a developer evaluating AgentSuite, not an auditor reading the dev-reports. The audit-team breadcrumb is useful inside the project but reads as "we're showing our homework" to an outsider, which slightly undermines the directness of the rest of the README.

**Fix path**
Trim to:
> Replacing these mock-LLM bodies with content from a real Anthropic Sonnet run is queued for v1.0.2 (cost ~$0.30).

Move the dev-reports breadcrumb to `dev-reports/audit-AgentSuite-2026-04-29-v101/next-sprint-watchlist.md` itself, where it belongs.

---

### [UX-106] — Minor — Copy — `cost_usd` field still missing from CLI run-summary JSON

**Evidence**
v1.0.0 finding UX-013: the trailing `typer.echo(json.dumps(...))` at `agentsuite/agents/founder/agent.py:101-105` echoes only `run_id`, `primary_path`, `status`. v1.0.1 stage progress now exposes per-stage cost on stderr; the final-summary JSON on stdout still does not include `cost_usd`, `qa_passed`, or `artifact_count`.

This was not in the v1.0.1 CR scope so it's not a closure failure — but with stage progress now showing live cost, the *final* JSON not echoing total cost is now an asymmetry the user can feel: stderr told them every stage's cumulative cost, stdout's summary then drops it.

**Fix path**
Add `cost_usd` (round 4dp), `qa_passed` (`not state.requires_revision`), and `artifact_count` to the JSON. Three-line fix per agent's `run_cmd`. Closes v1.0.0 UX-013 and tightens the new stage-progress UX. Roll into v1.0.2.

---

### [UX-107] — Nit — Copy — "v1.0.1" badge still rendered as muted small print

**Evidence**
`docs/index.html:29`: `h1 .v { font-size: 0.9rem; color: var(--muted); margin-left: 0.5rem; font-weight: normal; }`. v1.0.0 UX-017 flagged this; v1.0.1 simply incremented the version string from `1.0.0` to `1.0.1` without revisiting the styling.

**Fix path**
Same as v1.0.0 UX-017. Bump to `font-weight: 600` and `color: var(--accent)`. One-line CSS edit.

---

### [UX-108] — Nit — Visual — Screenshot timing column reads `(0.0s, $0.0000)` because regen ran against the mock

**Evidence**
`docs/screenshots/cli-founder-run.svg` shows every stage at `0.0s` and `$0.0000`. This is correct — the regen was done against the deterministic mock per `ffd134f`'s commit message — but a developer who reads "0.0s, $0.0000" five times in a row will register it as suspicious before they register that this is the mock provider.

**Fix path**
Either (a) add a one-line caption under the screenshot saying "Recorded against the deterministic mock LLM. Real provider runs are 10–30s per stage and ~$0.05 each." or (b) rebuild the screenshot from a real Anthropic run as part of UX-101's structural fix — the v1.0.2 regenerated sample-output run becomes the source for both the directory and the screenshot. (b) is the better outcome and closes three findings (UX-101, UX-105's redirect target, UX-108) in one PR.

---

## Cross-cutting closure assessment

The v1.0.1 fix landed a **structurally sound subset** of the v1.0.0 Blocker:

- The CLI no longer lies about itself (UX-003, UX-004, UX-006 all closed).
- The MCP surface no longer lies about itself (UX-002 closed; drift tests added).
- The sample-output README no longer lies about itself (CR-01 honesty disclaim closed).

But it left the **rhetorical half** of UX-001 open:

- The landing page and README still call it "a real run" in their primary paragraphs, with the honest "mock-LLM scaffold" qualifier added below in a less-prominent subsection.
- The rendered SVG screenshots (`brand-system-rendered.svg`, `qa-report-rendered.svg`) still embed the literal "Mocked content." string and the `8.00` stub scores.

This is the difference between "the project does not commit fraud anymore" (closed) and "the project's first impression is honest" (still open). For v1.0.1 — a hotfix release scoped to the named CRs — the structural close is the right deliverable. For v1.0.2, the rhetorical close (UX-101) plus the structural regen against a real provider closes UX-001 fully and removes the last "GA wasn't groomed" UX debt.

## v1.0.2 follow-up notes (priority order)

1. **UX-101** — Replace "real run" copy at `docs/index.html:73` and `README.md:217` with the new mock-aware copy. 5 minutes, no code changes.
2. **Regenerate against Claude Sonnet** — Close UX-001's structural half (queued in `examples/sample-output/founder/README.md:34`). $0.30, one maintainer credential, one PR. Closes UX-101, UX-108, and refreshes UX-105's wording.
3. **UX-102** — Roadmap card. 5 minutes.
4. **UX-106** — Add `cost_usd` / `qa_passed` / `artifact_count` to CLI summary JSON. 30 minutes per agent × 7 agents, or a single shared helper for ~30 minutes total.
5. **UX-103** — Rich `Status` in-flight indicator between stages. 1–2 hours including tests.
6. **UX-107, UX-108, UX-104** — visual nits, batch into a v1.x polish sprint.

Single-PR shape that closes the most v1.0.2 weight: regenerate sample-output against Claude → re-render SVG screenshots from the real markdown → update `docs/index.html:73` and `README.md:217` copy → replace `cli-founder-run.svg` with a real-provider recording. That one PR closes UX-101, UX-104 (real-provider screenshot uses native `✔` if encoding allows), UX-105, UX-108, and the structural half of UX-001 in one move.

## States audit matrix (v1.0.1 delta only)

| Component / page | Default | Loading | Empty | Error | Partial | Notes |
|---|---|---|---|---|---|---|
| CLI `agentsuite founder run` | ✓ | ✓ | ✓ | ✓ | n/a | **Loading state added in v1.0.1.** Per-stage `[OK]` line on stderr. UX-103 notes the in-flight gap. |
| CLI `--quiet` mode | ✓ | (suppressed) | ✓ | ✓ | n/a | Verified end-to-end: stderr empty under `--quiet`. |

## Appendix: surfaces verified in this closure pass

- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/index.html` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/README.md` (lines 80-220 read for MCP names + sample-output copy)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/screenshots/cli-founder-run.svg` (full text inspection — `--user-request` and `--founder-voice-samples` confirmed absent)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/screenshots/brand-system-rendered.svg` (text inspection — "Mocked" still present, 10 occurrences)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/screenshots/qa-report-rendered.svg` (text inspection — 10 instances of `8.00` stub scores)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/examples/sample-output/founder/README.md` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/cli.py` (full read — `--quiet` impl)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/kernel/base_agent.py` (`_emit_stage_progress` + `_drive` loop)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/USER-MANUAL.md` (grep — zero hits for unprefixed founder_* names; UX-002 closure confirmed)
- Runtime: end-to-end run of `agentsuite founder run` against `agentsuite.llm.mock:_default_mock_for_cli` produced 5 `[OK]` stderr lines and the JSON summary on stdout; same run with `--quiet` produced an empty stderr.
