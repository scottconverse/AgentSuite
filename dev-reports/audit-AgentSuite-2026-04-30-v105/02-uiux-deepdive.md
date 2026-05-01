# UI/UX Deep-Dive — AgentSuite v1.0.5

**Audit date:** 2026-04-30
**Role:** Senior UI/UX Designer
**Scope audited:** CLI (`agentsuite/cli.py`), MCP server interface (`agentsuite/mcp_server.py`), output artifact structure (`.agentsuite/`), developer SDK ergonomics (`agentsuite/kernel/base_agent.py`, `agentsuite/kernel/artifacts.py`, all agent `mcp_tools.py` modules), GitHub landing page (`docs/index.html`)
**Auditor posture:** Balanced

---

## TL;DR

AgentSuite's CLI ergonomics are solid for a developer tool at this stage: consistent subcommand structure, error messages that name the problem, and a useful `--debug` escape hatch. The strongest dimension is the MCP interface clarity — the tool naming convention (`agentsuite_<agent>_<verb>`) is systematic and discoverable. The weakest dimension is the landing page, which shows version v1.0.1 while the package ships v1.0.5 and contains a Roadmap section advertising a "v0.8 Next Agent: Coming soon" that shipped six releases ago, directly undermining trust. Two other systemic issues deserve priority attention: the `RevisionRequired` error from the approval gate has no recovery path documented or signaled anywhere in the developer-facing surface (CLI, MCP, landing page), and the `soft_warn` cost signal is tracked in memory but never surfaced to the user — a silent budget breach that could cause real-money surprises.

---

## Severity roll-up (UX)

| Severity | Count |
|---|---|
| Blocker  | 0 |
| Critical | 2 |
| Major    | 4 |
| Minor    | 3 |
| Nit      | 2 |

---

## What's working

- **Consistent `--latest` flag on approve** — every agent's approve subcommand supports `--latest`, sparing the developer from having to copy-paste a run ID. Small ergonomic win with high frequency of use.
- **Next-step hint on every `run` completion** — after each agent run, a hint emitted to stderr tells the user exactly what command to run next (e.g., `Next: agentsuite founder approve --latest --approver YOUR_NAME --project-slug YOUR_SLUG`). This is the kind of "what now?" guidance most CLI tools omit. All seven agents implement it.
- **`--quiet` / `AGENTSUITE_QUIET` flag** — the stage-progress lines can be suppressed cleanly for shell piping. The implementation correctly routes progress to stderr and JSON to stdout, which is the right separation. Most developer tools get this wrong.
- **`agentsuite-mcp --help` output** — the MCP binary's custom `--help` handler is a genuine improvement over the silent exit-0 behavior. The environment variable table is scannable and directly useful to an integrator looking at the README.
- **`--debug` traceback flag** — opt-in full traceback is exactly right. The default is clean; the escape hatch exists when needed.
- **Systematic MCP tool naming** — `agentsuite_<agent>_<verb>` (e.g., `agentsuite_founder_run`, `agentsuite_engineering_approve`) is immediately parseable in a tool picker. No ambiguity about which agent a tool belongs to.
- **Content-addressed artifact SHA tracking** — the SHA-256 on every `ArtifactRef` is a professional touch that lets integrators detect drift without re-reading files.

---

## What couldn't be assessed

- **Live run output** — no live agent run was executed. The artifact UX of a completed run (directory layout, file naming, human-readability of individual artifacts like `brand-system.md`, `qa_report.md`) was assessed from source code structure only, not from actual output.
- **MCP tool picker rendering in Codex / Claude Code** — the tool descriptions (Python docstrings on the registered callables) cannot be assessed without running the MCP server live and observing how the descriptions appear in a tool picker UI.
- **`AGENTSUITE_EXPOSE_STAGES` advanced stage tools** — the five `_stage_*` tools are gated behind an env var. Their UX could not be assessed without enabling them.
- **Soft-warn cost signal propagation** — the `CostTracker.warned` flag is tracked in memory and serialized to `cost_summary.json`, but whether it surfaces to the user during a live run (e.g., a stderr line) requires tracing through all stage handlers, which was not fully traced.

---

## First impressions

