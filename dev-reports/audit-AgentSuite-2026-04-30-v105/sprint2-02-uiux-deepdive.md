# UI/UX Deep-Dive — Sprint 2 — AgentSuite v1.0.7

**Audit date:** 2026-04-30
**Role:** Senior UI/UX Designer
**Scope audited:** Sprint 2 UX-relevant changes — UX-004, UX-006, QA-005, ENG-005/UX-003, ENG-002. CLI + MCP tool interface across all 7 agents. "User experience" = developer experience of using AgentSuite via CLI and MCP.
**Auditor posture:** Balanced

---

## TL;DR

Sprint 2 delivers a clean, meaningful improvement to the developer experience: the `$0.0000` noise is gone, the approval-gate status is now clearly labeled, empty list-runs returns a parseable empty array, and the UnknownAgent error tells developers exactly what to type next. The strongest dimension is cross-agent consistency — all 7 agents received the same changes in lockstep, with no divergence between them. The weakest dimension is the zero-result state for `project_slug` filtering in `list_runs`: when a developer passes a slug that has no matching runs, they receive a silent empty array with no indication of whether the slug is wrong or simply has no history, leaving them without a path forward.

---

## Severity roll-up (UX)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 0 |
| Major | 2 |
| Minor | 4 |
| Nit | 3 |

---

## What's working

- **`awaiting_approval` status label is consistently applied across all 7 agents.** Every agent's `_stage_to_status()` function (founder/agent.py:68–72, design/agent.py:73–77, product/agent.py:73–77, engineering/agent.py:73–77, marketing/agent.py:73–77, trust_risk/agent.py:77–81, cio/agent.py:77–81) maps `"approval"` → `"awaiting_approval"` using identical code. The CLI JSON output and the MCP `RunResult` both surface this status. Zero drift across the 7-agent surface.

- **`$0.0000` suppression is implemented correctly.** `base_agent.py:38` gates cost display with `if total_usd > 0` before appending the cost string. The progress line for Ollama runs reads `[OK] intake complete  (0.2s)` rather than `[OK] intake complete  (0.2s, $0.0000)`. This is the right call — noise suppressed, meaningful data preserved.

- **`project_slug` filter is implemented consistently across all 7 MCP `list_runs` tools.** The `getattr(state.inputs, "project_slug", None)` pattern (e.g., founder/mcp_tools.py:143, design/mcp_tools.py:139, product/mcp_tools.py:139) safely handles agents whose input schema does not have a `project_slug` field, returning all runs rather than crashing. This is a good defensive choice.

- **The cost warning is appropriately routed to stderr.** `base_agent.py:185–190` writes the warning to `sys.stderr`, keeping `stdout` clean for the JSON payload that shell scripts pipe. The threshold is discoverable — it fires at the soft cap (default $1.00, configurable via `AGENTSUITE_COST_CAP_USD`).

- **The UnknownAgent error message names the valid agents.** Both the CLI (`cli.py:282–285`) and the MCP server (`mcp_server.py:79–81`) include the complete enumerated list of valid agent names. This is a direct, actionable error.

- **The `RevisionRequired` CLI error message is the best error copy in the codebase.** `cli.py:155–163` gives the developer: the problem, the file to read, the command to re-run with the exact flag syntax, and the command for re-approval. Every error message in the product should aspire to this level of completeness.

- **`--quiet` flag is documented and wired.** `cli.py:52–60` exposes `--quiet/-q` as a global option with a clear help string and exports `AGENTSUITE_QUIET=1` to the kernel. The docstring comment referencing UX-006/QA-005 ties it to the sprint ticket, which is helpful.

- **`agentsuite-mcp --help` produces human-readable output.** `mcp_server.py:174–198` intercepts `--help` before FastMCP takes over stdin, returning a formatted usage block. This is exactly what a developer wiring an MCP server into Codex will type first.

---

## What couldn't be assessed

