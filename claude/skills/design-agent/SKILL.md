---
name: design-agent
description: Use when the user wants to produce a complete design specification bundle — visual direction, design brief, mood board, brand rules, image generation prompts, accessibility audit, and asset acceptance checklist — for a campaign, product, or brand. Triggers when the user says "design a campaign", "create design specs", "design agent", "/design-agent", or describes a visual direction / brand identity / asset brief task. Invokes the AgentSuite Design agent via MCP.
---

# Design Agent (AgentSuite)

This skill invokes the Design agent from the AgentSuite MCP server. It produces 9 design specification artifacts and 8 production-ready asset brief templates in 30–120 seconds and pauses for human approval before promoting to long-lived storage.

## When to use

User wants any of:
- Visual direction document
- Design brief for a campaign
- Mood board specification
- Brand rules extraction from existing materials
- Image generation prompts for AI art tools (Midjourney, Stable Diffusion, DALL·E)
- Asset acceptance checklist
- Accessibility audit template (WCAG AA)
- Ready-to-fill brief templates for banner ads, social graphics, landing heroes, email headers, deck slides, print flyers, video thumbnails, or icon sets

## When NOT to use

- One-off copy or text tasks — use the Founder agent or write directly
- Technical product specification — that's the Product agent (v0.3+)
- Marketing campaign execution — that's the Marketing agent (v0.5+)
- Brand system / voice guide from scratch — run the Founder agent first, then the Design agent reads from `_kernel/`

## Steps

1. **Confirm AgentSuite MCP is configured.** Call `agentsuite_list_agents`. If "design" is not in `enabled`, tell the user to set `AGENTSUITE_ENABLED_AGENTS=founder,design` in their MCP env config (paste the snippet from `~/.claude/skills/design-agent/mcp-snippet.json`).

2. **Gather inputs from the user.** Ask:
   - Target audience (one sentence)
   - Campaign goal (one sentence)
   - Output channel: web / social / email / print / video / deck / other
   - Project slug (lowercase, hyphenated) — for `_kernel/` promotion
   - Path to brand materials directory (optional — PDFs, images, markdown docs)

3. **Invoke `design_run`.** Pass the gathered fields plus `agent_name="design"`, `role_domain="design-ops"`. Wait for the JSON-RPC response (30–120 s; do not poll).

4. **Show the user the result.** Display the `primary_path` (always `visual-direction.md`) and the list of `open_questions`. Tell them to read `visual-direction.md` and `qa_report.md`.

5. **Wait for approval signal.** When the user says "approved" or "ship it", call `design_approve` with the same `run_id` and `project_slug`.

6. **Confirm promotion.** Echo the `promoted_paths` from the `ApprovalResult` so the user sees what landed in `_kernel/`.

## Cost expectation

A typical run costs $0.30 – $1.50 against Claude Sonnet or GPT-4o (9 LLM calls for spec artifacts + 1 consistency check + 1 QA score). Hard cap is $5.00 per run. If `HardCapExceeded` is raised, reduce input size or raise `AGENTSUITE_COST_CAP_USD`.

## Failure modes

- **`NoProviderConfigured`** — tell user to set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.
- **`ConsistencyCheckFailed`** — open `consistency_report.json` and explain the mismatch between artifacts.
- **`extract stage produced invalid JSON`** — re-run, usually transient.
- **`QA score below threshold`** — `requires_revision=true` in result; open `qa_report.md` and `revision-instructions.md` for specific changes.

## After approval

The promoted artifacts in `_kernel/<slug>/` can be fed directly into any image generation tool, design tool (Figma, Canva), or LLM session as grounding context. The `brief-template-library/` folder contains 8 ready-to-fill brief templates for specific asset types.