Arriving at `docs/index.html` cold, three things register within five seconds:

1. The headline and lede do the job: "Seven role-specific reasoning agents that turn vague intent into precise operating artifacts." A developer knows immediately what this is.
2. The install command is above the fold. Good.
3. The version badge in the `<h1>` says `v1.0.1`. The package `__version__.py` says `1.0.5`. That mismatch signals a project that ships faster than it updates its front door.

Arriving at the CLI for the first time (running `agentsuite --help`) the experience is coherent: seven agent subcommands, a clean description, global flags documented. The top-level help text reads "AgentSuite -- reasoning agents for vague intent -> precise artifacts" — close to a good tagline but the double-hyphen and ASCII arrow feel unpolished compared to the landing page's em-dash treatment.

---

## Journey walkthroughs

### Journey 1: Integrator arrives at landing page → installs → runs founder agent → approves

**Step 1 — Landing page.** Developer lands on `docs/index.html`. The "What it does" section is dense but technically accurate. The "Shipped agents" grid correctly lists all seven agents. However the Roadmap section still shows `v0.8 Next Agent: Coming soon` — five versions behind. This actively undermines trust: if the roadmap is stale, what else is stale?

**Step 2 — Install.** Install command is correct and copy-pasteable. No issues.

**Step 3 — First run.** Developer runs `agentsuite founder run --business-goal "..." --project-slug myproject`. The agent walks five stages. Each stage emits a progress line: `[OK] intake complete  (0.2s, $0.0000)`. The format is functional. Minor friction: the bracketed `[OK]` prefix reads as a log-level marker rather than a human-friendly "done" signal. A first-time developer might not know whether `[OK]` means success or something that warranted verification.

**Step 4 — After run.** The run completes and JSON is emitted to stdout: `{"run_id": "...", "primary_path": "...", "status": "approval"}`. The status value is the raw stage name `approval`, which is technically correct but reads oddly to a human. A developer seeing `"status": "approval"` might wonder if this is an internal state or an instruction. The CLI then emits the next-step hint to stderr. If the user is piping stdout, they see the hint; if they're capturing both, the hint is mixed in. This works but the separation is invisible to first-time users.

**Step 5 — Approve.** Developer runs the approve command. If QA flagged the run for revision (`requires_revision=True`), the `ApprovalGate.approve()` raises `RevisionRequired`. The error message is `"QA flagged this run as requiring revision. Address the QA feedback and re-run before approving."` This is accurate but not actionable: it doesn't tell the developer where to find the QA feedback (which file?), what "re-run" means in the context of an approval-stage run (does this mean `resume`? From what stage?), or what the `--run-id` of the run is. The developer is stuck at a dead end.

### Journey 2: MCP integrator wires AgentSuite into Codex → calls a tool → handles failure

**Step 1 — Configuration.** The MCP config snippets in the landing page and README are copy-pasteable and correct. Good.

**Step 2 — Tool discovery.** An integrator running `agentsuite_list_agents` gets `{"enabled": [...], "all_registered": [...]}`. This is the right first tool to call. The naming is clear.

**Step 3 — Run a tool.** The integrator calls `agentsuite_founder_run(request)`. If the request is missing required fields, the error surfaces as a Pydantic `ValidationError` propagated up through FastMCP. The integrator sees a raw Pydantic error trace rather than a structured MCP error object. Whether FastMCP wraps this gracefully depends on the MCP SDK version — this couldn't be assessed without a live run.

**Step 4 — Status check.** The integrator calls `agentsuite_founder_get_status(run_id)`. If `run_id` uses a pre-v0.9 schema, `ValueError` is raised with message: `"run_id '...' uses a pre-v0.9 schema — delete the run directory and re-run."` This is actionable.

**Step 5 — Approval.** The integrator calls `agentsuite_founder_approve(run_id, approver, project_slug)`. If the run requires revision, the MCP tool receives `RevisionRequired` from `ApprovalGate.approve()`, which is not caught in `founder_approve()` — it propagates as an unhandled exception to the MCP caller. No structured error; no guidance on what to call next.

---

## Findings

### [UX-001] — Critical — Copy / State — Landing page version is four releases stale and roadmap is a ghost