- **Runtime behavior of `_emit_stage_progress`** — the format of the progress line was read from source; actual terminal rendering on Windows cp1252 vs UTF-8 was not verified live. The `chr(10)` newline append is correct but unusual.
- **MCP tool schema documentation** — FastMCP generates its tool descriptions from Python docstrings. The filter behavior of `project_slug` in `list_runs` depends entirely on whether FastMCP surfaces the parameter docstring in its schema. The docstring content of the `list_runs` functions was confirmed to be minimal (no parameter docs). Whether the MCP client sees the parameter at all could not be verified without a running server.
- **Threshold at which cost warning fires for CIO/trust_risk** — these agents have richer toolsets. Live execution with a provider was not available to confirm the warning fires at the first stage-completion event after `soft_warn_usd` is crossed, rather than only once at the very end.
- **`RunSummary.started_at`** — the field is present in the model but the `list_runs` implementations do not include `started_at` in the CLI's JSON output (`cli.py:198–204`), only in the MCP result. Could not verify whether the CLI omission is intentional or an oversight without a running agent.

---

## First impressions

A developer integrating AgentSuite for the first time types `agentsuite founder run --business-goal "..."`. During the 2–5 minute run, they now see meaningful progress lines on stderr (`[OK] intake complete  (1.2s, $0.0432)`) while the JSON result lands cleanly on stdout. When the run finishes, the JSON shows `"status": "awaiting_approval"` — clear, unambiguous, ready to branch on. The next-step hint fires on stderr: `Next: agentsuite founder approve --latest --approver YOUR_NAME --project-slug YOUR_SLUG`. The developer knows exactly what to do.

The first failure mode a developer hits is typing a wrong agent name. They now get: `Unknown agent name. Valid agents: founder, design, product, engineering, marketing, trust_risk, cio` — actionable on first read. Sprint 2 has substantially improved this first-run experience.

---

## Journey walkthroughs

### Journey: Developer integrates via MCP — lists runs filtered by project

1. Developer calls `agentsuite_founder_list_runs(project_slug="my-project")`.
2. If runs exist for that slug, they receive a populated list. Clear.
3. If no runs exist for that slug — they receive `[]`. **This is the gap.** An empty array is indistinguishable from "wrong slug" vs. "no runs yet for this project." The developer has no feedback.
4. The developer may iterate: try `agentsuite_founder_list_runs()` to see all runs, then manually scan for their slug. This friction is avoidable.

### Journey: Developer encounters the cost warning

1. Run is in progress, spending accumulates.
2. At the first stage-completion after spend crosses $1.00 (soft cap), stderr receives: `Warning: cost cap approaching. Current spend: $X.XXXX`.
3. The warning says "approaching" but the developer doesn't know the hard cap without reading docs. There's no `(cap: $5.00)` in the message. They don't know how much headroom they have.

### Journey: Developer with AGENTSUITE_LLM_PROVIDER_FACTORY set outside pytest

1. Developer copies a test environment variable into their shell config.
2. First CLI run produces: `RuntimeError: AGENTSUITE_LLM_PROVIDER_FACTORY is set outside of a pytest run. This environment variable executes arbitrary Python and must only be used in tests. Unset it before running AgentSuite.`
3. Clear. Actionable. Tells them exactly what to unset.

---

## Findings

> **Finding ID prefix:** `UX-`
> **Categories:** Copy / State / IA / Pattern / Journey

---

### [UX-A01] — Major — State — Empty list-runs response is silent when project_slug filter yields no matches

**Evidence**

All 7 `list_runs` MCP tools (e.g., `founder/mcp_tools.py:127–153`, `design/mcp_tools.py:123–149`). When `project_slug` is provided and no runs match, the function returns `[]`. The same empty list is returned when `project_slug` is omitted and there are genuinely no runs. The developer has no way to distinguish:

- Slug `"my-project"` exists but has no runs → `[]`
- Slug `"my-projects"` (typo) has no runs → `[]`
- No runs exist at all in the output directory → `[]`

**Why this matters**

A developer integrating via MCP will call `list_runs(project_slug="my-project")` to check run history before deciding whether to trigger a new run. An empty response without any indication of whether the slug matched anything will cause repeated re-runs or confused debugging sessions. This is the most common "first week with the tool" failure mode for a new integrator.

