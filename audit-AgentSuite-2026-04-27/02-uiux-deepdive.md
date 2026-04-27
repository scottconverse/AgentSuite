# UI/UX Deep-Dive — AgentSuite

**Auditor:** Senior UI/UX Designer
**Date:** 2026-04-27
**Scope:** CLI, landing page, README, USER-MANUAL, MCP tool surfaces, artifact output experience

---

## Executive Summary

AgentSuite's documentation surfaces (README, USER-MANUAL) are genuinely strong — thorough, patient in tone, and accurate. The landing page is technically sound but undersells the product and lacks visual differentiation. The CLI has a deep, pervasive discoverability problem: the primary user workflow requires knowing the right agent subcommand before `--help` reveals it, and the help texts for core required arguments are terse to the point of being unhelpful. Several agents are missing `approve` and `list-runs` commands in the CLI despite the pattern being established. MCP tool descriptions are adequate but rely on Python type inference rather than explicit docstrings, meaning Claude Code will see bare function signatures with no guidance. There are no Blocker-level UX failures — a motivated developer can complete the workflow — but there are two Critical gaps that will create real friction on first use.

---

## What's Working Well

- **USER-MANUAL is the best surface in the project.** Agent-by-agent walkthroughs, clear tables of output files, a glossary that grows with each agent, an actionable common-errors table. The tone is consistently patient. A genuine non-technical person could follow this.
- **README quick-start is accurate and complete.** The Ollama offline path is first-class, not an afterthought. The artifact tables are precise and useful.
- **CLI argument naming is consistent across all 7 agents.** Every `run` command uses long-form option names (`--business-goal`, not `-g`). Naming conventions match the USER-MANUAL examples exactly — no translation friction.
- **Landing page is technically clean.** Viewport meta tag present, responsive grid breaks at 600px, semantic HTML, no dead anchor tags. The version badge is current.
- **MCP tool naming is consistent.** `{agent}_run`, `{agent}_approve`, `{agent}_get_status`, `{agent}_list_runs`, `{agent}_resume` is a predictable pattern across all 7 agents.
- **Output JSON from CLI is structured and machine-readable.** The `run_id`, `status`, `stage`, `cost_usd`, and `primary_path` fields are stable across agents — a downstream harness can parse them without agent-specific logic.

---

## Findings

### Blockers

None identified.

---

### Critical

**C1 — CLI has no top-level discovery for the run workflow.**

Running `agentsuite --help` shows:
```
Commands: agents, list-runs, founder, design, product, engineering, marketing, trust-risk, cio
```
There is no description on any agent subcommand that tells the user what that agent produces. A first-time user sees "founder" and "cio" as bare labels. They must already know to run `agentsuite founder --help` to discover `run` and `approve`. The root `--help` gives no hint that `run` is the primary verb or what each agent does. This is the first thing a new developer sees after install.

**Impact:** First-time users will stall at the CLI entry point. A developer who just did `pip install` and runs `agentsuite --help` gets a list of opaque subcommand names with no indication of what to do next.

**Fix:** Add a one-sentence `help=` string to each `typer.Typer()` declaration that includes the primary output (e.g. `"Founder agent — brand system, voice guide, prompt library. Start here."` rather than just `"Founder agent commands"`). The current help strings for `design_app`, `engineering_app`, etc. do include artifact names, but `founder_app` only says `"Founder agent commands"` — the most-used agent has the weakest help text.

---

**C2 — `founder_run` and `design_run` MCP tool signatures have no docstrings — Claude cannot self-document them.**

The MCP tool functions `founder_run`, `founder_resume`, `founder_approve`, `founder_get_status`, and `founder_list_runs` are registered via `server.add_tool(name, fn)` with no docstring on the callable. The engineering agent tools have the same pattern. When Claude Code introspects these tools, it sees the function name and type signature only — no description of what the tool does, what `business_goal` should contain, or what `project_slug` is used for. The `EngineeringRunRequest` model has a `role_domain` default of `"engineering"` (inconsistent with `"engineering-ops"` used in CLI) with no explanation.

**Impact:** An AI harness (Codex, Claude Code) cannot reliably invoke `founder_run` without guessing at parameter intent. The `business_goal` field has no description annotation in `FounderRunRequest`. A model may pass a URL, a JSON blob, or a 3000-word brief when a single sentence is what's needed.

**Fix:** Add a `description=` argument to each `server.add_tool()` call and add `Field(description="...")` annotations to all required parameters in `FounderRunRequest`, `EngineeringRunRequest`, and equivalents. The README documents what these parameters should contain — that text needs to move into the schema.

---

### Major

**M1 — Four agents are missing `approve` and/or `list-runs` CLI commands.**