**Evidence**
`docs/index.html` line 49: `<h1>AgentSuite <span class="v">v1.0.1</span></h1>`. Package `__version__.py`: `"1.0.5"`. Roadmap section (lines 118–121): `<div class="card"><h3>v0.8 Next Agent</h3><p>Coming soon.</p></div>` — this shipped as Engineering at v0.4, Marketing at v0.5, Trust/Risk at v0.6, and CIO at v0.7. The entire content of the "Coming soon" card shipped four-plus versions ago.

**Why this matters**
A developer evaluating AgentSuite arrives at the landing page and sees v1.0.1 with a roadmap item that's already in the "Shipped agents" grid above. The cognitive dissonance is immediate: either the project is disorganized, or this page is unmaintained. Both interpretations reduce trust before the developer has even read the install instructions. This is the project's storefront — trust damage at the front door affects conversion.

**Blast radius**
- Adjacent code/pages: `README.md` shows `v1.0.3` in its header badge (not v1.0.5 either — partial sync). The README and landing page are independently maintained and drift at each release.
- User-facing: any developer evaluating AgentSuite from the GitHub Pages URL.
- Migration: none — this is copy/content only.
- Tests to update: none known.
- Related findings: UX-002 (version drift in README too).

**Fix path**
Update `docs/index.html` line 49 to `v1.0.5`. Remove the Roadmap section entirely or replace it with the actual next milestone. If a roadmap section is retained, it should name only items that are not yet shipped. Recommended replacement:

```html
<h2>Roadmap</h2>
<div class="grid">
  <div class="card"><h3>Multi-agent pipelines</h3><p>Chain agents end-to-end: Founder → Design → Engineering in a single run.</p></div>
</div>
```

Automate version injection into `docs/index.html` via the release script so this drift cannot recur.

---

### [UX-002] — Critical — Journey / State — `RevisionRequired` approval failure has no recovery path for the developer

**Evidence**
`agentsuite/kernel/approval.py` lines 44–48: `ApprovalGate.approve()` raises `RevisionRequired("QA flagged this run as requiring revision. Address the QA feedback and re-run before approving.")`. In the CLI path (`cli.py` `_make_approve_fn`), this exception is caught by the bare `except Exception as exc` block at line 142 and re-emitted as `Error: {exc}` with exit 1. The developer sees:

```
Error: QA flagged this run as requiring revision. Address the QA feedback and re-run before approving.
```

This message tells the developer *what happened* but not: (a) which file contains the QA report, (b) what "re-run" means operationally (`resume`? from `qa` stage? a full new run?), or (c) what command to execute next. In the MCP path (`founder_mcp_tools.py` `founder_approve()`), `RevisionRequired` is **not caught at all** — it propagates as an unhandled exception to the MCP caller.

**Why this matters**
This is the highest-friction point in the core developer workflow. A developer whose run fails QA hits a dead end. They know something is wrong but do not know what to do next. In a CLI tool aimed at developers integrating via MCP into Codex/Claude Code, a dead end at the approval gate — after spending 5 stages and real money — is a support-call event, not a recoverable error.

**Blast radius**
- Adjacent code: `agentsuite/agents/*/mcp_tools.py` — all seven agents' `_approve` MCP tool functions lack `RevisionRequired` handling. Fix needed in all seven files.
- User-facing: any developer whose QA stage returns `requires_revision=True` via any agent, via either CLI or MCP path.
- Migration: none.
- Tests to update: check that MCP tool tests cover the `RevisionRequired` path.
- Related findings: UX-005 (soft-warn cost signal not surfaced).

**Fix path**
Three changes:

1. In `cli.py`, add a dedicated `except RevisionRequired` handler before the bare `except Exception` in `_make_approve_fn` that emits a structured error with explicit next-step:
```python
except RevisionRequired:
    typer.echo(
        "Error: QA flagged this run as needing revision.\n"
        f"  Review:  {_output_root() / 'runs' / resolved_run_id / 'qa_report.md'}\n"
        f"  Re-run:  agentsuite {agent_name_for_latest} run [original flags] --run-id {resolved_run_id} --force\n"
        "  Or resume from QA stage:  agentsuite {agent_name_for_latest} resume --run-id {resolved_run_id} --stage qa",
        err=True,
    )
    raise typer.Exit(1)
```