**Blast radius**
- Adjacent code: all 7 `list_runs` implementations share this exact pattern. The fix applies to `founder/mcp_tools.py`, `design/mcp_tools.py`, `product/mcp_tools.py`, `engineering/mcp_tools.py`, `marketing/mcp_tools.py`, `trust_risk/mcp_tools.py`, `cio/mcp_tools.py` — all lines implementing the slug filter.
- Shared state: the `RunSummary` model (`mcp_models.py`) would need no changes; this is purely a response envelope addition.
- User-facing: every developer who uses slug-filtered listing hits this gap.
- Migration: no stored-data change. The addition is additive to the returned list/dict shape.
- Tests to update: any test that asserts `list_runs(project_slug=X)` returns a bare `[]` for no-match. These tests are passing correct behavior — they'd need to be updated to match the new shape.
- Related findings: UX-A02 (CLI `list-runs` command has the same issue at the CLI surface).

**Fix path**

Change the return type from `list[RunSummary]` to a dict envelope when a filter is active, so the developer gets context:

```python
# Current (silent):
return []  # when project_slug filter matches nothing

# Recommended:
# Option A: always return a structured envelope when project_slug is passed
return {
    "runs": [],
    "filter": {"project_slug": project_slug},
    "matched": 0,
    "note": "No runs found for project_slug='my-project'. Pass project_slug=None to list all runs."
}
```

Alternatively (less change): keep the `list[RunSummary]` return type but add a metadata header field to `RunSummary` list wrappers. However, Option A is cleaner for MCP consumers that parse JSON.

A lower-effort option if the return type can't change: add an MCP-level tool `agentsuite_founder_project_exists(project_slug: str) -> bool` that lets the developer verify the slug before filtering. Still, Option A is the right call.

---

### [UX-A02] — Major — State — CLI `list-runs` at agent level omits `started_at` field; CLI top-level `list-runs` omits `started_at` too; both are inconsistent with MCP shape

**Evidence**

`cli.py:198–204` — the per-agent `list_runs_cmd` builds a dict with keys: `run_id`, `agent`, `stage`, `cost_usd`. Missing: `started_at`. Compare to `mcp_models.py:35–43` `RunSummary`, which includes `started_at`. The top-level `cli.py:264–270` has the same omission.

The MCP `list_runs` tools build `RunSummary` objects (which include `started_at`), so a developer using MCP sees a different field set than a developer using the CLI.

**Why this matters**

A developer automating approval workflows — checking "has a run for this project started in the last hour?" — has to use a different JSON path depending on whether they're on CLI or MCP. This creates silent integration bugs when developers copy CLI output shapes into MCP integrations or vice versa. The shape contract should be identical across both surfaces.

**Blast radius**
- Adjacent code: `cli.py` functions `_make_list_runs_fn` (line 179) and the top-level `list_runs_cmd` (line 247).
- User-facing: developers scripting around run age/ordering are affected.
- Tests to update: any tests that assert CLI list-runs output shape.
- Related findings: UX-A01 (same `list_runs` surface with empty-state gap).

**Fix path**

Add `started_at` to the CLI output dicts at both call sites in `cli.py`:

```python
# _make_list_runs_fn (line 198):
out.append({
    "run_id": state.run_id,
    "agent": state.agent,
    "stage": state.stage,
    "started_at": state.started_at.isoformat() if state.started_at else None,
    "cost_usd": state.cost_so_far.usd,
})

# top-level list_runs_cmd (line 264):
# same addition
```

---

### [UX-A03] — Minor — Copy — Cost warning message omits the hard cap value, leaving developers without actionable budget context

**Evidence**

`base_agent.py:185–186`:
```python
sys.stderr.write(
    f"Warning: cost cap approaching. "
    f"Current spend: ${cost_tracker.total.usd:.4f}\n"
)
```

The message says "cap approaching" but does not say what the cap is, how much headroom remains, or what will happen when the cap is hit.

**Why this matters**