The `founder` and `design` agents have both `run` and `approve`. The `product`, `engineering`, and `marketing` agents have `run` but only `product_app` and `engineering_app` have no `approve` registered in `cli.py` (marketing has no `approve` command at all). Specifically:

- `product_app`: has `approve` ✓
- `engineering_app`: no `approve` command registered — `engineering_run_cmd` is defined but there is no `@engineering_app.command("approve")` in `cli.py`
- `marketing_app`: no `approve` command in `cli.py`
- `trust_risk_app`: has `approve` ✓ and `list-runs` ✓
- `cio_app`: has `approve` ✓ and `list-runs` ✓

A user following the USER-MANUAL's Step 4 ("approve") for Engineering or Marketing will get a `No such command 'approve'` error with no explanation.

**Fix:** Add `@engineering_app.command("approve")` and `@marketing_app.command("approve")` following the established `trust_risk_approve_cmd` pattern.

---

**M2 — Landing page agent cards use version prefixes instead of role names.**

The 7 agent cards are labeled `"v0.1 Founder"`, `"v0.2 Design"`, etc. Version numbers belong in the release history, not in the primary navigation. A developer scanning the page to find "the agent that does marketing plans" has to decode that `v0.5` is Marketing. The card body text corrects this for later agents (v0.4–v0.7 have descriptive bodies) but v0.1–v0.3 cards have weak bodies: `"v0.2 Design: Brief generation + brand QA scoring"` tells a new visitor almost nothing about what they would use this for.

**Fix:** Change card headings to role names (`Founder`, `Design`, `Product`, etc.) and move the version to a badge or secondary label. Expand v0.1–v0.3 card bodies to match the detail level of v0.4–v0.7.

---

**M3 — `run-id` collision is silent and destructive; USER-MANUAL doesn't warn about it.**

The CLI defaults `run_id` to `"run-cli"` for all commands when `--run-id` is omitted. A user who runs the Founder agent, then runs the Product agent, will have the second run overwrite `.agentsuite/runs/run-cli/` silently. The USER-MANUAL Step 4 says "The terminal prints a JSON status block when it's done" but says nothing about run ID uniqueness or the collision risk. The output JSON includes `"run_id": "run-cli"` but does not include a warning.

**Fix:** Either generate a timestamp run ID by default (matching the MCP path which uses `_now_id()`), or add a prominent warning in the USER-MANUAL and a `typer.echo` warning when the run directory already exists.

---

**M4 — Landing page install command contradicts README.**

The landing page shows:
```
pip install agentsuite
# or, no install:
uvx agentsuite-mcp
```

The README correctly says:
```
pip install git+https://github.com/scottconverse/AgentSuite.git
```
with a note that "there is no PyPI publication." The landing page implies a PyPI package exists. A developer who copies the landing page command will get a `pip install agentsuite` that either fails or installs the wrong package.

**Fix:** Align the landing page install block with the README. Use the `git+https://` form or add a clear parenthetical that this installs from GitHub.

---

**M5 — No visual elements anywhere — no screenshot, diagram, or demo output.**

The landing page is all text. There is no screenshot of a terminal run, no example of what `brand-system.md` looks like, no architecture diagram inline. The README architecture diagram is an ASCII art box. The USER-MANUAL has no visual examples of what the output files look like. A developer evaluating AgentSuite has no way to form a visual mental model of what they would get.

**Fix:** Add at minimum one code block showing a sample `brand-system.md` excerpt to the landing page (or a screenshot of a terminal run). A 10-line excerpt of real agent output would do more to sell this than any amount of prose.

---

### Minor

**m1 — `product approve` outputs plain text; all other agents output JSON.**

`product_approve_cmd` returns `typer.echo(f"Approved {run_id} by {approver}")`. All other agents (`trust-risk`, `cio`) also do this — only `founder` and `design` return JSON from `approve`. This is inconsistent. A harness parsing approval output will succeed on founder/design and fail silently on others.

---

**m2 — `AGENTSUITE_ENABLED_AGENTS` env var uses underscores in the MCP config examples but hyphens in README.**

The landing page MCP config shows `"trust_risk,cio"` (underscore). The README's MCP quick-start shows `"trust-risk,cio"` (hyphen). If the value is case/delimiter-sensitive, one of these is wrong. At minimum, the inconsistency will cause confusion.

---

**m3 — `agentsuite agents` shows `_registered` as a raw dict key in the output.**

```json
{
  "enabled": ["founder"],
  "all_registered": [...]
}
```
The key `"all_registered"` exposes internal naming from `reg._registered.keys()`. The key should be `"registered"` or `"available"` — not a name that maps directly to a private attribute.

---

**m4 — USER-MANUAL covers only 5 of 7 agents at depth.**

The manual has full walkthroughs for Founder, Product, Engineering, Marketing, Trust/Risk, and CIO. The Design agent has no walkthrough section — it goes from the Founder section directly to Product. A user trying to run `agentsuite design run` has no USER-MANUAL guidance.