2. In each agent's `_approve` MCP tool function, add a `try/except RevisionRequired` that returns a structured error dict (or raises `ValueError` with the path to the QA report included in the message) rather than letting the exception propagate raw.

3. In the next-step hint on run completion, add a note that if QA requires revision, `qa_report.md` in the run directory contains the feedback.

---

### [UX-003] — Major — Copy — Stage progress format is opaque to first-time users

**Evidence**
`agentsuite/kernel/base_agent.py` `_emit_stage_progress()` (lines 23–43): emits lines of the form `[OK] intake complete  (0.2s, $0.0000)`. The `[OK]` prefix is borrowed from log-level conventions (`[INFO]`, `[WARN]`, `[ERROR]`) but it communicates nothing useful here beyond "not an error." The double-space before the parenthetical is inconsistent. The cost format `$0.0000` shows four decimal places which displays as `$0.0000` for fast no-LLM stages — creates cognitive load ("did it cost anything?").

**Why this matters**
For a first-time developer watching a 5-stage pipeline that may take 30–120 seconds, the progress output is their only signal that the system is alive and working. Opaque or ambiguous signals increase anxiety and reduce trust in the tool. Stage 1 (intake) often costs $0.0000 (no LLM call), so users see `$0.0000` repeated and wonder whether the cost tracking is broken.

**Blast radius**
- Adjacent code: `_emit_stage_progress` is called once per stage in `base_agent.py`'s `_drive()` loop. A single-point change propagates to all seven agents.
- User-facing: every CLI user of every agent.
- Migration: none. Output format change.
- Tests to update: any tests asserting the exact stderr output format.
- Related findings: UX-005.

**Fix path**
Replace `[OK]` with a checkmark-free but friendlier prefix. Drop the double-space. Omit cost for $0.0000 stages (or display it as "no LLM cost"). Recommended format:

```python
line = f"  stage {stage} done ({elapsed_s:.1f}s"
if total_usd > 0:
    line += f", ${total_usd:.4f}"
line += ")"
```

Output would read: `  stage intake done (0.2s)` and `  stage extract done (8.4s, $0.0023)`.

---

### [UX-004] — Major — Copy / IA — CLI `run` JSON output uses internal stage name as `status`

**Evidence**
`agentsuite/agents/founder/agent.py` `run_cmd()` lines 101–105:
```python
typer.echo(json.dumps({
    "run_id": state.run_id,
    "primary_path": str(...),
    "status": state.stage,   # emits "approval" when run reaches the gate
}, indent=2))
```

The `status` field emits the raw internal stage value (`"approval"`) when the run completes successfully. An integrator capturing this JSON sees `"status": "approval"` and must know the internal state machine to interpret it. Compare to the MCP model `RunResult.status` which uses the developer-friendly literal `"awaiting_approval"`. The CLI and MCP surface use different status vocabularies for the same event.

**Why this matters**
Developers integrating the CLI output in shell scripts or CI pipelines parse the JSON. A `status` of `"approval"` is ambiguous: does it mean "approve it" (instruction) or "in approval" (state)? The MCP model solved this with `"awaiting_approval"` — the CLI should match. Cross-surface inconsistency forces developers to hold two mental models simultaneously.

**Blast radius**
- Adjacent code: `agentsuite/agents/*/agent.py` — all seven agents' `run_cmd` functions emit `"status": state.stage`. All seven need the same fix.
- Shared state: `AgentCLISpec.primary_artifact` is per-agent; no shared impact.
- User-facing: any shell script or CI integration parsing CLI JSON output.
- Migration: breaking change for existing shell scripts relying on `"status": "approval"`. Should be noted in CHANGELOG.
- Tests to update: CLI output format tests for all seven agents.
- Related findings: none.

**Fix path**
In each agent's `run_cmd`, translate `state.stage` to the user-facing status before emitting. A shared helper:

```python
def _stage_to_status(stage: str) -> str:
    if stage == "approval":
        return "awaiting_approval"
    return stage
```

Apply in all seven `run_cmd` functions. Update CHANGELOG to note the output contract change.

---

