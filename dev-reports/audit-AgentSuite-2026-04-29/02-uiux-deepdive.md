# UI/UX Deep-Dive — AgentSuite v1.0.0

**Audit date:** 2026-04-29
**Role:** Senior UI/UX Designer
**Scope audited:** docs/index.html landing page, README.md as front door, CLI invocation experience and stage-progress messages, error-message quality, MCP tool descriptions/schemas, the 5 SVG screenshots, examples/sample-output/founder/ browsability, copy/voice across surfaces. The `docs/index.html` was reviewed by reading the rendered HTML statically (no live browser harness in this audit pass — see "What couldn't be assessed").
**Auditor posture:** Adversarial

---

## TL;DR

For a v1.0.0 GA release, the surface that prospective adopters actually touch — the landing page, README, and "Sample run" exhibits — is materially misleading in three independent places, and that's the lede of this audit. The terminal screenshot fabricates per-stage progress output the CLI does not emit. The "Spec artifacts (rendered)" panel on the landing page literally displays the words "Mocked content." inside a stylized box, presented as if it were real Founder output. The README declares MCP tool names (`founder_run`, `founder_approve`, etc.) that do not match what the server actually registers (`agentsuite_founder_run`, etc.) — every developer who copy-pastes from the README will fail their first MCP call. Underneath those, the visual language is competent — restrained typography, clean grid, working Lighthouse pass — and the error messaging in the resolver and CLI is genuinely good. But "competent typography on a page that lies about the product" is not a v1.0 surface. **The single most important takeaway: the public-facing demo and the documented MCP schema must match the running code before this can be called GA.**

## Severity roll-up (UX)

| Severity | Count |
|---|---|
| Blocker | 1 |
| Critical | 3 |
| Major | 5 |
| Minor | 6 |
| Nit | 3 |

## What's working

