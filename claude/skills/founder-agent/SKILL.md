---
name: founder-agent
description: Use when the user wants to build a reusable creative-ops system for a product or company — brand system, voice guide, audience map, brief library, prompt library. Triggers when the user says "build a brand system", "set up creative ops", "founder agent", "/founder-agent", or describes a launch/positioning/brand-foundation task. Invokes the AgentSuite Founder agent via MCP.
---

# Founder Agent (AgentSuite)

This skill invokes the Founder agent from the AgentSuite MCP server. It produces 26 reusable creative-ops artifacts in 30-90 seconds and pauses for human approval before promoting them to long-lived storage.

## When to use

User wants any of:
- Brand system / brand book
- Voice and tone guide
- Audience map / persona doc
- Positioning document
- Reusable creative brief library
- Prompt library for marketing assets
- Any "I keep restating context every time I write copy" problem

## When NOT to use

- One-off content (a single landing page, single email) — overkill
- Technical product spec — that's the Product agent (v0.3+)
- Competitive intel / vendor analysis — that's the CIO agent (v0.7+)

## Steps

1. **Confirm AgentSuite MCP is configured.** Call `agentsuite_list_agents` first. If it returns `{"enabled": ["founder"]}`, proceed. If the call fails, tell the user to add the AgentSuite MCP entry to their `.mcp.json` (paste the snippet from `~/.claude/skills/founder-agent/mcp-snippet.json`).

2. **Gather inputs from the user.** Ask:
   - Business goal (one sentence)
   - Slug for `_kernel/` promotion (lowercase, hyphenated)
   - Path to inputs directory (optional — directory of READMEs, voice samples, screenshots)

3. **Invoke `founder_run`.** Pass the gathered fields plus `agent_name="founder"`, `role_domain="creative-ops"`, `user_request=<the user's original ask>`. Wait for the JSON-RPC response (30-90 s; do not poll).

4. **Show the user the result.** Display the `primary_path` (always `brand-system.md`) and the list of `open_questions`. Tell them to read `brand-system.md` and `qa_report.md`.

5. **Wait for approval signal.** When the user says "approved" or "ship it", call `founder_approve` with the same `run_id` and `project_slug`.

6. **Confirm promotion.** Echo the `promoted_paths` from the `ApprovalResult` so the user sees what landed in `_kernel/`.

## Cost expectation

A typical run costs $0.20 – $1.00 against Claude Sonnet or GPT-4o. Hard cap is $5.00 per run. If `HardCapExceeded` is raised, suggest the user reduce input size or raise `AGENTSUITE_COST_CAP_USD`.

## Failure modes

- **`NoProviderConfigured`** — tell user to set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in their shell.
- **`ConsistencyCheckFailed`** — open `consistency_report.json` and explain the mismatch.
- **`extract stage produced invalid JSON`** — re-run, usually transient.

## After approval

The Design agent (v0.2+) can read directly from `_kernel/<project_slug>/`. Until then, the artifacts are ready to feed into ChatGPT, Claude, Midjourney, etc., as context for any creative work.