### [UX-005] — Major — State — Soft-warn cost threshold latches silently; no user-visible signal

**Evidence**
`agentsuite/kernel/cost.py` `CostTracker.add()` (lines 80–82): when accumulated cost exceeds `soft_warn_usd` (default $1.00), `self.warned = True` latches. The flag is serialized to `cost_summary.json` as `"cap_warned": true`. However, `_drive()` in `base_agent.py` never checks `cost_tracker.warned` and never emits a warning to stderr. The warning flag exists in the data model but is never acted on.

**Why this matters**
The $1.00 soft-warn threshold exists precisely to alert developers who are approaching the $5.00 hard cap. If a run is burning $0.40 per stage and the developer does not look at `cost_summary.json` after each stage, they will not know they have crossed the soft warn until the hard cap fires at $5.00 with `HardCapExceeded`. For a developer running seven agents across multiple sessions, this is a real money-surprise risk. The infrastructure to handle this exists; the user-visible output does not.

**Blast radius**
- Adjacent code: `base_agent.py` `_drive()` loop — single location to add the warning emit.
- Shared state: `CostTracker.warned` flag already exists; no model changes needed.
- User-facing: any developer running a multi-stage or expensive agent.
- Migration: none.
- Tests to update: tests covering `_drive()` behavior when cost crosses soft-warn threshold.
- Related findings: UX-003 (stage progress output).

**Fix path**
In `_drive()` after `cost_tracker.add()` (after each stage), check `cost_tracker.warned` and emit once to stderr:

```python
if cost_tracker.warned and not _warned_emitted:
    typer.echo(
        f"[WARN] Cost ${state.cost_so_far.usd:.4f} has crossed the soft-warn "
        f"threshold of ${cost_tracker.cap.soft_warn_usd:.2f}. "
        f"Hard cap: ${cost_tracker.cap.hard_kill_usd:.2f}. "
        "Set AGENTSUITE_COST_CAP_USD to adjust.",
        err=True,
    )
    _warned_emitted = True
```

---

### [UX-006] — Minor — IA — `list_runs` `project_slug` parameter is accepted but ignored across all seven `*_list_runs` MCP tools

**Evidence**
`agentsuite/agents/founder/mcp_tools.py` line 117: `def founder_list_runs(project_slug: str | None = None) -> list[RunSummary]:`. The function accepts `project_slug` but the parameter is never used — runs are filtered only by `state.agent == "founder"`. The same pattern exists in all seven agents' `_list_runs` functions. The CLI `list-runs` subcommand also accepts `--project-slug` (line 222 of `cli.py`) and similarly ignores it.

**Why this matters**
A developer calling `agentsuite_founder_list_runs(project_slug="patentforge")` expecting to filter by project will receive all Founder runs regardless of project. This is a silent contract lie — a parameter that appears to do something but does nothing. Developers who rely on this for workspace management will get wrong results without an error.

**Blast radius**
- Adjacent code: all seven `_list_runs` MCP tool functions. All seven CLI `list-runs` subcommands.
- User-facing: developers using `project_slug` filter in list operations.
- Migration: none — fixing this to actually filter is additive behavior.
- Tests to update: tests for list-runs filtering by project_slug (likely absent).
- Related findings: none.

**Fix path**
Either implement the filter (compare `project_slug` against a stored value in `RunState` — currently `RunState` does not persist `project_slug` on the run itself, only at approval time) or remove the parameter from the signature and update documentation. If implementing the filter is deferred, at minimum add a `# TODO: project_slug filter not yet implemented` and raise a `NotImplementedError` or emit a warning when a non-None value is supplied.

---

### [UX-007] — Minor — Copy — `agentsuite --help` uses ASCII `->` while landing page uses Unicode em-dash

**Evidence**
`agentsuite/cli.py` line 38–40: `app = typer.Typer(help="AgentSuite -- reasoning agents for vague intent -> precise artifacts")`. The landing page tagline uses "→" (Unicode arrow). README uses "→" in its header blockquote. The CLI uses `->`.

**Why this matters**
Minor tone inconsistency. A developer who reads the README and then runs `agentsuite --help` notices the mismatch at a subconscious level. Not blocking, but the CLI is the developer's daily touchpoint.

