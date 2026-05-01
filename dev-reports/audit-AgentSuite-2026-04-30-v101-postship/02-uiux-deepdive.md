# UI/UX Deep-Dive — AgentSuite v1.0.1

**Audit date:** 2026-04-30
**Role:** Senior UI/UX Designer
**Scope audited:** CLI (all 7 agent subcommands + global commands), MCP server entry point, docs/index.html landing page, USER-MANUAL.md, examples/sample-output/founder/README.md
**Auditor posture:** Balanced

---

## TL;DR

AgentSuite's CLI is structurally sound: progressive disclosure via subcommands, clean stderr/stdout separation, error messages that generally name the problem. The weakest dimensions are (1) an unhandled error class that bypasses the --debug gate and surfaces raw tracebacks unconditionally, (2) a USER-MANUAL install step that omits the required provider extra and leaves new users stranded before their first run, (3) a stale "v0.8 Next Agent - Coming soon" Roadmap card on the landing page that undermines the v1.0.1 release narrative, and (4) several copy and consistency issues that erode first-time developer trust. No single finding blocks the primary CLI workflow, but the unhandled traceback (UX-201) and the USER-MANUAL install gap (UX-204) together create a frustrating onboarding experience for the two most common entry paths.

---

## Severity roll-up (UX)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 2 |
| Major | 5 |
| Minor | 4 |
| Nit | 3 |

---

## What's working