A developer seeing `Warning: cost cap approaching. Current spend: $1.0032` doesn't know: Is the hard cap $2.00? $5.00? $10.00? How many more stages will run before termination? Will they lose partial output? Without this context, some developers will kill the run preemptively (losing work), while others will ignore the warning (not realizing the hard kill is imminent).

**Fix path**

Expand the warning to include cap context and headroom:

```python
sys.stderr.write(
    f"Warning: cost cap approaching — ${cost_tracker.total.usd:.4f} spent, "
    f"${cost_tracker.cap.soft_warn_usd:.2f} soft-warn threshold crossed. "
    f"Hard kill at ${cost_tracker.cap.hard_kill_usd:.2f}. "
    f"Set AGENTSUITE_COST_CAP_USD=N to raise the limit.\n"
)
```

---

### [UX-A04] — Minor — Copy — `_stage_to_status()` is duplicated verbatim across all 7 agent files; if a new stage needs remapping it will be missed in some agents

**Evidence**

Identical 4-line function at:
- `founder/agent.py:68–72`
- `design/agent.py:73–77`
- `product/agent.py:73–77`
- `engineering/agent.py:73–77`
- `marketing/agent.py:73–77`
- `trust_risk/agent.py:77–81`
- `cio/agent.py:77–81`

All copies are currently identical, so there is no divergence today. But the function has no single source of truth.

**Why this matters**

This is the exact pattern that produces user-facing inconsistency when the next sprint adds a new stage. One agent file gets updated, others don't, and developers integrating against MCP see `"paused"` from one agent and `"paused_for_human"` from another. The problem hasn't happened yet, but the architecture is one PR away from it.

**Fix path**

Move `_stage_to_status()` to `agentsuite/kernel/base_agent.py` as a module-level function (it has no instance state). Each agent module imports it from there. One authoritative implementation, zero drift risk.

```python
# kernel/base_agent.py (add once):
def stage_to_status(stage: str) -> str:
    """Map internal stage names to user-facing status values."""
    if stage == "approval":
        return "awaiting_approval"
    return stage
```

```python
# each agent module (replace the local copy):
from agentsuite.kernel.base_agent import stage_to_status
# ...
"status": stage_to_status(state.stage),
```

---

### [UX-A05] — Minor — IA — `project_slug` is optional in 5 of 7 agents' CLI `run` commands but required in `product/agent.py:89`

**Evidence**

`product/agent.py:89`:
```python
project_slug: str = typer.Option(..., help="Project slug for output dir"),
```

Compare to all 6 other agents where `project_slug` is optional:
```python
project_slug: str | None = typer.Option(None, help="Stable slug for `_kernel/` promotion"),
```

The product agent's `run` command requires `--project-slug` at invocation time. All other agents let the developer omit it at run time and supply it at approval time.

**Why this matters**

A developer learning the tool from one agent's workflow will hit a confusing `Missing option '--project-slug'` error on the first Product agent invocation with no explanation of why this agent is different. The inconsistency violates the "consistent interaction model across all 7 agents" principle the Sprint 2 work is clearly aiming for.

**Fix path**

Change `product/agent.py:89` to match the other 6 agents:

```python
project_slug: str | None = typer.Option(None, help="Stable slug for `_kernel/` promotion"),
```

If the Product agent genuinely requires the slug at run time (not just approval time), add a guard in `run_cmd` that raises a clear error with explanation:

```python
if project_slug is None:
    typer.echo(
        "Error: --project-slug is required for the Product agent. "
        "It determines the output path for the generated PRD.\n"
        "Example: agentsuite product run --product-name MyApp "
        "--target-users ... --core-problem ... --project-slug my-app",
        err=True,
    )
    raise typer.Exit(1)
```

---

### [UX-A06] — Minor — Copy — `_make_list_runs_fn` generates a CLI subcommand with no `--project-slug` filter, unlike the MCP `list_runs` tools which do have the filter

**Evidence**

`cli.py:179–205` — `_make_list_runs_fn` takes only `agent_name: str` and the inner `list_runs_cmd` takes no arguments. The MCP equivalent (`founder_list_runs`, `design_list_runs`, etc.) accepts `project_slug: str | None = None`.