**Fix path**
Change the CLI help string to: `"AgentSuite — reasoning agents for vague intent → precise artifacts"`. The `_force_utf8_io()` call at module load ensures UTF-8 output on Windows. This is already in place for this exact reason.

---

### [UX-008] — Minor — IA — `agentsuite-mcp --help` env var documentation omits `AGENTSUITE_COST_CAP_USD`

**Evidence**
`agentsuite/mcp_server.py` `main()` help text (lines 176–188): lists five env vars (`AGENTSUITE_ENABLED_AGENTS`, `AGENTSUITE_OUTPUT_DIR`, `AGENTSUITE_LLM_PROVIDER`, `AGENTSUITE_EXPOSE_STAGES`, `AGENTSUITE_QUIET`). `AGENTSUITE_COST_CAP_USD` is absent. The CLI `agentsuite --help` does not document it either (it is only documented in the README).

**Why this matters**
An integrator reading only the `--help` output to configure their MCP server has no way to discover cost cap configuration. For a tool that charges real money per run, this is a meaningful omission.

**Fix path**
Add to the help text:
```
  AGENTSUITE_COST_CAP_USD      Hard kill cap per run in USD (default: 5.00).
                               Soft warn fires at 20% of this value.
```

---

### [UX-009] — Nit — Copy — `[OK]` prefix inconsistency: `RunStateSchemaVersionError` skip messages use different format

**Evidence**
`cli.py` lines 168–169: `typer.echo(f"Skipping pre-v0.9 run dir {d.name}", err=True)`. This emits to stderr without any prefix, while stage progress uses `[OK] ...`. The formatting language is inconsistent across the two stderr streams.

**Fix path**
Prefix with `[SKIP]` or `[WARN]`: `f"[WARN] Skipping pre-v0.9 run dir {d.name} — delete it and re-run to include it in results."`.

---

### [UX-010] — Nit — Copy — `agentsuite agents` JSON response uses `all_registered` key with underscore; other keys use camelCase-adjacent hyphen-less style

**Evidence**
`cli.py` lines 252–255: `json.dumps({"enabled": reg.enabled_names(), "all_registered": reg.registered_names()})`. The `all_registered` key name is fine but slightly inconsistent with MCP tool output which uses `all_registered` too — this is actually consistent. This is a genuine nit about naming style: `all_registered` implies a distinction from some subset; `registered` (without `all_`) would be clearer.

**Fix path**
Rename `all_registered` to `registered` in both the CLI and the MCP `agentsuite_list_agents` tool output. Document as a minor API change in CHANGELOG.

---

## States audit matrix

| Surface | Default | Loading (progress) | Empty | Error | Partial | Notes |
|---|---|---|---|---|---|---|
| CLI `run` | ✓ | ✓ (stage progress lines) | N/A | ✓ (basic) | — | RevisionRequired error lacks recovery path (UX-002) |
| CLI `approve` | ✓ | N/A | ✓ (no runs dir) | Partial | — | RevisionRequired not handled distinctly (UX-002) |
| CLI `list-runs` | ✓ | N/A | ✓ (empty JSON array) | Partial | — | Schema-version skip logged but not counted |
| CLI `agents` | ✓ | N/A | N/A | N/A | — | Clean |
| MCP `*_run` | ✓ | ✓ (stage progress via stderr) | N/A | Partial | — | Pydantic ValidationError may surface raw to caller |
| MCP `*_approve` | ✓ | N/A | — | Partial | — | RevisionRequired uncaught (UX-002) |
| MCP `*_list_runs` | ✓ | N/A | ✓ (empty list) | N/A | — | project_slug filter silently ignored (UX-006) |
| MCP `agentsuite_cost_report` | ✓ | N/A | ✓ (`{"runs":[],"total_usd":0.0}`) | Partial | — | Schema-version runs silently skipped |
| Landing page (`docs/index.html`) | Partial | N/A | N/A | N/A | — | Stale version + stale roadmap (UX-001) |

---

## Accessibility snapshot

This is a CLI tool and developer-facing landing page. Traditional UI accessibility criteria apply only to the landing page.

