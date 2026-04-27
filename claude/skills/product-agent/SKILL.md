---
name: product-agent
description: Use when the user wants to produce a complete product specification bundle — PRD, user story map, feature prioritization, success metrics, competitive analysis, user personas, acceptance criteria, product roadmap, and risk register — for a product, feature, or initiative. Triggers when the user says "create a PRD", "write a product spec", "product roadmap", "feature requirements", "product agent", "/product-agent", or describes a product management artifact task. Invokes the AgentSuite Product agent via MCP.
---

# Product Agent Skill

This skill invokes the Product agent from the AgentSuite MCP server. It produces 9 product specification artifacts and 8 brief templates for sprint planning, stakeholder updates, launch announcements, and related PM outputs in 30–120 seconds, then pauses for human approval before promoting to long-lived storage.

## When to use

User wants any of:
- Product Requirements Document (PRD)
- User story map with epics and stories
- Feature prioritization framework (MoSCoW, RICE, or weighted scoring)
- Success metrics and KPI definitions
- Competitive analysis and positioning
- User personas and Jobs-to-be-Done
- Acceptance criteria for a feature or epic
- Product roadmap (now / next / later or quarterly)
- Risk register with mitigation strategies
- Ready-to-fill brief templates for sprint planning, stakeholder updates, launch announcements, go-to-market summaries, executive summaries, user interview guides, A/B test plans, or retrospective reports

## When NOT to use

- Visual direction or brand identity — use the Design agent
- Marketing campaign execution — that's the Marketing agent (v0.5+)
- Technical architecture or system design — use the Founder agent first to establish brand/scope, then consult engineering
- One-off copy or text tasks — write directly or use the Founder agent

## Steps

1. **Confirm required inputs.** Ask the user for:
   - `product_name` — the name of the product or feature (required)
   - `target_users` — one sentence describing who this is for (required)
   - `core_problem` — one sentence describing the problem being solved (required)
   - `project_slug` — lowercase, hyphenated identifier for `_kernel/` promotion (required)

2. **Gather optional context.** Ask if the user has:
   - Research docs (user interviews, survey results, analytics exports)
   - Competitor docs (competitor feature lists, pricing pages, review summaries)
   These are optional — the agent can run without them.

3. **Set the environment.** Ensure `AGENTSUITE_ENABLED_AGENTS=founder,design,product` is set in the MCP env config. If "product" is not in `enabled` when you call `agentsuite_list_agents`, paste the snippet from `~/.claude/skills/product-agent/mcp-snippet.json` and ask the user to update their MCP config.

4. **Run the agent.** Execute:
   ```
   agentsuite product run --product-name "..." --target-users "..." --core-problem "..." --project-slug "..."
   ```
   Optionally append `--research-dir path/to/research` or `--competitor-dir path/to/competitors` if the user provided those files.

5. **Artifacts appear in `.agentsuite/runs/{run_id}/`.** The primary output is `product-requirements-doc.md`. Additional artifacts: `user-story-map.md`, `feature-prioritization.md`, `success-metrics.md`, `competitive-analysis.md`, `user-personas.md`, `acceptance-criteria.md`, `product-roadmap.md`, `risk-register.md`.

6. **Review QA scores.** Open `qa_scores.json`. If any score is < 7.0, read `revision_instructions` in that file for specific guidance on what to improve. Address revisions before approving.

7. **Approve when satisfied.** Call:
   ```
   agentsuite product approve --run-id {run_id} --approver {name} --project-slug {slug}
   ```
   This promotes artifacts to `_kernel/<slug>/` for use in downstream agents and sessions.

## Cost expectations

A typical run costs $0.10 – $0.50 against Claude Sonnet or GPT-4o (12 LLM calls: 9 spec artifacts + extract + consistency check + QA scoring). Cost varies with input context size. Hard cap is $5.00 per run — if `HardCapExceeded` is raised, reduce input size or raise `AGENTSUITE_COST_CAP_USD`.

## Failure modes

- **`ConsistencyCheckFailed`** — One of the 9 artifacts contradicts another on a critical dimension (e.g. target user in the PRD conflicts with personas). Fix: add clearer brand/scope constraints to your input, or narrow the `core_problem` statement before re-running.
- **`Low QA scores`** — `requires_revision=true` in the result. Open `qa_scores.json` and read `revision_instructions` for each artifact scoring below 7.0. Apply the specific changes listed before approving.
- **`NoProviderConfigured`** — Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the MCP env.
- **`extract stage produced invalid JSON`** — Transient LLM formatting error. Re-run; it typically resolves on retry.

## After approval

Promoted artifacts in `_kernel/<slug>/` can be fed directly into any subsequent AgentSuite agent session, shared with engineering as grounding context, or loaded into a design session to align visual direction with product intent. The `brief-template-library/` folder contains 8 ready-to-fill templates for sprint planning, stakeholder updates, launch announcements, go-to-market summaries, executive summaries, user interview guides, A/B test plans, and retrospective reports.