The CLI user cannot filter by slug at the per-agent level. They can only filter at the top-level `agentsuite list-runs` command (`cli.py:247`), which also accepts `--project-slug` but lists across all agents.

**Why this matters**

A developer scripting `agentsuite founder list-runs` to check their project's run history has no way to narrow the output without grepping the JSON. This is a minor friction, but it creates a CLI/MCP feature gap that will confuse developers who move between both surfaces.

**Fix path**

Add `project_slug: Optional[str] = typer.Option(None)` to the inner `list_runs_cmd` in `_make_list_runs_fn` and filter using the same `state.inputs.project_slug` check that the MCP tools use.

---

### [UX-A07] — Nit — Copy — `_summary_from_state` in MCP tools still shows `cost=$0.0000` in the `summary` string field even when cost is zero

**Evidence**

All 7 `mcp_tools.py` files, e.g. `founder/mcp_tools.py:37–44`:
```python
def _summary_from_state(state: RunState) -> str:
    parts = [f"agent={state.agent}", f"stage={state.stage}"]
    ...
    parts.append(f"cost=${state.cost_so_far.usd:.4f}")
    return "; ".join(parts)
```

`ENG-005/UX-003` suppressed `$0.0000` from the progress line in `base_agent.py:38`, but did not apply the same suppression to this summary string. An Ollama run still produces `summary: "agent=founder; stage=approval; cost=$0.0000"`.

**Why this matters**

Minor inconsistency in the developer-visible output. The sprint's intent was to eliminate the zero-cost noise; this location was missed.

**Fix path**

Apply the same conditional in `_summary_from_state`:
```python
cost_usd = state.cost_so_far.usd
if cost_usd > 0:
    parts.append(f"cost=${cost_usd:.4f}")
```

Apply to all 7 `mcp_tools.py` files. Or, better: move `_summary_from_state` to a shared module (it is currently identically duplicated across all 7 files).

---

### [UX-A08] — Nit — Copy — `RunResult` docstring still says "founder_run / founder_resume / founder_get_status" — it's now a shared model for all 7 agents

**Evidence**

`mcp_models.py:11`:
```python
"""Result envelope returned by founder_run / founder_resume / founder_get_status."""
```

**Fix path**

```python
"""Result envelope returned by each agent's run / resume / get_status MCP tools."""
```

---

### [UX-A09] — Nit — IA — `trust_risk` vs `trust-risk` naming inconsistency across CLI and MCP

**Evidence**

- CLI command: `agentsuite trust-risk ...` (kebab-case, `trust_risk/agent.py:136` `cli_name="trust-risk"`)
- MCP tool names: `agentsuite_trust_risk_run`, `agentsuite_trust_risk_list_runs` (snake_case with underscore)
- `agent_name` field: `"trust_risk"` (underscore)
- Error messages in `cli.py:283` and `mcp_server.py:81`: `"trust_risk"` (underscore)

The CLI uses a hyphen, everything else uses an underscore. A developer reading CLI error copy (`Valid agents: ... trust_risk ...`) will try `agentsuite trust_risk run` and get a "No such command" error, because the CLI command is `trust-risk`.

**Why this matters**

This predates Sprint 2 and is a pre-existing inconsistency. Sprint 2 propagated it consistently across the error messages, which is better than before, but the root inconsistency remains.

**Fix path**

Either update the error messages in `cli.py:283` and `mcp_server.py:81` to read `trust-risk` (matching the CLI command), or add an alias so both work. The simplest fix:

```python
# cli.py:282–285 — change to use hyphen to match the CLI command:
"Unknown agent name. Valid agents: "
"founder, design, product, engineering, marketing, trust-risk, cio",
```

```python
# mcp_server.py:81 — here underscore is correct (MCP tool names use underscore)
# so add a clarifying comment or keep as-is. But the message should differentiate:
f"AGENTSUITE_ENABLED_AGENTS contains an unknown agent name: {e}. "
"Valid agents (use underscore for env var): "
"founder, design, product, engineering, marketing, trust_risk, cio"
```

---