- **Stderr/stdout stream discipline** — stage progress to stderr, JSON output to stdout. This is the right choice for a developer-integrator audience and is executed correctly. Shell piping works cleanly. The --quiet flag suppresses stderr markers for script use.
- **Error messages on missing required args** — Typer renders a clean boxed error ("Missing option '--business-goal'") with a help hint. No raw tracebacks for this class of mistake.
- **Provider auto-detection logic** — the resolver has a sensible priority (Anthropic -> OpenAI -> Gemini -> Ollama local) with specific, actionable error text for each missing prerequisite. The error message tells users exactly what to fix.
- **Trust-risk / trust_risk normalization** — the registry silently normalizes hyphens to underscores, so both forms work in AGENTSUITE_ENABLED_AGENTS. The runtime behavior is forgiving even where the docs disagree.
- **Stage progress format** — [OK] intake complete  (12.3s, $0.0234) is terse, informative, and pipe-safe. Surfaces time and cumulative cost at each gate without overwhelming output.
- **MCP help text** — agentsuite-mcp --help is hand-authored and surfaces all env vars with defaults and accepted values. Exactly what an integrator needs on first contact.
- **Landing page color contrast** — all sampled combinations pass WCAG 2.1 AA: muted text (#555) on background (#fafafa) is 7.14:1, accent links (#2a4d8f) are 7.87:1, body text (#1a1a1a) is 16.67:1.
- **Responsive grid** — the agent cards use a 2-column grid with a max-width:600px breakpoint that collapses to single-column. Works correctly.
- **--latest flag on approve** — resolving the most recent run by mtime is a high-value UX shortcut that reduces run-ID copy-paste friction for the common case.

---

## What could not be assessed

- **Actual rendered output of SVG screenshots on landing page** — the SVGs exist on disk but were not rendered in a live browser session. Correct rendering on GitHub Pages is assumed from file presence.
- **MCP tool behavior inside a live Codex/Claude Code harness** — tool schemas and docstrings were reviewed from source; actual tool invocation over stdio was not tested.
- **Dark mode rendering** — the landing page uses only CSS custom properties on :root with no prefers-color-scheme:dark block; it will render light-only. Noted as Nit-213, not assessed as broken since light-mode rendering is correct.
- **Known open issues UX-102, UX-103, UX-105, UX-106** — acknowledged as carried-in v1.0.2 backlog per the audit brief. UX-102 (stale roadmap card) and UX-105 (sample-output audit vocabulary) are re-elevated here with updated IDs because their severity warrants tracking in this report.

---

## First impressions

Arriving at docs/index.html as a developer evaluating AgentSuite:

The headline is clear: "Seven role-specific reasoning agents that turn vague intent into precise operating artifacts." Within five seconds I understand the product category. The lede is honest: "Open-source. MCP-compatible with Codex, Claude Code, and Cowork."

The install command (pip install "agentsuite[anthropic] @ git+...") is non-standard enough that a developer who has not seen the @ git+ form before may pause. No explanation of why it installs from GitHub rather than PyPI appears on the landing page.

The Roadmap section immediately undercuts the v1.0.1 release story. There is a single card reading "v0.8 Next Agent - Coming soon." A visitor who sees seven shipped agents listed, then a Roadmap showing "v0.8," will be confused about where the product actually is.

The SVG screenshots give visual grounding. The agent cards grid is clean and scannable. The quick-start code blocks are correct and copyable.

---

## Journey walkthroughs

### Journey 1: New developer, CLI path — install to first run to approve

**Step 1 — Install.**
If the developer uses the README or landing page, they get the correct command with a provider extra. If they find the USER-MANUAL first (linked from the landing page Documentation section), they get a bare pip install without any extra. The package installs without error, but running any agent then fails — in the worst case with a raw traceback (see UX-204).

**Step 2 — First run.**
After all five stages complete, stdout emits:

    {
      "run_id": "run-20260430T123456-abc123",
      "primary_path": ".agentsuite/runs/run-20260430T123456-abc123/brand-system.md",
      "status": "approval"
    }

No guidance on what to do next. The status field says "approval" - an internal stage name, not a human instruction. A first-time user stares at this JSON and must already know to run agentsuite founder approve.

**Step 3 — Approve.**
If the run directory has any schema version mismatch (common if the developer has an old .agentsuite/ from a pre-v0.9 run), _resolve_latest_run_id throws RunStateSchemaVersionError outside the try/except block. The user sees a full rich-formatted traceback regardless of --debug state (UX-201). On success, output shows run_id, status, approved_by - but no promoted artifact paths.

**Overall friction:** one critical error-handling hole, one missing "what next" signal, one missing post-approval confirmation.

---

### Journey 2: Developer integrator, MCP path — configure to discover tools to run

**Step 1 — Configure.**
The landing page and README both provide ready-to-paste config blocks. One inconsistency: the landing page snippet uses trust_risk (underscore) while the README snippet uses trust-risk (hyphen). Both work at runtime, but a new integrator sees two different forms in two canonical sources and must trust that it does not matter (UX-205).

**Step 2 — Discover tools.**
agentsuite-mcp --help returns a clean, hand-authored help block covering every env var with its default and accepted values. This is strong.

**Step 3 — Run a tool.**
Tool schemas are inferred from Python type annotations. The business_goal field has no example value in its description. The project_slug field has no constraint documented (alphanumeric? max length? hyphens allowed?).

---

## Findings

> **Finding ID prefix:** UX-
> **Categories:** Visual hierarchy / Copy / State / Accessibility / Responsive / Journey / Pattern / Motion / IA

---

### [UX-201] — Critical — State — Raw traceback escapes --debug gate on schema-version mismatch

**Evidence**
agentsuite/cli.py, line 120. The call _resolve_latest_run_id(agent_name_for_latest) sits outside the try/except Exception block that starts at line 126. When .agentsuite/runs/ contains any run directory with a _state.json at schema_version < 2 (common for developers who used pre-v0.9 releases), StateStore.load() raises RunStateSchemaVersionError. This exception propagates through _make_approve_fn unhandled, and Typer renders the full rich-formatted traceback regardless of --debug state.

Reproduced with: agentsuite founder approve --latest --approver me --project-slug test
Against a workspace containing a pre-v0.9 run directory, a 30-line rich traceback panel appeared unconditionally. The error message at the bottom is actionable ("Delete .agentsuite/runs/audit-n1 and re-run") but is buried under 28 lines of code-frame noise.

**Why this matters**
Every developer who carried over a .agentsuite/ directory from pre-v0.9 hits this path. The raw traceback signals "something is broken with the tool" rather than "you have a stale run directory." The --debug flag promises to control traceback visibility but only controls exceptions inside the try/except — this one escapes.

**Blast radius**
- Adjacent code: _resolve_latest_run_id is called in _make_approve_fn, reused by all 7 agents via the shared closure. All 7 approve --latest invocations share this gap.
- Shared state: StateStore.load() raises RunStateSchemaVersionError from agentsuite/kernel/state_store.py. Any code path calling .load() outside a try/except is worth auditing.
- User-facing: affects any developer who ran AgentSuite before v0.9 and kept their .agentsuite/ directory. Also any CI environment that re-uses a workspace across upgrades.
- Migration: none required — fix is wrapping the call, not changing the schema.
- Tests to update: likely no existing tests cover the approve --latest + stale-run-dir path.
- Related findings: UX-204 shares the same symptom (raw traceback) via a different code path.

**Fix path**
Move resolved_run_id = _resolve_latest_run_id(...) inside the existing try/except Exception block at line 126:

    try:
        if latest:
            resolved_run_id = _resolve_latest_run_id(agent_name_for_latest)
        elif run_id is not None:
            resolved_run_id = run_id
        else:
            typer.echo("Error: provide --run-id <id> or --latest.", err=True)
            raise typer.Exit(1)
        agent = agent_class(output_root=_output_root(), llm=_resolve_llm_for_cli())
        state = agent.approve(run_id=resolved_run_id, approver=approver, project_slug=project_slug)
    except Exception as exc:
        if _debug_mode:
            traceback.print_exc()
        else:
            typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

---

### [UX-202] — Critical — Journey — No "what next" signal after run completes at approval gate

**Evidence**
agentsuite/agents/founder/agent.py, build_cli_spec() -> run_cmd. Successful run JSON output shows run_id, primary_path, and status="approval". "approval" is an internal stage name. No stderr message, no hint text, no next-step guidance. The same pattern is copy-pasted across all 7 agents' run_cmd functions.

**Why this matters**
A developer running AgentSuite for the first time has no prior mental model for the approval gate. "status": "approval" does not communicate that action is required. Without a "what now?" message, the most likely outcome is the developer waits or assumes the run failed. This is the single highest-friction moment in the primary user journey.

**Blast radius**
- Adjacent code: all 7 run_cmd functions in agentsuite/agents/*/agent.py. A systemic pattern — one structural change to AgentCLISpec covers all seven.
- User-facing: every first-time user on every agent. 100% exposure on the happy path.
- Tests to update: none — this is additive output.
- Related findings: UX-203 (approve output missing promoted paths — the journey gap continues post-approval).

**Fix path**
Add a next_step_hint field to AgentCLISpec. Have cli.py's _register_agents() emit it to stderr after the JSON output when present. Each agent sets the hint for its domain. Example for founder:

    "Review brand-system.md and qa_report.md in the run directory, then:\n"
    "  agentsuite founder approve --latest --approver <you> --project-slug <slug>"

---

### [UX-203] — Major — Journey — Approve output missing promoted artifact paths

**Evidence**
agentsuite/cli.py, _make_approve_fn. Approval success output:

    {"run_id": "...", "status": "done", "approved_by": "me"}

The MCP founder_approve function returns ApprovalResult which includes promoted_paths. The CLI approval strips this out. After approval the user needs to know where their kernel artifacts are. "status: done" tells them it is over but not where the files landed.

**Blast radius**
- Adjacent code: _make_approve_fn in cli.py is shared by all 7 agents via the factory pattern. One fix covers all.
- User-facing: affects every user who runs the approval workflow.
- Tests to update: none known.
- Related findings: UX-202, UX-106 (v1.0.2 backlog — CLI summary JSON missing fields shown in stderr).

**Fix path**
After state = agent.approve(...), compute the kernel directory and add it to the JSON output:

    kernel_dir = _output_root() / "_kernel" / project_slug
    promoted_count = len(list(kernel_dir.rglob("*"))) if kernel_dir.exists() else 0
    typer.echo(json.dumps({
        "run_id": state.run_id,
        "status": "done",
        "approved_by": state.approved_by,
        "kernel_dir": str(_output_root() / "_kernel" / project_slug),
        "promoted_count": promoted_count,
    }, indent=2))

---

### [UX-204] — Major — Journey — USER-MANUAL install step omits required provider extra

**Evidence**
docs/USER-MANUAL.md, Step 1: pip install git+https://github.com/scottconverse/AgentSuite.git

The package installs without error but without any [anthropic], [openai], [gemini], or [ollama] extra. When the user subsequently runs agentsuite founder run, the provider resolver may succeed in checking prerequisites (e.g., the Ollama daemon is running) but then fail when instantiating the SDK with ProviderNotInstalled. This exception is not caught by _resolve_llm_for_cli (which catches only NoProviderConfigured) — the user sees a raw traceback.

The landing page and README both show correct install commands with extras. The USER-MANUAL is the document linked for non-technical users.

**Blast radius**
- Adjacent code: _resolve_llm_for_cli in cli.py needs a one-line addition to catch ProviderNotInstalled alongside NoProviderConfigured.
- User-facing: affects every USER-MANUAL reader who follows Step 1 literally.
- Migration: none.
- Tests to update: none known.
- Related findings: UX-201 (raw traceback — different path, same symptom).

**Fix path — two changes required:**

1. Fix docs/USER-MANUAL.md Step 1:

    pip install "agentsuite[anthropic] @ git+https://github.com/scottconverse/AgentSuite.git"

Add note: "The [anthropic] part installs the Anthropic Claude SDK. Replace with [openai], [gemini], or [ollama] to use a different AI provider. See Step 2b for the Ollama offline option."

2. Widen the except clause in _resolve_llm_for_cli in cli.py:

    from agentsuite.llm.base import ProviderNotInstalled
    ...
    except (NoProviderConfigured, ProviderNotInstalled) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

---

### [UX-205] — Major — Copy — trust_risk vs trust-risk inconsistency across canonical sources

**Evidence**
Three authoritative surfaces use two different forms in AGENTSUITE_ENABLED_AGENTS documentation:

| Source | Form |
|---|---|
| docs/index.html MCP snippets | trust_risk (underscore) |
| README.md MCP snippets | trust-risk (hyphen) |
| agentsuite-mcp --help env var docs | trust_risk (underscore) |
| CLI subcommand name (what users type) | trust-risk (hyphen) |

The runtime normalizes both, but a developer comparing the landing page snippet to the README sees two different values.

**Blast radius**
- Adjacent code: docs/index.html, README.md, agentsuite/mcp_server.py line 171. Three files to sync.
- User-facing: any integrator configuring MCP from one source then checking another.
- Tests to update: none.
- Related findings: none.

**Fix path**
Standardize on trust-risk (hyphen) everywhere — it matches the CLI subcommand name. Update docs/index.html and mcp_server.py to use hyphen form. Add a comment in registry.py that the normalization is intentional.

Canonical all-agents string: "founder,design,product,engineering,marketing,trust-risk,cio"

---

### [UX-206] — Major — Copy / IA — Stale "v0.8 Next Agent — Coming soon" Roadmap card on landing page

**Evidence**
docs/index.html, Roadmap section contains a single card: h3 "v0.8 Next Agent", p "Coming soon." At v1.0.1, all seven planned agents are shipped. This is the known UX-102 issue carried into the v1.0.2 backlog.

**Why this matters**
A developer sees seven shipped agents, then a Roadmap showing "v0.8 — Coming soon." This implies the project stalled. It directly contradicts the v1.0.1 header. This is the most prominent trust signal on the landing page and it is wrong.

**Blast radius**
- Adjacent code: docs/index.html only.
- User-facing: every landing page visitor.
- Migration: none.
- Tests to update: none.
- Related findings: none.

**Fix path (option A — preferred):**
Replace the stale Roadmap section:

    <h2>What's next</h2>
    <p>v1.0.1 ships all seven planned agents. Planned for v1.1: real-LLM sample output in examples,
    streaming progress during long stages, and a structured resume/retry API. See
    <a href="https://github.com/scottconverse/AgentSuite/blob/main/CHANGELOG.md">CHANGELOG.md</a>
    for the full history.</p>

**Fix path (option B):** Remove the Roadmap section until there is a genuine forward-looking item to share.

---

### [UX-207] — Minor — Copy — --quiet flag help text leaks internal audit IDs

**Evidence**
agentsuite/cli.py line 49: help="Suppress per-stage progress markers on stderr (UX-006/QA-005)."

This appears verbatim in agentsuite --help output. UX-006/QA-005 are internal audit tracking IDs meaningless to end users.

**Fix path**

    help="Suppress per-stage progress markers on stderr. Useful when scripting or piping JSON output.",

---

### [UX-208] — Minor — IA — Inconsistent list-runs availability across agents

**Evidence**
Only trust_risk and cio set has_list_runs=True and expose a list-runs subcommand. Founder, Design, Product, Engineering, and Marketing do not. A developer running agentsuite founder --help has no discoverable CLI path to list only founder runs.

**Fix path**
Set has_list_runs=True in all seven AgentCLISpec registrations. _make_list_runs_fn already handles per-agent name filtering — no additional implementation needed.

---

### [UX-209] — Minor — Copy — Generic help text on founder and design subcommands

**Evidence**
agentsuite --help shows:

    founder      Founder agent commands
    design       Design agent commands
    product      Product Agent — generates PRD, roadmap, and brief templates.

Founder and Design have generic placeholder text while the five later agents have descriptive one-liners.

**Fix path**
- Founder: "Founder Agent — generates brand system, voice guide, brief library, and prompt templates."
- Design: "Design Agent — generates visual direction briefs and brand QA scoring."

---

### [UX-210] — Minor — Copy — Sample-output README contains internal audit vocabulary and dev-report paths

**Evidence**
examples/sample-output/founder/README.md references: tests/golden/test_founder_patentforgelocal.py setup (internal test path), dev-reports/audit-AgentSuite-2026-04-29/next-sprint-watchlist.md (internal audit artifact path), and "the v1.0.0 audit Blocker that conflated mock output with real run output" (internal sprint vocabulary). A prospective adopter browsing this directory encounters dev-team vocabulary.

**Fix path**
Remove all references to internal test paths, dev-report paths, and audit IDs. Replace the v1.0.2 follow-up section with:

    ## Note on content quality

    The artifact bodies in this directory are generated by a deterministic mock LLM used for testing.
    The text is intentionally short placeholder content. To see real AI-generated output, run the
    agent yourself with a configured provider (see the command above).
    A run with Anthropic Claude Sonnet costs roughly $0.20-0.40.

---

### [UX-211] — Nit — Copy — CLI tagline uses ASCII arrow, landing page uses Unicode elsewhere

**Evidence**
cli.py line 37: "AgentSuite -- reasoning agents for vague intent -> precise artifacts"
The README uses the Unicode arrow: "vague intent -> precise artifacts" (in title) vs the page body arrow.

**Fix path**
Update to match: help="AgentSuite — reasoning agents for vague intent to precise artifacts"
The _force_utf8_io() call at the top of cli.py ensures correct rendering on Windows terminals.

---

### [UX-212] — Nit — Copy — --approver help text gives no format guidance

**Evidence**
help="Approver identity" — no indication of expected format (free-form string? email? username?).

**Fix path**

    help="Approver name or identifier stored in the run state (e.g. 'alice', 'alice@example.com')"

---

### [UX-213] — Nit — IA — No dark mode support on landing page

**Evidence**
docs/index.html uses only :root CSS custom properties with no prefers-color-scheme:dark override. Target audience (developers) has high dark mode adoption (~50%).

**Fix path**

    @media (prefers-color-scheme: dark) {
      :root {
        --fg: #e8e8e8;
        --muted: #aaa;
        --bg: #1a1a1a;
        --accent: #6b9fde;
        --code-bg: #2a2a2a;
        --border: #333;
      }
    }

---

## States audit matrix

| Surface | Default | Loading | Success | Error | Empty | Notes |
|---|---|---|---|---|---|---|
| agentsuite --help | OK | -- | OK | -- | -- | Well-formed |
| agentsuite founder run | OK | OK (stderr) | Partial (UX-202) | Partial (UX-201, UX-204) | -- | Missing next-step hint; traceback escape |
| agentsuite founder approve | OK | -- | Partial (UX-203) | Partial (UX-201) | OK | Missing promoted paths; traceback escape |
| agentsuite list-runs (global) | OK | -- | OK | -- | OK ([]) | --project-slug accepted but silently ignored |
| agentsuite founder list-runs | Missing | -- | -- | -- | -- | Command does not exist (UX-208) |
| agentsuite agents | OK | -- | OK | -- | -- | Clean |
| agentsuite-mcp --help | OK | -- | OK | -- | -- | Strong |
| Landing page | OK | -- | Partial (UX-206) | -- | -- | Stale Roadmap section |

---

## Accessibility snapshot

**CLI surfaces:**
- Keyboard navigation: N/A — terminal tools are inherently keyboard-driven.
- Color in output: [OK] prefix, no ANSI color codes. Not color-only. Pass.
- Screen reader: terminal output is screen reader accessible by default. Pass.

**Landing page (docs/index.html):**
- Keyboard navigation: all links reachable via Tab. No interactive elements beyond anchors. Pass.
- Focus visibility: browser-default focus ring. Acceptable for an information page.
- Color contrast (sampled): body text #1a1a1a on #fafafa: 16.67:1 (AAA). Muted #555 on #fafafa: 7.14:1 (AAA). Accent #2a4d8f on #fafafa: 7.87:1 (AAA). All pass WCAG 2.1 AA comfortably.
- Screen reader: semantic HTML (h1, h2, h3, header, main, footer). SVG images have alt text. Code in pre/code. Pass.
- Reduced motion: no animations or transitions. Pass.
- Touch targets: inline text links and block card elements — adequate area. Pass.
- Dark mode: not supported (Nit-213).

---

## Patterns and systemic observations

**Pattern 1: No "next step" guidance is systemic across all 7 agents.**
Every run_cmd ends by printing JSON and returning. None emit a hint. The pattern was copy-pasted uniformly when agents were added. A single next_step_hint field on AgentCLISpec would close the gap across all seven agents in one structural change.

**Pattern 2: Raw traceback escape has two independent paths in cli.py.**
UX-201 (RunStateSchemaVersionError in approve --latest) and UX-204 (ProviderNotInstalled in resolve_provider) both produce raw tracebacks via incomplete exception coverage. Both fixable in cli.py with targeted one-to-two line changes.

**Pattern 3: Inconsistent agent CLI spec richness.**
Founder and Design (first two agents shipped) have generic help text. The five later agents have descriptive one-liners. Natural sprint-sequence artifact. Fix is two string literals.

**Pattern 4: list-runs --project-slug accepts but ignores its argument.**
agentsuite list-runs --project-slug <slug> is silently non-filtering. Accepting a flag that does nothing is misleading. In v1.0.2 engineering backlog. Flagged here for completeness.

---

## Appendix: surfaces reviewed

| Surface | Location | Method |
|---|---|---|
| Top-level CLI help | agentsuite --help | Live invocation |
| Founder subcommand help | agentsuite founder {--help,run --help,approve --help} | Live invocation |
| Design, Product, Engineering, Marketing, trust-risk, CIO help | agentsuite {agent} --help and run --help | Live invocation |
| Global list-runs, agents | agentsuite list-runs --help, agentsuite agents --help | Live invocation |
| MCP server help | agentsuite-mcp --help | Live invocation |
| Error state: missing required arg | agentsuite founder run (no args) | Live invocation |
| Error state: approve no run-id | agentsuite founder approve --approver x --project-slug x | Live invocation |
| Error state: approve --latest with stale run dir | agentsuite founder approve --latest ... | Live invocation |
| CLI source | agentsuite/cli.py | Code review |
| MCP server source | agentsuite/mcp_server.py | Code review |
| Provider resolver | agentsuite/llm/resolver.py | Code review |
| Base agent / stage progress | agentsuite/kernel/base_agent.py | Code review |
| Agent registry | agentsuite/agents/registry.py | Code review |
| Founder agent spec | agentsuite/agents/founder/agent.py, mcp_tools.py | Code review |
| Landing page | docs/index.html | Code review + contrast calculation |
| User manual | docs/USER-MANUAL.md | Code review |
| Sample output README | examples/sample-output/founder/README.md | Code review |
| Contributing guide | CONTRIBUTING.md | Code review |