- **Landing page restraint** (`docs/index.html`) — the 760px max-width single-column layout, system-font stack, and small color palette (one accent #2a4d8f on a #fafafa ground) read as a confident, modern dev-tool landing page rather than a corporate marketing template. No carousel, no hero illustration, no "Get started for free" CTAs that go nowhere. Above-the-fold lede ("Seven role-specific reasoning agents that turn vague intent into precise operating artifacts") gets close to passing the 5-second test.
- **`NoProviderConfigured` error copy** (`agentsuite/llm/resolver.py:92-96`) — when a user runs the CLI with no API key set, they get a single clear, actionable message naming all four providers and the local-Ollama escape hatch. This is exactly what the global standard prescribes and is rare in OSS dev tools.
- **CLI flag ergonomics** (`agentsuite/agents/founder/agent.py:73-99`) — `--force` overwrite gate with a clear "use --force to overwrite" hint, `--latest` shorthand on `approve`, and a typed `Path` for `--inputs-dir` are all correct choices. `cli.py` `--debug` global option for full tracebacks is the right shape.
- **MCP cross-agent tools work as documented** — `agentsuite_list_agents`, `agentsuite_kernel_artifacts`, `agentsuite_cost_report` registered names (`mcp_server.py:139-141`) match the README claim. Only the per-agent names drift (see UX-002).
- **Sample-output README is internally honest** (`examples/sample-output/founder/README.md:6`) — it explicitly identifies content as generated under "the deterministic mock LLM (`agentsuite.llm.mock._default_mock_for_cli`)." The honesty exists in the repo; it just doesn't propagate to the surfaces that drive adoption.
- **Favicon + robots.txt + `<main>` landmark** — recent Lighthouse-pass work added these correctly. The favicon is a tiny inline SVG (`docs/index.html:6`), no extra HTTP request, which is the right move for a single-page static site.

## What couldn't be assessed

- **Live rendered HTML at viewport sizes.** This audit was a static read of `docs/index.html`. I did not load it in 320 / 768 / 1024 / 1440 viewports through a real browser; CSS-layer issues (e.g. whether the 2-column `.grid` actually collapses cleanly, whether the SVG screenshots overflow on a 360-width Android Chrome) are inferred from the stylesheet, not measured. A QA pass with the Chrome MCP at three breakpoints is recommended as a follow-on.
- **MCP tool descriptions as the harness sees them.** I confirmed registered tool *names* but did not introspect the FastMCP schema as a connected harness (Codex/Claude Code) would render them — so I cannot judge the quality of parameter descriptions, defaults, or examples surfaced in the IDE picker. A subagent that runs `uvx agentsuite-mcp` and dumps `tools/list` would close this.
- **Discussions board state.** `docs/community/launch-posts.md` is on disk; whether the GitHub Discussions board has been seeded with these posts (Hard Rule 5 + global standard) was not verified in the GitHub API in this pass.
- **Lighthouse run's specific subscore breakdown.** The 96/100/100/100 number is taken on faith from the project context; `docs/lighthouse-rc1.report.json` exists but was not opened.

---

## First impressions

A first-time developer arriving at the landing page sees a clean, calm hero, a one-paragraph value prop, an `Install` snippet, and then — within one screen of scrolling — a Sample run section that's the entire reason they're here. Their eye lands on the first SVG: a terminal-style screenshot showing five green check marks and a JSON summary. Encouraging. They read down: "What you get on disk" (directory tree screenshot), "Spec artifacts (rendered)" — and there, in a stylized monospace panel, the visible body text is "Mocked content." Every assumption that this is a serious tool dies in that moment. This is the Blocker. The product the page is selling and the product visible in the screenshots are not the same product, and the gap is visible to a lay viewer in less than ten seconds.

If they don't notice that — or charitably assume "Mocked content" is some kind of demo placeholder — and proceed to wire up MCP, they hit the second wall: the README tells them to call `founder_run` and the actual registered name is `agentsuite_founder_run`. They'll either get a "tool not found" error in their harness or — worse, depending on harness — a silently empty result. They won't blame their harness. They'll blame AgentSuite.

## Journey walkthroughs

### Journey: "I'm a developer who just discovered AgentSuite, evaluate it in 5 minutes"

1. Land on `docs/index.html` from a Hacker News link or a tweet.
2. Read the lede. "Reasoning agents for vague intent → precise artifacts." OK, intriguing, vague but evocative.
3. Read "What it does." The 26-artifacts / six-stage / `_kernel/` framing is the strongest copy block on the page.
4. Scroll to "Sample run." See the terminal screenshot of green checkmarks. Believe it.
5. Click through to `examples/sample-output/founder/` on GitHub. Open `brand-system.md`. Read **"# brand-system\nMocked content."**. Internalize that the demo is fake. Trust evaporates.
6. Tab back, read "Quick start (MCP)," paste the `.mcp.json` block.
7. Restart the IDE. Try to invoke `founder_run` from the README. Get an error. Conclude AgentSuite is broken. Bounce.

This journey has two independent failure modes (UX-001, UX-002) that compound each other. Either one alone is recoverable; together they are a v1.0 release-quality issue.

### Journey: "I have AgentSuite installed, I'm running my first founder run from the CLI"

1. `export ANTHROPIC_API_KEY=...`
2. Run `agentsuite founder run --business-goal "Launch X" --project-slug x --inputs-dir ./inputs`.
3. Stage handlers run. Per `kernel/base_agent.py:147`, "✔ {stage} complete" is logged at **DEBUG** level, which means by default the user sees **nothing** for the duration of the run — could be 30 seconds, could be 5 minutes depending on provider. No spinner, no stage banner, no per-artifact echo, no token-spend tick. Just dead terminal.
4. At the very end, a single JSON blob lands. The user has no way to know during the run whether the agent is alive, hung, or running up a $2 bill.
5. The README/landing page screenshot shows checkmarks they never saw, deepening the feeling of "this product doesn't behave like advertised."

This is a Critical journey gap, separate from the screenshot-misrepresentation concern.

---

## Findings

### [UX-001] — Blocker — Copy/Pattern — Public landing page exhibits screenshot of "Mocked content." as the rendered Founder output

**Evidence**
`docs/index.html:79` references `screenshots/brand-system-rendered.svg`, captioned "brand-system.md rendered." The SVG (`docs/screenshots/brand-system-rendered.svg`) renders, inside a Rich-style monospace panel titled "brand-system.md", the literal body text:

```
brand-system

Mocked content.
```

Same pattern in `qa-report-rendered.svg` derives from `examples/sample-output/founder/qa_report.md`, which is the rubric report with every dimension scored exactly `8.00` — a giveaway that the scores are stubs from `agentsuite/llm/mock.py`, not real LLM scoring. Compounded by `docs/index.html:73`: "Browse the full output of a real run — 14 artifacts, no install required" — the page explicitly calls it a real run. It is not.

**Why this matters**
The single most-viewed UX surface of a v1.0.0 GA release tells prospective adopters, in their first 30 seconds, that the product produces output that says "Mocked content." in the place where its strongest spec artifact should be. Trust in the project — and in the maintainer — does not survive that moment. This converts the landing page from an asset into a liability.

**Blast radius**
- Adjacent surfaces showing the same problem: `docs/screenshots/brand-system-rendered.svg`, `docs/screenshots/qa-report-rendered.svg`, the README screenshots table at `README.md:209-217`, and the GitHub-browsable `examples/sample-output/founder/{brand-system.md, founder-voice-guide.md, audience-map.md, ...}` — every artifact in that directory is one-line stub content per `examples/sample-output/founder/README.md:6` (deterministic-mock provenance is honest internally but never surfaces on the landing page).
- User-facing: every developer evaluating AgentSuite from a public link, including funders, contributors, and partners. This is the conversion-killing surface.
- Migration: regenerating the sample requires running the Founder agent against a real LLM provider with $0.20–$1.00 of cloud spend (or a high-quality local Ollama run) on the `examples/patentforgelocal/` inputs, then committing the actual artifacts. Then re-rendering the SVGs from the real markdown.
- Tests to update: `tests/golden/test_founder_patentforgelocal.py` likely asserts the mock-stub bytes; either generate a separate live sample or split "byte-stable golden test" from "browsable real sample" — they are not the same thing.
- Related findings: UX-005 (sample-output README's mock-disclosure is not propagated upstream).

**Fix path**
Two-step fix:
1. Generate a real Founder run against the `examples/patentforgelocal/` inputs using a real LLM (Anthropic Claude is fine, ~$0.30 per the cost cap), commit those artifacts to `examples/sample-output/founder/`, and re-render the two screenshot SVGs (`brand-system-rendered.svg`, `qa-report-rendered.svg`) from the new markdown via the same `rich` pipeline. Keep the deterministic-mock fixtures somewhere else (`tests/fixtures/mock-founder-output/`).
2. On `docs/index.html`, change `<p>Browse the full output of a real run — 14 artifacts, no install required ...` to `<p>Browse a complete sample run — every artifact a Founder run produces, generated against Claude on the PatentForgeLocal scenario.</p>`. Drop the word "real" if you can't keep the screenshots in sync; or add a small attribution line under each rendered screenshot ("from a Claude-3.7-sonnet run, 2026-04-29, $0.31").

If a live regen is genuinely off the table for v1.0, the *minimum* acceptable fix is to remove the "Spec artifacts (rendered)" panel and the word "real" from the landing page, and add a "Sample fixtures use deterministic mock content" note to the sample-output's README that surfaces on the GitHub directory landing.

---

### [UX-002] — Critical — Copy/IA — README MCP tool names don't match what the server registers

**Evidence**
`README.md:96`: "Tools `founder_run`, `founder_approve`, `founder_get_status`, `founder_list_runs`, `founder_resume`, plus the cross-agent `agentsuite_list_agents`, `agentsuite_kernel_artifacts`, `agentsuite_cost_report` are now callable."

Actual registrations in `agentsuite/agents/founder/mcp_tools.py:127-131`:
```python
server.add_tool("agentsuite_founder_run", founder_run)
server.add_tool("agentsuite_founder_resume", founder_resume)
server.add_tool("agentsuite_founder_approve", founder_approve)
server.add_tool("agentsuite_founder_get_status", founder_get_status)
server.add_tool("agentsuite_founder_list_runs", founder_list_runs)
```

Same `agentsuite_<agent>_<verb>` pattern is consistent across all seven agents (`design`, `product`, `engineering`, `marketing`, `trust_risk`, `cio`). Only the cross-agent tools (`agentsuite_list_agents` etc.) match the README. `docs/index.html` doesn't quote per-agent names so it's spared this specific bug, but the README is the canonical front-door doc, linked from the landing page's Documentation section.

**Why this matters**
A developer pasting the suggested invocation into Codex / Claude Code / Cowork after restarting the harness will not find a tool called `founder_run`. They will either see "tool not found" in their IDE or a silent miss in agent autocomplete. The fix is one extra word per call, but they'll have no way to know that — they'll think the install is broken. This is the highest-volume-impact MCP-onboarding bug in the project.

**Blast radius**
- Adjacent code: `README.md:96`, plus the ASCII tool list in `docs/USER-MANUAL.md` (likely repeats the same names — verify), and any blog/social copy already published.
- User-facing: every MCP user's first call. Worst-case: a user assumes AgentSuite doesn't work and uninstalls before discovering the prefix.
- Migration: docs-only — pick one, fix forward. Do *not* rename the tools to match the README; the prefixed form is correct (collision-resistant, consistent with the project's MCP namespace convention).
- Tests to update: any contract test that asserts MCP tool names; the cleanroom test should grep for the documented tool names and fail if they're absent.
- Related findings: UX-007 (USER-MANUAL.md likely has the same drift), DOC-* in the docs role's audit.

**Fix path**
Edit `README.md:96` to:
> Tools `agentsuite_founder_run`, `agentsuite_founder_approve`, `agentsuite_founder_get_status`, `agentsuite_founder_list_runs`, `agentsuite_founder_resume`, plus the cross-agent `agentsuite_list_agents`, `agentsuite_kernel_artifacts`, `agentsuite_cost_report` are now callable.

Add a one-line `tests/test_readme_tool_names.py` that imports `build_server()`, lists registered names, and asserts every backticked `agentsuite_*` token in `README.md` is in that set. This is a 20-line test that prevents a class of bug.

---

### [UX-003] — Critical — Copy/Pattern — CLI screenshot shows progress output the CLI does not emit

**Evidence**
`docs/screenshots/cli-founder-run.svg` (referenced by both `docs/index.html:72` and `README.md:7`) shows a terminal session with:
```
✔ intake complete
✔ extract complete
✔ spec complete
✔ execute complete
✔ qa complete
```
followed by a JSON summary.

Actual stage-completion log: `agentsuite/kernel/base_agent.py:147`:
```python
_log.debug("✔ %s complete", stage)
```
Logged at **DEBUG** level, which Python's default `logging` config does NOT surface. Inspecting `agentsuite/agents/founder/agent.py:100-105`, the `run_cmd` does a single `typer.echo(json.dumps({...}))` after the entire run completes — no per-stage echoes, no spinner, no progress bar.

In other words, the screenshot shows output the running CLI does not produce.

**Why this matters**
Two compounding harms:
1. The screenshot is a credibility claim. A developer who runs the documented invocation will sit in front of a silent terminal for 30s–5min, with no signal that anything is happening, and will compare that experience to the screenshot they were sold. That gap reads as "the product is broken" or "I'm doing it wrong."
2. The runtime UX itself — silent for the entire duration of an LLM-bound run, with no cost ticker — is independently a Critical UX problem. The screenshot is fictional, but the fictional UX is *better than* the real UX, and the real UX needs the screenshot's behavior, not vice versa.

**Blast radius**
- Adjacent code: every agent's `run_cmd` (`agents/{founder,design,product,engineering,marketing,trust_risk,cio}/agent.py`) follows the same single-trailing-`typer.echo` pattern. Fix once in `kernel/base_agent.py`'s `run()` driver, applies to all seven agents simultaneously.
- User-facing: every CLI user, every run. This is the second-most-trafficked surface after the landing page.
- Migration: none for users; bumps the runtime print pattern from "silent until JSON" to "stage-by-stage status to stderr, JSON to stdout." Stdout-vs-stderr discipline preserves machine-readability — scripts that capture `agentsuite founder run > result.json` keep working.
- Tests to update: `tests/cli/test_*.py` that assert output shape will need to capture both streams; trivial.
- Related findings: UX-008 (no cost-tick during run).

**Fix path**
Two ways:
1. **Cheapest fix to make the screenshot honest:** add a `logging.basicConfig(level=logging.INFO)` in `cli.py`'s `_global_options` callback (gated on a `--quiet` flag for opt-out), and bump the `_log.debug` in `base_agent.py:147` to `_log.info`. Also emit them to stderr (the screenshot's color scheme implies stderr-style status output anyway).
2. **Better fix:** use Rich's `Status` / `Progress` directly (the screenshot is already rendered with Rich's `--export-svg`, so the dependency is already in the dev environment) and emit:
   ```
   ⠋ intake (running)…
   ✔ intake complete (0.3s, $0.012)
   ⠋ extract (running)…
   ✔ extract complete (4.1s, $0.043)
   ...
   ```
   This is what the screenshot implies and what serious dev tools do.

Either fix should be paired with a per-stage cost echo so the cost-cap (`AGENTSUITE_COST_CAP_USD=5.0`) feels visible rather than only enforced as a kill.

---

### [UX-004] — Critical — Copy — README-documented `--founder-voice-samples` flag does not exist on the founder run command

**Evidence**
The hero screenshot in the README and on the landing page (`docs/screenshots/cli-founder-run.svg`) shows the invocation:
```
$ agentsuite founder run \
    --user-request 'build creative ops for PatentForgeLocal' \
    --business-goal 'Launch PatentForgeLocal v1' \
    --project-slug pfl \
    --inputs-dir examples/patentforgelocal/ \
    --founder-voice-samples examples/patentforgelocal/voice-sample.txt
```

Actual `run_cmd` signature in `agentsuite/agents/founder/agent.py:73-79`:
```python
def run_cmd(
    business_goal: str = typer.Option(..., help="Required business goal"),
    project_slug: str | None = typer.Option(None, ...),
    inputs_dir: Path | None = typer.Option(None, ...),
    run_id: str | None = typer.Option(None, ...),
    force: bool = typer.Option(False, "--force", ...),
) -> None:
```

There is no `--user-request` flag and no `--founder-voice-samples` flag. The Typer CLI will reject the screenshot's invocation with `Error: No such option: --user-request`.

**Why this matters**
The most prominent screenshot on the entire landing page demonstrates an invocation that, if a user copy-pastes it (filling in their own paths), will fail at the first command. This is the third independent place where the published surface promises behavior the running code does not deliver.

**Blast radius**
- Adjacent code: `FounderAgentInput` in `agentsuite/agents/founder/input_schema.py` does have a `founder_voice_samples` field — the schema supports it; the CLI just doesn't expose it. Fix is to add the option to `run_cmd` and thread it into `FounderAgentInput(...)`.
- User-facing: every CLI user who tries the documented invocation.
- Migration: pure additive — add the flags to the CLI, no breaking change.
- Tests to update: add a CLI test that uses both `--user-request` and `--founder-voice-samples`.
- Related findings: UX-001, UX-003 — all three "screenshot lies" findings share a root cause: the screenshots were produced from an idealized invocation, not from the running CLI.

**Fix path**
Add to `run_cmd`:
```python
user_request: str | None = typer.Option(None, "--user-request", help="Free-text request for the agent (defaults from --business-goal)."),
founder_voice_samples: list[Path] = typer.Option(None, "--founder-voice-samples", help="Path(s) to founder voice-sample text files for voice extraction."),
```
and thread them into the `FounderAgentInput(...)` constructor. Then re-render the screenshot from the working CLI so the page and the binary agree.

---

### [UX-005] — Major — Copy — "v0.8 Next Agent — Coming soon" card on a v1.0.0 landing page

**Evidence**
`docs/index.html:117-120`:
```html
<h2>Roadmap</h2>
<div class="grid">
  <div class="card"><h3>v0.8 Next Agent</h3><p>Coming soon.</p></div>
</div>
```

The page header says `<h1>AgentSuite <span class="v">v1.0.0</span></h1>` (line 49). A v1.0 release whose roadmap is one card titled "Next Agent — Coming soon" reads as either (a) the version was bumped to 1.0 prematurely, or (b) the page wasn't updated when it was. Either way it undermines the GA framing.

**Why this matters**
"v1.0.0" carries semantic-versioning weight in the OSS world — it means "stable public API, contract honored." A roadmap card that announces nothing erodes the credibility of that 1.0. Combined with UX-001 and UX-002, the cumulative impression is that the surface and the project state were not reconciled before tagging GA.

**Blast radius**
- Adjacent surfaces: `README.md:272-273` ("Roadmap: v0.8.0 — next agent") has the same problem.
- User-facing: every visitor reading the page top-to-bottom; investors/funders specifically.
- Tests to update: none.
- Related findings: UX-001, UX-002 (collectively the "GA surface wasn't groomed before tagging" pattern).

**Fix path**
Either name the next agent concretely ("v1.1 — Operations Agent: incident response, runbook automation, on-call handoff") or remove the Roadmap section entirely until the team is ready to commit. A speculative roadmap card is worse than no roadmap card on a 1.0 page. If you want to signal "more coming," a single line under the agents grid — "Additional agents land in 1.x; subscribe to releases" — does the same job at lower cost.

---

### [UX-006] — Major — State — CLI run produces no progress signal during an LLM-bound run

**Evidence**
See UX-003 evidence: `kernel/base_agent.py:147` is the only stage-completion echo; it's at DEBUG level; `run_cmd` only emits a single trailing JSON. The `cost_tracker` accumulates in-memory but is not surfaced until the run completes. There is no spinner, no stage banner, no token tick, no "running…" indicator.

**Why this matters**
Distinct from the screenshot-lies finding: even if the screenshot were honest, the runtime is bad. A user running against Claude Sonnet on a 9-spec-artifact stage can sit silently for 30–90 seconds. With `AGENTSUITE_COST_CAP_USD=5.0` as the only kill switch, they have no idea whether the run is at $0.10 or $4.90 until it ends. Every modern dev-tool CLI in 2026 (gh, supabase, vercel, fly, cargo, npm) at minimum emits a Rich-style spinner with phase text. AgentSuite is below table stakes here.

**Blast radius**
- Adjacent code: same as UX-003 — fix at `kernel/base_agent.py` and propagates to every agent.
- User-facing: every CLI user every run.
- Migration: stdout-vs-stderr discipline — keep the JSON on stdout, status to stderr.
- Tests to update: capture both streams.
- Related findings: UX-003.

**Fix path**
Same as UX-003 fix path option 2: Rich `Status` per stage, with elapsed-seconds and cost-so-far in the status text. Pseudocode in `BaseAgent.run()`:
```python
from rich.status import Status
from rich.console import Console
console = Console(stderr=True)
for stage_name, handler in self.stage_handlers().items():
    with console.status(f"[bold cyan]⠋[/] {stage_name} (running)…"):
        state = handler(state, ctx)
    console.print(f"[green]✔[/] {stage_name} complete · {ctx.cost_tracker.total_usd:.3f} USD")
```

---

### [UX-007] — Major — Copy — `examples/sample-output/founder/` is a graveyard of one-line stubs but is the most-promoted exhibit in the project

**Evidence**
Sampling `examples/sample-output/founder/`:
- `brand-system.md` → `# brand-system\nMocked content.`
- `founder-voice-guide.md` → `# founder-voice-guide\nMocked content.`
- `audience-map.md` → `# audience-map\nMocked content.`
- `qa_report.md` → table with every dimension scored exactly `8.00`

Linked from `README.md:217` ("Browse a complete sample run on GitHub… every artifact a real Founder run produces") and `docs/index.html:73` ("Browse the full output of a real run — 14 artifacts, no install required").

**Why this matters**
Anyone who clicks through the "no install required" CTA — the most explicit "look, here's the goods" link in the entire project — sees fixture stubs. The friction-free evaluation path the team carefully built terminates in a moment of "this doesn't look serious." UX-001 is the screenshot version of this; UX-007 is the GitHub-browser version of the same root cause.

**Blast radius**
- Adjacent code: same root as UX-001 — regenerating one fixes both.
- User-facing: every developer who clicks through the sample-output link.
- Tests to update: `tests/golden/test_founder_patentforgelocal.py` (separate the byte-stable mock golden from the browsable live sample).
- Related findings: UX-001 (same root cause, different surface).

**Fix path**
See UX-001 fix path. Adding `MOCK FIXTURE — NOT A REAL RUN` as the first line of every file in `examples/sample-output/founder/` is the *minimum* if a real regen is impossible for v1.0. Better: regenerate against Claude, commit real artifacts.

---

### [UX-008] — Major — Accessibility — `<a>` tag accessibility relies on color alone for non-underlined visual states

**Evidence**
`docs/index.html:35-36`:
```css
a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; border-bottom: 1px solid transparent; }
a:hover { border-bottom-color: var(--accent); }
```

OK on default and hover, but there is no `:focus` or `:focus-visible` style. A keyboard user tabbing through the page receives only the browser-default focus ring (which on Chromium is a thin outline that's been variously broken/removed by user-agent stylesheets over the years). On the dark hero / light card backgrounds the default ring contrast is borderline. There's also no skip-to-main-content link despite the `<main>` landmark having been added in the recent Lighthouse pass.

The `:hover` style adds a `border-bottom`, which subtly shifts vertical rhythm by 1px — minor, but compounds with the absence of an explicit focus style.

**Why this matters**
Keyboard-only users and screen-reader+keyboard users navigating a single-page landing page can traverse it, but they don't get a strong focus signal. WCAG 2.1 SC 2.4.7 (Focus Visible) is met by browser default but only marginally; SC 2.4.1 (Bypass Blocks) is technically not satisfied without a skip link though enforcement on a single-section landing page is lenient.

**Blast radius**
- Adjacent code: just `docs/index.html` — single page.
- User-facing: keyboard and AT users.
- Tests to update: Lighthouse accessibility category should re-run; aXe-core would flag the missing focus style.
- Related findings: none.

**Fix path**
Add:
```css
a:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 2px;
}
```
and a skip link at the very top of `<body>`:
```html
<a href="#main" class="skip-link">Skip to main content</a>
```
with `.skip-link { position: absolute; left: -9999px; } .skip-link:focus { left: 0; top: 0; padding: 0.5rem; background: white; z-index: 100; }`. Add `id="main"` to the existing `<main>` tag.

---

### [UX-009] — Major — Copy — Voice/tone drifts between landing page and README

**Evidence**
- Landing-page lede (`docs/index.html:50`): "Seven role-specific reasoning agents that turn vague intent into precise operating artifacts. Open-source. MCP-compatible with Codex, Claude Code, and Cowork."
- README "Why AgentSuite" (`README.md:13-15`): "**For developers wiring AI into Codex / Claude Code / Cowork** who are tired of every generation re-introducing context and drifting on voice. AgentSuite is the operating layer between intent and output: seven role-specific agents that each walk a deterministic six-stage pipeline (intake → extract → spec → execute → qa → approval), persist 26 artifacts per run, and promote approved output into a `_kernel/` that the next run consumes."

Both are good, but they're solving for different audiences in different voices. The landing page is product-poetry ("vague intent → precise operating artifacts"); the README is empathetic-developer ("tired of every generation re-introducing context"). The README copy is *the better hook* and would land harder above the fold on the landing page than the abstract version currently there.

There's also a stage-count drift inside the same project: landing page says "six-stage pipeline (intake → extract → spec → execute → qa → approval)" (six items, treating approval as a stage); README "Quick start" (`README.md:51`) says "five stages, writes 26 artifacts"; the architecture diagram (`README.md:223-231`) shows five primary stages and renders approval as a gate not a stage. The kernel itself has a `Stage` Literal that includes `"approval"` and `"done"` as states. This is a small inconsistency that, in the README and landing page side by side, looks sloppy.

**Why this matters**
Voice consistency on a v1.0 surface is a trust signal. A reader doesn't consciously notice voice drift; they unconsciously register that "this product's surfaces don't feel built by the same person." Compounded with the screenshot/MCP-name issues, it's part of the "GA wasn't groomed" pattern.

**Blast radius**
- Adjacent: stage-count language is repeated in `docs/USER-MANUAL.md`, `docs/README-FULL.pdf` (rebuild needed), and probably a discussion-board seed post.
- User-facing: every reader who scans both surfaces.
- Tests to update: none.
- Related findings: UX-005.

**Fix path**
Pick one canonical sentence count and copy:
> AgentSuite is the operating layer between vague intent and precise output. Seven role-specific reasoning agents — Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO — each walk a deterministic six-stage pipeline (intake → extract → spec → execute → qa → approval), persist 26 artifacts per run, and promote approved output into a long-lived `_kernel/` the next run consumes. MCP-native, provider-agnostic, MIT-licensed.

Use that paragraph verbatim as the lede on the landing page, the first paragraph after the H1 in the README, and the abstract in `docs/README-FULL.pdf`. Pick **either** five-stage or six-stage and stop drifting; "five stages with an approval gate" reads cleanly to me.

---

### [UX-010] — Minor — IA — `Documentation` section on landing page links into GitHub blob URLs, not to served docs

**Evidence**
`docs/index.html:122-129`: every Documentation link points to `github.com/scottconverse/AgentSuite/blob/main/...` — README, USER-MANUAL.md, README-FULL.pdf, CONTRIBUTING.md, CHANGELOG.md.

Since the landing page is on GitHub Pages, the docs *could* be served at `/USER-MANUAL.html`, `/CHANGELOG.html` etc. with a tiny markdown-to-HTML build step (or a single Pandoc run in CI). Linking to GitHub blob views means users leave the curated UX and land in GitHub's chrome — different typography, no nav, harder to share clean URLs.

**Why this matters**
Minor — GitHub blob views are functional. But for a project whose landing page just got a Lighthouse pass, sending all secondary docs to GitHub-default rendering is leaving polish on the table.

**Fix path**
Either accept it (Minor — log and move on) or add a Pandoc step to `Makefile` that renders `docs/USER-MANUAL.md` and `CHANGELOG.md` to `docs/USER-MANUAL.html` and `docs/CHANGELOG.html` using the same CSS as `index.html`. ~30 lines of Makefile + CSS.

---

### [UX-011] — Minor — Copy — Provider check error doesn't include `unset` workaround for the inverse case

**Evidence**
`agentsuite/llm/resolver.py:92-96` is exemplary copy when *no* provider is configured. But there's no equivalent message for "I have ANTHROPIC_API_KEY set but I want to force Ollama." The user has to read the README to discover `AGENTSUITE_LLM_PROVIDER=ollama`. If they `unset ANTHROPIC_API_KEY` to "force" Ollama they get the message at `:87` — `"Ollama daemon not running…"` — only if Ollama isn't running. If Ollama is running and Anthropic key is set, auto-detect picks Anthropic without telling them.

**Why this matters**
Mild. A first-time Ollama-curious user could spend money on Anthropic by accident.

**Fix path**
After `resolve_provider()` resolves but before returning, emit one stderr line:
```
[agentsuite] Using provider: anthropic (auto-detected from ANTHROPIC_API_KEY). Set AGENTSUITE_LLM_PROVIDER to override.
```
Once. Suppressible with `--quiet` or `AGENTSUITE_QUIET=1`.

---

### [UX-012] — Minor — Copy — `Error: {exc}` swallows context in `cli.py:107`

**Evidence**
`agentsuite/cli.py:103-108`:
```python
except Exception as exc:
    if _debug_mode:
        traceback.print_exc()
    else:
        typer.echo(f"Error: {exc}", err=True)
    raise typer.Exit(1)
```

For a `pydantic.ValidationError`, `str(exc)` is OK. For a network error from the LLM provider, it's "Connection aborted." with no remediation ("retry; check API status; check provider"). The error message catches *every* exception and renders it identically.

**Fix path**
Add a small `_format_exc(exc)` helper that branches on common types — `httpx.ConnectError` → "Could not reach the LLM provider. Check network and provider status."; `pydantic.ValidationError` → keep the field-by-field detail; default → preserve current behavior. Keep `--debug` for full traceback.

---

### [UX-013] — Minor — Copy — JSON output of `run_cmd` only echoes 3 fields; users hitting the cap won't know

**Evidence**
`agentsuite/agents/founder/agent.py:101-105`:
```python
typer.echo(json.dumps({
    "run_id": state.run_id,
    "primary_path": str(_output_root() / "runs" / state.run_id / "brand-system.md"),
    "status": state.stage,
}, indent=2))
```

No `cost_usd`, no `qa_passed`, no `requires_revision`. The MCP `_result_from_state` (`mcp_tools.py:42-57`) is richer than the CLI output. Compare: the screenshot fakes `"cost_usd": 0.234`, `"qa_passed": true`, `"artifact_count": 14` — better fields than the real CLI emits.

**Fix path**
Mirror the MCP shape:
```python
typer.echo(json.dumps({
    "run_id": state.run_id,
    "agent": state.agent,
    "stage": state.stage,
    "primary_path": str(_output_root() / "runs" / state.run_id / "brand-system.md"),
    "cost_usd": round(state.cost_so_far.usd, 4),
    "qa_passed": not state.requires_revision,
    "artifact_count": <count of files in run_dir>,
}, indent=2))
```
This single fix also makes the screenshot honest retroactively.

---

### [UX-014] — Minor — Pattern — Two-column `.grid` with seven cards renders an awkward 4×2 with one orphan

**Evidence**
`docs/index.html:107-115` lists seven shipped agents in a `.grid { grid-template-columns: 1fr 1fr; }`. Seven items in a 2-column grid yields three full rows plus a single orphan card on row 4 — visually unbalanced.

**Fix path**
Either render as 1-column at all widths (lines up with the rest of the page's narrow column), or change to `repeat(auto-fit, minmax(220px, 1fr))` so cards reflow at viewport width. Or commit to a Roadmap card and make it eight cards (4×2). The first option is least clever and the right answer.

---

### [UX-015] — Nit — Copy — "Source on GitHub. Issues + discussion welcome." dead-ends if Discussions isn't enabled

**Evidence**
`docs/index.html:132`: "Source on <a href='...'>GitHub</a>. Issues + discussion welcome." Whether `github.com/scottconverse/AgentSuite/discussions` is enabled and seeded was not verified in this audit.

**Fix path**
If Discussions is on: link the word "discussion" to `…/discussions`. If not: drop "+ discussion" until it's enabled. Don't promise a forum that doesn't exist.

---

### [UX-016] — Nit — Visual — `h1` letterspacing of `-0.02em` is fine; `h2` could match for hierarchy consistency

**Evidence**
`docs/index.html:28`: `h1 { letter-spacing: -0.02em; }`. `h2`: no letter-spacing; gets the default normal. Visual treatment of headings drifts by one design token.

**Fix path**
Add `letter-spacing: -0.01em;` to `h2`. One-line fix. Not worth a sprint.

---

### [UX-017] — Nit — Copy — "v1.0.0" badge in the H1 is `font-weight: normal` and `0.9rem`; reads as small print rather than a proudly-stated version

**Evidence**
`docs/index.html:29`: `h1 .v { font-size: 0.9rem; color: var(--muted); margin-left: 0.5rem; font-weight: normal; }`. v1.0 is the headline of the headline; the styling whispers it.

**Fix path**
Bump to `font-weight: 600` and a non-muted color (e.g. the accent), or render as a real `<span class="badge">` pill. Subjective; flag and move on.

---

## States audit matrix

| Component / page | Default | Loading | Empty | Error | Partial | Notes |
|---|---|---|---|---|---|---|
| Landing page (`index.html`) | ✓ | n/a | n/a | n/a | n/a | Static page |
| CLI `agentsuite founder run` | ✓ | ✗ | ✓ | ✓ | n/a | Loading state missing — UX-006. Error state OK via `_format_exc` once UX-012 lands. |
| CLI `agentsuite founder approve` | ✓ | n/a | ✓ | ✓ | n/a | "no runs found" empty handled at `cli.py:76`. |
| CLI `agentsuite list-runs` | ✓ | n/a | ✓ | ✓ | n/a | Returns `"[]"` on empty — terse but honest. Could add a friendly hint: `[]  (no runs yet — try 'agentsuite founder run --help')`. |
| Sample-output GitHub directory | ✓ | n/a | n/a | n/a | n/a | But content is mock stubs — UX-001/UX-007. |
| MCP tool surface | ✓ | n/a | n/a | partial | n/a | Tool-name drift — UX-002. Not all error returns are typed. |

## Accessibility snapshot

- **Keyboard navigation:** Functional on `index.html`. Tab order is DOM order, which is also visual order — fine. Skip link missing (UX-008).
- **Focus visibility:** Browser default only. No explicit `:focus-visible` style (UX-008).
- **Color contrast (sampled):** Body text `#1a1a1a` on `#fafafa` ≈ 16.5:1, well above AA. `.lede` text `#555` on `#fafafa` ≈ 7.5:1, passes AA for normal and large. Accent links `#2a4d8f` on `#fafafa` ≈ 8.5:1, passes. Card text `#555` on `#ffffff` ≈ 7.6:1, passes. **No contrast issues found at sampled combos.**
- **Screen reader labeling:** All `<img>` tags have meaningful `alt` attributes (`docs/index.html:72,76,79,80,83`). The `<main>` landmark is present. `<header>` and `<footer>` are present. **No labeling issues found.**
- **Reduced motion:** No animations on the page; vacuously satisfied.
- **Touch target size:** Links inside body text inherit body's 1.6 line-height ≈ ~26px tall. Below 44px AA target on small phones. Not a Major finding for body-text links per WCAG 2.5.5 (Level AAA), but the install/MCP code blocks have small inline `<code>` regions that are not interactive. No interactive controls fail the 44px guideline because there are no buttons or form fields on the page.

## Patterns and systemic observations

**Pattern: "the surface and the binary disagree."** UX-001, UX-002, UX-003, UX-004 are four findings with one shared root cause — the public-facing artifacts (landing page, README, sample-output, CLI screenshot) were authored against an idealized version of AgentSuite, not the running code, and the gap was not caught before the v1.0.0 tag landed. Recommend a single PR that fixes all four together: regenerate the screenshot from the real CLI (after fixing UX-003 and UX-013 so the real CLI actually emits rich output), regenerate `examples/sample-output/founder/` from a real LLM run, fix the README MCP names, add a `tests/test_readme_tool_names.py` and a `tests/test_screenshot_invocation.py` (which subprocess-runs the literal command from the screenshot and asserts the documented flags exist) so this class of drift is caught by CI from now on.

**Pattern: "silent runtime."** UX-006 and UX-008 (focus-visible) are different surfaces of the same value: AgentSuite under-communicates with its user during operations. The CLI is silent during a multi-minute run; the landing page doesn't tell keyboard users where they are. Both are "the user is doing something but the product isn't acknowledging it" issues. Recommend one Sprint-1 ticket: "Add stage-by-stage progress emission to BaseAgent.run() with cost ticker; add `:focus-visible` and a skip link to docs/index.html."

**Pattern: "v1.0 polish wasn't done."** UX-005 (placeholder Roadmap), UX-009 (voice drift), UX-014 (orphan grid card), UX-017 (whispered version badge) all share a "this was groomed in a hurry" feel. None alone is critical; together they signal an unfinished GA. A single 30-minute pass through the page from the standpoint of "what would I tighten if I were shipping this to YC" would catch all of them.

## Appendix: surfaces reviewed

- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/index.html` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/README.md` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/cli.py` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/agents/founder/agent.py` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/agents/founder/mcp_tools.py` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/agents/founder/stages/qa.py` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/mcp_server.py` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/llm/resolver.py` (full read)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/agentsuite/kernel/base_agent.py:147` (targeted)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/screenshots/cli-founder-run.svg` (rendered text inspected)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/docs/screenshots/brand-system-rendered.svg` (rendered text inspected)
- `C:/Users/scott/OneDrive/Desktop/Claude/AgentSuite/examples/sample-output/founder/` (directory listing + 4 representative files read)
- All seven `agentsuite/agents/<agent>/mcp_tools.py` `add_tool(...)` lines via grep (registered names verified)
- All `Error:` strings across `agentsuite/` via grep