## States audit matrix

| Surface | Default | Success-populated | Empty/zero-results | Error | Notes |
|---|---|---|---|---|---|
| CLI run command (7 agents) | ✓ | ✓ | n/a | ✓ | Error paths cover: run exists+force, RevisionRequired, generic exception |
| CLI approve | ✓ | ✓ | n/a | ✓ | RevisionRequired path is excellent |
| CLI list-runs (per-agent) | ✓ | ✓ | ✓ (empty `[]`) | partial | No project_slug filter — UX-A06 |
| CLI list-runs (top-level) | ✓ | ✓ | ✓ (empty `[]`) | partial | project_slug filter present but no null-slug feedback — UX-A01 |
| MCP list_runs (7 agents) | ✓ | ✓ | ✗ | partial | Silent empty on slug miss — UX-A01 |
| MCP run/resume | ✓ | ✓ | n/a | ✓ | |
| MCP approve (RevisionRequired) | ✓ | ✓ | n/a | ✓ | Error dict is clear and actionable |
| Progress stderr (all agents) | ✓ | ✓ | ✓ ($0 suppressed) | ✓ | Cost warning missing cap context — UX-A03 |

---

## Accessibility snapshot

This is a developer CLI tool. Classic accessibility criteria (color contrast, touch targets, screen readers) do not apply. Developer-experience equivalents:

- **Machine parseability:** stdout is clean JSON on all success paths; stderr carries human-readable progress. This separation is correct and consistent. No cases were found where JSON and prose are mixed on the same stream.
- **Exit codes:** success paths exit 0; error paths use `raise typer.Exit(1)`. Consistent across all 7 agents.
- **Color usage:** no ANSI color codes in any output path, which is correct for a tool that must pipe cleanly in CI environments.
- **Screen-reader equivalent (plain-text help):** `agentsuite --help`, `agentsuite founder --help`, and `agentsuite-mcp --help` all produce readable plain text. No raw exception tracebacks escape to the user unless `--debug` is passed.

---

## Patterns and systemic observations

### Pattern 1: Copy-paste duplication of helper functions across all 7 agent modules

`_stage_to_status()`, `_now_id()`, `_summary_from_state()`, and `_result_from_state()` are duplicated verbatim (with only the `primary` artifact path varying) across all 7 `mcp_tools.py` files. This is the copy-paste propagation anti-pattern in its most legible form. Sprint 2 fixed `_stage_to_status` in all 7 places simultaneously, which worked — but required touching 7 files for a 4-line change. The next sprint that needs to change `_summary_from_state` (e.g., to add the zero-cost suppression from UX-A07) will face the same 7-file change. The fix is to promote these to shared functions in a `_common.py` or `kernel/` module. This is an architectural concern (ENG scope), but its primary user-facing consequence is UX drift when one of the copies gets a fix that others don't.

### Pattern 2: `list_runs` empty-state contract is undefined

There is no documentation (function docstring, README, or MCP tool description) stating what a developer should expect when calling `list_runs` with a `project_slug` filter that has no matches. The behavior is correct by one reading (return everything matching, return nothing if nothing matches), but the developer mental model will expect a "not found" signal. This is a UX contract gap.

### Pattern 3: CLI and MCP output shapes are close but not identical

The CLI `list-runs` output omits `started_at` compared to the MCP `RunSummary`. The MCP `_summary_from_state()` string includes the zero-cost display that the progress line suppresses. These small divergences compound over time into a surface where developers can't rely on one shape to predict the other.

---

## Appendix: surfaces reviewed

| Surface | Files |
|---|---|
| CLI entry point | `agentsuite/cli.py` |
| MCP server entry point | `agentsuite/mcp_server.py` |
| Kernel pipeline driver | `agentsuite/kernel/base_agent.py` |
| Cost accounting | `agentsuite/kernel/cost.py` |
| MCP output models | `agentsuite/mcp_models.py` |
| All 7 agent.py files | `founder`, `design`, `product`, `engineering`, `marketing`, `trust_risk`, `cio` |
| All 7 mcp_tools.py files | same 7 agents |