---

**m5 — The Roadmap section on the landing page is a dead end.**

The v0.8 card says `"Coming soon."` with no ETA, no hint of what domain, and no link to a GitHub issue or discussion. This actively communicates that the project may be stalled.

---

**m6 — CLI `founder run` hardcodes `user_request` instead of using `business_goal`.**

Line 68 in `cli.py`:
```python
user_request=f"build creative ops for {business_goal}",
```
This is a synthetic string that discards the literal intent of the `--business-goal` flag. If the LLM uses `user_request` for any reasoning, it sees a paraphrased version of the input. The other agents (engineering, marketing) construct similarly synthetic `user_request` strings. This is an internal detail, but it could cause subtle output drift.

---

### Nits

**n1 — "Restart the harness" (README MCP Claude Code section) is not actionable.** A developer who doesn't know what "the harness" is — which includes most first-time users — won't know what to restart. Should say "Restart Claude Code."

**n2 — The footer on the landing page says "Issues + discussion welcome" with no link to the Issues URL.** The GitHub link goes to the repo root, not directly to `/issues`.

**n3 — `engineering_app` is initialized with `name="engineering"` and `help="Engineering Agent — ..."` but also registered as `app.add_typer(engineering_app, name="engineering")`. The duplicate `name=` on both the Typer constructor and `add_typer` is harmless but redundant — it exists inconsistently: `product_app`, `engineering_app`, `marketing_app`, `trust_risk_app`, and `cio_app` all do it; `founder_app` and `design_app` do not.**

**n4 — USER-MANUAL Step 4 for Founder says "walks 5 stages" but the pipeline has 6 stages** (intake → extract → spec → execute → qa → approval). The manual correctly lists 6 stages in the glossary.

**n5 — The landing page `<meta name="description">` is 197 characters, within limits, but uses "vague human intent" which is jargon.** A product description that a search engine surfaces should lead with the concrete deliverable.

---

## Surface-by-Surface Summary

**CLI:** The architecture is solid — 7 agents, consistent `run`/`approve`/`resume`/`get-status`/`list-runs` pattern, long-form option names, JSON output. The fatal UX gap is discoverability: the root `--help` gives no guidance on which agent to start with or what each one produces, and four agents have incomplete CLI coverage (missing `approve` or inconsistent output format). Error handling is delegated to Python exceptions by default — there is no user-facing error wrapper in `cli.py`. A `typer.BadParameter` or similar would be a meaningful improvement for invalid `--channel` values and missing API keys.

**Landing page:** Technically clean, mobile-responsive, correct links. The headline is accurate but not compelling — it reads like a tagline, not a value proposition. The agent cards are labeled with version numbers instead of role names, which is a discoverability problem for a first-time visitor. The install command is wrong (implies PyPI). No visual content whatsoever. The Roadmap section is a dead end. Could convert a motivated reader into an installer; unlikely to convert a cold visitor.

**README:** The strongest developer-facing doc. Accurate install instructions with a clear no-PyPI note, four separate quick-start paths (CLI, Ollama, Codex, Claude Code), full artifact tables for all 7 agents, and a working architecture diagram. The Design and Product artifact tables are stub entries ("see CHANGELOG") while Founder, Engineering, Trust/Risk, and CIO have full inline tables — an inconsistency that will frustrate users of those agents.

**USER-MANUAL:** Genuinely excellent for a CLI tool. Agent-by-agent walkthroughs, plain-language artifact descriptions, actionable error tables, cumulative glossary. Two gaps: the Design agent has no walkthrough, and the run-ID collision risk (defaulting to `"run-cli"`) is not documented. The tone is warm and consistent. A non-technical person could use this successfully.

**MCP tool surfaces:** The tool naming convention is predictable and consistent. The critical gap is the absence of docstrings and `Field(description=...)` annotations — an AI harness introspecting these tools will see bare function signatures. The `FounderRunRequest` class has no parameter-level documentation. The `EngineeringRunRequest.role_domain` default (`"engineering"` vs. `"engineering-ops"` in CLI) is an internal inconsistency. `expose_stages` stage tool names are inconsistent between agents: founder uses `founder_intake`, engineering uses `engineering_stage_intake`.

**Output artifact experience:** The JSON status block printed after a run is clean and machine-parseable. The `primary_path`, `run_id`, `status`, `cost_usd`, and `open_questions` fields give a harness everything it needs. The `"awaiting_approval"` status string is clear. The one problem is that `product_approve` and several others return a plain-text string instead of JSON, breaking the pattern a harness would rely on. There is no human-readable summary line printed alongside the JSON — a user running the CLI manually has to read and parse JSON to know if their run succeeded.
