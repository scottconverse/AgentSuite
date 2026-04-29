# Good-first-issue tickets to file before v1.0.0-rc1 (drafts)

Three drafts for `good first issue` tickets to file in the GitHub issue tracker before tagging v1.0.0-rc1. Pick three (or substitute), file via `gh issue create`, label `good first issue` + `help wanted`. Each one is self-contained, has clear acceptance criteria, and touches code paths that don't require deep kernel knowledge.

Suggestion: file in this order; the first is the smallest and easiest, the third has the most learning value.

---

## Issue 1 — Add `--quiet` flag to suppress stage progress markers

**Title:** Add `--quiet` flag to the CLI to suppress stage progress markers

**Body:**

> Currently `agentsuite founder run` (and the other six agents) emit stage progress markers (`✔ <stage> complete` lines) to stdout/stderr. For users running AgentSuite from scripts, CI jobs, or piped invocations, these markers are noise.
>
> Add a `--quiet` (`-q`) flag to all `agentsuite <agent> run` commands that suppresses the progress lines. JSON summary output at the end of the run is unaffected — the flag only silences the per-stage lines.
>
> ## Acceptance
>
> - `agentsuite founder run ... --quiet` produces zero output before the final JSON summary.
> - Without `--quiet`, behavior is unchanged.
> - Test: `tests/integration/test_cli_quiet.py` (new) — invoke `agentsuite founder run` under mock LLM with and without `--quiet`, assert stdout content matches expectation in each mode.
> - Documented in `README.md` quick-start and `USER-MANUAL.md` CLI reference.
>
> ## Where to look
>
> - `agentsuite/cli.py` — add the Typer flag.
> - `agentsuite/kernel/base_agent.py` ~line 147 — the `_log.debug("✔ %s complete", stage)` is gated by log level; the user-visible markers come from somewhere else; trace and confirm.
>
> ## Difficulty
>
> Small. ~1–2 hours including the test. No kernel changes — just CLI plumbing.

**Labels:** `good first issue`, `help wanted`, `cli`

---

## Issue 2 — Add Marketing-agent walkthrough to USER-MANUAL

**Title:** Add a complete Marketing-agent example walkthrough to USER-MANUAL

**Body:**

> The USER-MANUAL has a glossary and per-agent input reference, but the Marketing agent section currently lacks a complete worked example showing input → output → next-action. The Founder section has one; the others should match.
>
> ## Acceptance
>
> - `docs/USER-MANUAL.md` gains a `### Marketing — worked example` subsection under the Marketing reference.
> - The example walks through:
>   1. The user's intent ("we're launching a SaaS dev-tool, B2B, $50/mo, dev audience")
>   2. The CLI invocation with all required flags
>   3. The 9 spec artifacts produced (campaign-brief, target-audience-profile, messaging-framework, content-calendar, channel-strategy, seo-keyword-plan, competitive-positioning, launch-plan, measurement-framework) — one-line each on what the artifact contains
>   4. The 8 brief-templates produced and what they're for
>   5. What to do with the output (where it lands, how to consume it from a downstream agent)
> - Tone matches the Founder example — patient, plain-language, no jargon without definition.
> - Screenshot of the rendered campaign-brief.md is welcome but not required.
>
> ## Where to look
>
> - `docs/USER-MANUAL.md` — find the Founder example and use it as a template.
> - `agentsuite/agents/marketing/agent.py` — confirm the artifact list matches reality.
> - `examples/sample-output/founder/` — for output-style reference (Marketing agent doesn't yet have a sample-output dir).
>
> ## Difficulty
>
> Medium. ~3–4 hours of patient writing. No code changes.

**Labels:** `good first issue`, `help wanted`, `documentation`

---

## Issue 3 — Add unit test for `AGENTSUITE_OUTPUT_DIR` env var

**Title:** Add unit test for `AGENTSUITE_OUTPUT_DIR` env var override

**Body:**

> Per `CLAUDE.md` and the `BaseAgent` constructor, agents write to `.agentsuite/` in CWD by default but honor an `AGENTSUITE_OUTPUT_DIR` env var override. This is documented but doesn't have a test, so a future refactor could silently break it.
>
> Add a focused unit test that:
>
> 1. Sets `AGENTSUITE_OUTPUT_DIR=/some/tmp/path`
> 2. Instantiates an agent without an explicit `output_root` arg
> 3. Asserts artifacts land at `/some/tmp/path/runs/<run-id>/`, not at `./.agentsuite/runs/<run-id>/`
> 4. Confirms the explicit `output_root=` argument still wins over the env var (precedence)
>
> ## Acceptance
>
> - New test in `tests/unit/kernel/test_output_dir.py` (or extend an existing suitable file)
> - Two test functions: `test_env_var_override`, `test_explicit_arg_wins_over_env`
> - Test uses `monkeypatch.setenv` for env-var manipulation; cleans up after itself
> - Pre-existing tests unaffected
>
> ## Where to look
>
> - `agentsuite/kernel/base_agent.py` — find the env-var read in `__init__` (or wherever it lives)
> - `agentsuite/cli.py` — for an example of `monkeypatch` patterns in the existing test suite
> - `tests/unit/kernel/` — folder pattern to match
>
> ## Difficulty
>
> Small-medium. ~2 hours including a quick read of the env-var handling code. Good intro to AgentSuite's test infrastructure.

**Labels:** `good first issue`, `help wanted`, `tests`

---

## Filing checklist

Before posting:

1. Verify each issue's "where to look" file paths still match current code.
2. Update difficulty estimates if they look off after a fresh skim.
3. File via `gh issue create --title "..." --body-file <path> --label "good first issue,help wanted,<area>"`.
4. After all three are filed, link them from the v1.0.0-rc1 release notes and from the Discussions "Welcome" announcement.
