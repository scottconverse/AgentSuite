---
name: cio-agent
description: Use when the user wants to produce a complete CIO artifact bundle — IT strategy, technology roadmap, vendor portfolio, digital transformation plan, IT governance framework, enterprise architecture, budget allocation model, workforce development plan, and IT risk appetite statement — for an organization. Triggers when the user says "create an IT strategy", "technology roadmap", "IT governance", "digital transformation", "CIO agent", "/cio-agent", or describes a CIO or IT leadership artifact task. Invokes the AgentSuite CIO agent via MCP.
---

# CIO Agent Skill

This skill invokes the CIO agent from the AgentSuite MCP server. It produces 9 IT and technology specification artifacts and 8 brief templates for board technology briefings, IT steering committee agendas, vendor review summaries, project portfolio status updates, digital initiative proposals, IT investment cases, technology modernization pitches, and quarterly IT reviews in 30–120 seconds, then pauses for human approval before promoting to long-lived storage.

## When to use

User wants any of:
- IT strategy with vision, principles, and strategic objectives
- Technology roadmap with phased initiatives and milestones
- Vendor portfolio with rationalization criteria and contract optimization
- Digital transformation plan with change management and adoption strategy
- IT governance framework with decision rights, policies, and accountability
- Enterprise architecture with current-state, target-state, and transition plan
- Budget allocation model with investment categories, prioritization, and ROI framework
- Workforce development plan with skills gaps, training programs, and talent pipeline
- IT risk appetite statement with risk categories, tolerances, and escalation thresholds
- Ready-to-fill brief templates for board technology briefings, IT steering committee agendas, vendor review summaries, project portfolio status updates, digital initiative proposals, IT investment cases, technology modernization pitches, or quarterly IT reviews

## When NOT to use

- Trust and risk artifacts — use the Trust/Risk agent
- Product requirements — use the Product agent
- Visual/brand direction — use the Design agent
- One-off copy or text tasks — write directly or use the Founder agent

## Steps

1. **Confirm required inputs.** Ask the user for:
   - `organization_name` — the name of the organization (required)
   - `strategic_priorities` — one to three sentences describing the organization's top strategic priorities (required)
   - `it_maturity_level` — current IT maturity (e.g. foundational, developing, advanced, optimizing) (required)
   - `project_slug` — lowercase, hyphenated identifier for `_kernel/` promotion (required)

2. **Gather optional context.** Ask if the user has:
   - Budget context (total IT spend, investment envelopes, fiscal constraints)
   - Digital initiatives (current or planned transformation programs)
   - Regulatory environment (applicable compliance requirements such as SOX, HIPAA, PCI-DSS, GDPR)
   - Existing IT documentation directory (prior strategies, architecture diagrams, vendor contracts)
   These are optional — the agent can run without them.

3. **Set the environment.** Ensure `AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio` is set in the MCP env config. If "cio" is not in `enabled` when you call `agentsuite_list_agents`, paste the snippet from `~/.claude/skills/cio-agent/mcp-snippet.json` and ask the user to update their MCP config.

4. **Run the agent.** Execute:
   ```
   agentsuite cio run --organization-name "..." --strategic-priorities "..." --it-maturity-level "..."
   ```
   Optionally append `--budget-context "..."`, `--digital-initiatives "..."`, `--regulatory-environment "..."`, or `--it-docs-dir path/to/docs` if the user provided those inputs.

5. **Artifacts appear in `.agentsuite/runs/{run_id}/`.** The primary output is `it-strategy.md`. Additional artifacts: `technology-roadmap.md`, `vendor-portfolio.md`, `digital-transformation-plan.md`, `it-governance-framework.md`, `enterprise-architecture.md`, `budget-allocation-model.md`, `workforce-development-plan.md`, `it-risk-appetite-statement.md`.

6. **Review QA scores.** Open `qa_scores.json`. If any score is < 7.0, read `revision_instructions` in that file for specific guidance on what to improve. Address revisions before approving.

7. **Approve when satisfied.** Call:
   ```
   agentsuite cio approve --run-id {run_id} --approver {name} --project-slug {slug}
   ```
   This promotes artifacts to `_kernel/<slug>/` for use in downstream agents and sessions.

## Cost expectations

A typical run costs $0.10 – $0.50 against Claude Sonnet or GPT-4o (12 LLM calls: 9 spec artifacts + extract + consistency check + QA scoring). Cost varies with input context size. Hard cap is $5.00 per run — if `HardCapExceeded` is raised, reduce input size or raise `AGENTSUITE_COST_CAP_USD`.

## Failure modes

- **`ConsistencyCheckFailed`** — One of the 9 artifacts contradicts another on a critical dimension (e.g. the technology roadmap references an initiative not funded in the budget allocation model, or the enterprise architecture targets a capability not addressed in the workforce development plan). Fix: add clearer constraints to your input, or narrow the `strategic_priorities` statement before re-running.
- **`Low QA scores`** — `requires_revision=true` in the result. Open `qa_scores.json` and read `revision_instructions` for each artifact scoring below 7.0. Apply the specific changes listed before approving.
- **`NoProviderConfigured`** — Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the MCP env.
- **`extract stage produced invalid JSON`** — Transient LLM formatting error. Re-run; it typically resolves on retry.

## Rubric dimensions

QA scoring evaluates each artifact on 9 dimensions: `strategy_clarity`, `roadmap_feasibility`, `vendor_rationalization_depth`, `transformation_change_management`, `governance_accountability`, `architecture_completeness`, `budget_prioritization_rigor`, `workforce_skills_alignment`, `risk_appetite_specificity`. Each dimension scores 0–10; artifacts with any dimension below 7.0 are flagged for revision.

## After approval

Promoted artifacts in `_kernel/<slug>/` can be fed directly into any subsequent AgentSuite agent session, shared with technology and business teams as IT planning grounding, or loaded into a product session to align roadmap decisions with enterprise IT direction. The `brief-template-library/` folder contains 8 ready-to-fill templates for board technology briefings, IT steering committee agendas, vendor review summaries, project portfolio status updates, digital initiative proposals, IT investment cases, technology modernization pitches, and quarterly IT reviews.