**Landing page (`docs/index.html`)**
- Keyboard navigation: the page contains no interactive elements beyond `<a>` tags. Tab order follows document order, which is logical. No issues.
- Focus visibility: browser default focus rings apply to links. No custom focus suppression detected.
- Color contrast: primary text `#1a1a1a` on `#fafafa` background: approximately 18:1 — passes WCAG AAA. Muted text `#555` on `#fafafa`: approximately 7:1 — passes AA for normal text. Accent `#2a4d8f` on white card background: approximately 8:1 — passes AA. No contrast failures detected.
- Screen reader labeling: `<img>` tags for SVG screenshots have `alt` attributes (e.g., `alt="agentsuite founder run end to end"`). Adequate.
- Reduced motion: no animations on the page. Not applicable.
- Touch target size: link targets are inline text links — may be below 44px on mobile. Low impact given developer audience.
- Mobile responsive: the `@media (max-width: 600px)` breakpoint collapses the agent grid to a single column. `pre` blocks use `overflow-x: auto`. No clipping observed. Adequate.

**CLI accessibility:** not applicable (terminal output, no visual hierarchy concerns beyond the copy issues noted above).

---

## Patterns and systemic observations

### Pattern 1: Seven agents, seven copies of the same `mcp_tools.py` skeleton

Every agent's `mcp_tools.py` is a near-identical copy of the founder's, differing only in agent name, input schema type, and primary artifact filename. The `_summary_from_state`, `_now_id`, and `_result_from_state` helpers are duplicated verbatim across all seven files. This is not a UX issue per se, but it means that any fix to the MCP tool UX (e.g., UX-002's `RevisionRequired` handling) must be applied identically in seven places. The blast radius of every tool-facing UX change is 7x. This is a structural maintenance burden that will produce drift.

**Recommendation:** Extract `_summary_from_state`, `_now_id`, `_result_from_state`, and the `RevisionRequired` handler into `agentsuite/agents/_common.py` and import them in each agent's `mcp_tools.py`. This is a refactor, not a UX fix, but it is the prerequisite for keeping the UX consistent as agents are added.

### Pattern 2: Version not injected at build time

`docs/index.html` has a hard-coded version string. `README.md` has a hard-coded version in the header. Neither is injected from `agentsuite/__version__.py` during the release process. Every release requires a manual multi-file version update, and at v1.0.5 the landing page is already four versions behind. This will recur.

**Recommendation:** Add a `scripts/update-version-in-docs.sh` step to `scripts/verify-release.sh` that `sed`-replaces the version string in `docs/index.html` and validates that it matches `agentsuite/__version__.py`. Make the verify script fail if they diverge.

### Pattern 3: `project_slug` accepted but unused in all list operations

All seven `_list_runs` MCP tools and the global CLI `list-runs` accept `project_slug` but ignore it (UX-006). This silent parameter contract is a systemic pattern, not a one-off oversight. The fix must be applied consistently or the parameter should be removed from the API surface entirely until it is implemented.

---

## Appendix: surfaces reviewed

| Surface | Files read |
|---|---|
| CLI | `agentsuite/cli.py`, `agentsuite/agents/founder/agent.py`, `agentsuite/agents/engineering/agent.py`, `agentsuite/agents/cio/agent.py` |
| MCP server | `agentsuite/mcp_server.py`, `agentsuite/agents/founder/mcp_tools.py`, `agentsuite/agents/engineering/mcp_tools.py` |
| SDK kernel | `agentsuite/kernel/base_agent.py`, `agentsuite/kernel/artifacts.py`, `agentsuite/kernel/schema.py`, `agentsuite/kernel/state_store.py`, `agentsuite/kernel/approval.py`, `agentsuite/kernel/cost.py` |
| Agent inputs | `agentsuite/agents/founder/input_schema.py`, `agentsuite/agents/engineering/input_schema.py`, `agentsuite/agents/_common.py` |
| Provider resolution | `agentsuite/llm/resolver.py` |
| Registry | `agentsuite/agents/registry.py` |
| MCP models | `agentsuite/mcp_models.py` |
| Landing page | `docs/index.html` |
| README | `README.md` (first 100 lines) |
| Pipeline stage | `agentsuite/agents/founder/stages/intake.py` |
