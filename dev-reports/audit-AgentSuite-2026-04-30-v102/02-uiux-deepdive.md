# UI/UX Deep-Dive — AgentSuite v1.0.2-dev (Post-Sprint Audit)

**Role:** Senior UI/UX Designer  
**Date:** 2026-04-30  
**Scope:** CLI UX, MCP developer experience, error messages, hint copy  

Note: AgentSuite has no browser UI. "User experience" here means the CLI operator and MCP tool caller — a developer wiring AgentSuite into Codex/Claude Code. Every error message, progress line, and hint is evaluated from that developer's perspective.

---

## What's Working Well

- **Stage progress output is excellent.** `[OK] intake complete  (2.3s, $0.0012)` — clear, machine-readable pattern, actionable time and cost at a glance. Silenceable via `--quiet`. This is the right behavior.
- **UX-202 approve hint is a genuine UX win.** After every `run`, stderr now says:
  ```
  Next: agentsuite founder approve --latest --approver <your-name> --project-slug <slug>
  ```
  This removes the "now what?" moment that CLI first-timers hit. Good.
- **UX-201 approve --latest no longer shows a traceback** for schema-mismatch runs. Clean error instead of `RuntimeError: _state.json at ...`. Confirmed by test `test_approve_latest_handles_schema_version_error`.
- **UX-204 ProviderNotInstalled gives an actionable install command.** "pip install 'agentsuite[anthropic] @ git+...'" tells the developer exactly what to run. Good.
- **Help text is concise and non-jargon.** `agentsuite --help` shows all 7 agents with one-line descriptions. Sub-help for each command is clear. `agentsuite founder run --help` exposes all options without clutter.

---

## Findings

### MAJOR — UX-301: Next-step hint uses literal `<angle-bracket>` placeholders

**Category:** Copy / Usability  
**Severity:** Major  
**Evidence:** After a `founder run`, stderr emits:
```
Next: agentsuite founder approve --latest --approver <your-name> --project-slug <slug>
```

A developer who copy-pastes this gets:
```
Error: Got unexpected extra argument (<your-name>)
```

The `<>` convention is not universally understood as "fill this in." Angle brackets are sometimes interpreted as shell redirection. The hint is already doing the right thing by using `--latest` (so no run-id needed), but the unfilled placeholders undermine the usability gain.

**Blast radius:** All 7 agents emit a similar hint. Every first-time user who copy-pastes gets an immediate CLI error as their first interaction with `approve`.

**Fix path:** Either:
1. Use `YOUR_NAME` and `YOUR_SLUG` as uppercase placeholder convention (visually distinct, not shell-sensitive), or
2. Emit two lines — the generic template plus a concrete example using the actual `--project-slug` value from the run input (this is known at emit time since it's a CLI argument).

---

### MINOR — UX-302: `agentsuite migrate` ghost command in error messages

**Category:** Consistency  
**Severity:** Minor  
**Evidence:** `mcp_server.py:133` warning says `upgrade with \`agentsuite migrate\``. This command does not exist. A developer reading the warning, copying the command, and running it gets "Error: No such command 'migrate'". This is a friction point at exactly the moment when the user is already dealing with a schema version problem.

**Fix path:** Change message to "delete the run directory and re-run" or implement a stub `migrate` that prints the manual steps.

---

### MINOR — UX-303: No empty-state copy for list-runs when runs exist but none match filter

**Category:** Empty state  
**Severity:** Minor  
**Evidence:** `agentsuite founder list-runs` when runs exist but none are for the `founder` agent returns `[]`. This is technically correct but gives no context — a developer might not know if the command is broken or if there genuinely are no founder runs. The global `agentsuite list-runs` would show all runs, which would clarify, but the per-agent version is silent.

**Fix path:** Emit a JSON object with an explanatory note, or print a stderr note: "No runs found for agent 'founder'. Run 'agentsuite list-runs' to see all runs."

---

### NIT — UX-401: `--quiet` is a global flag but its help text appears only in the global `--help`

**Category:** Discoverability  
**Severity:** Nit  
**Evidence:** `agentsuite founder run --help` does not show `--quiet`. A developer looking for how to suppress progress output while on a specific agent's run command won't find it. Only `agentsuite --help` shows it.

**Behavior note:** The flag does work correctly when set — `agentsuite --quiet founder run ...`. The issue is discoverability, not function.

**Fix path:** Add `--quiet` to each agent's `run` subcommand, or add a note to the global help: "Use 'agentsuite --quiet <agent> run ...' to suppress progress output."

---

## Severity Counts

| Severity | Count |
|----------|-------|
| Blocker | 0 |
| Critical | 0 |
| Major | 1 |
| Minor | 2 |
| Nit | 1 |

---

## Summary

The UX tier is measurably better in v1.0.2 than v1.0.1 — the approve hint, stage progress, and provider error message are all genuine improvements. The major remaining issue (UX-301) is that the hint was added correctly as a mechanic but the copy was left as a template rather than completed. It's the last mile that makes the difference between a feature that delights and one that frustrates.
