---
name: marketing-agent
description: Use when the user wants to produce a complete marketing specification bundle — campaign brief, target audience profile, messaging framework, content calendar, channel strategy, SEO keyword plan, competitive positioning, launch plan, and measurement framework — for a product, service, or brand initiative. Triggers when the user says "create a campaign brief", "write a messaging framework", "marketing strategy", "content calendar", "channel strategy", "marketing agent", "/marketing-agent", or describes a marketing artifact task. Invokes the AgentSuite Marketing agent via MCP.
---

# Marketing Agent Skill

This skill invokes the Marketing agent from the AgentSuite MCP server. It produces 9 marketing specification artifacts and 8 brief templates for ad copy, blog posts, email campaigns, influencer briefs, landing pages, press releases, quarterly reports, and social post series in 30–120 seconds, then pauses for human approval before promoting to long-lived storage.

## When to use

User wants any of:
- Campaign brief with goals, audience, and creative direction
- Target audience profile with segmentation and personas
- Messaging framework with value propositions and proof points
- Content calendar with themes, cadence, and ownership
- Channel strategy with platform mix and budget allocation
- SEO keyword plan with priority terms and content mapping
- Competitive positioning with differentiation and battle cards
- Launch plan with sequenced milestones and go-live checklist
- Measurement framework with KPIs, baselines, and reporting cadence
- Ready-to-fill brief templates for ad copy, blog posts, email campaigns, influencer briefs, landing pages, press releases, quarterly reports, or social post series

## When NOT to use

- Technical architecture — use the Engineering agent
- Visual/brand direction — use the Design agent
- Product requirements — use the Product agent
- One-off copy or text tasks — write directly or use the Founder agent

## Steps

1. **Confirm required inputs.** Ask the user for:
   - `brand_name` — the name of the brand or product (required)
   - `campaign_goal` — one sentence describing the primary marketing objective (required)
   - `target_market` — the intended audience segment (required)
   - `project_slug` — lowercase, hyphenated identifier for `_kernel/` promotion (required)

2. **Gather optional context.** Ask if the user has:
   - Existing brand docs (brand guidelines, past campaign results, tone-of-voice guide)
   - Competitor docs (competitor campaigns, positioning, market research)
   - Budget range and timeline constraints
   - Preferred channels (social, email, paid, organic, PR, etc.)
   These are optional — the agent can run without them.

3. **Set the environment.** Ensure `AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing` is set in the MCP env config. If "marketing" is not in `enabled` when you call `agentsuite_list_agents`, paste the snippet from `~/.claude/skills/marketing-agent/mcp-snippet.json` and ask the user to update their MCP config.

4. **Run the agent.** Execute:
   ```
   agentsuite marketing run --brand-name "..." --campaign-goal "..." --target-market "..."
   ```
   Optionally append `--existing-brand-docs path/to/docs`, `--competitor-docs path/to/research`, `--budget-range "..."`, `--timeline "..."`, or `--channels "..."` if the user provided those inputs.

5. **Artifacts appear in `.agentsuite/runs/{run_id}/`.** The primary output is `campaign-brief.md`. Additional artifacts: `target-audience-profile.md`, `messaging-framework.md`, `content-calendar.md`, `channel-strategy.md`, `seo-keyword-plan.md`, `competitive-positioning.md`, `launch-plan.md`, `measurement-framework.md`.

6. **Review QA scores.** Open `qa_scores.json`. If any score is < 7.0, read `revision_instructions` in that file for specific guidance on what to improve. Address revisions before approving.

7. **Approve when satisfied.** Call:
   ```
   agentsuite marketing approve --run-id {run_id} --approver {name} --project-slug {slug}
   ```
   This promotes artifacts to `_kernel/<slug>/` for use in downstream agents and sessions.

## Cost expectations

A typical run costs $0.10 – $0.50 against Claude Sonnet or GPT-4o (12 LLM calls: 9 spec artifacts + extract + consistency check + QA scoring). Cost varies with input context size. Hard cap is $5.00 per run — if `HardCapExceeded` is raised, reduce input size or raise `AGENTSUITE_COST_CAP_USD`.

## Failure modes

- **`ConsistencyCheckFailed`** — One of the 9 artifacts contradicts another on a critical dimension (e.g. channel strategy targets a demographic that differs from the target audience profile). Fix: add clearer constraints to your input, or narrow the `campaign_goal` statement before re-running.
- **`Low QA scores`** — `requires_revision=true` in the result. Open `qa_scores.json` and read `revision_instructions` for each artifact scoring below 7.0. Apply the specific changes listed before approving.
- **`NoProviderConfigured`** — Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the MCP env.
- **`extract stage produced invalid JSON`** — Transient LLM formatting error. Re-run; it typically resolves on retry.

## Rubric dimensions

QA scoring evaluates each artifact on 9 dimensions: `audience_clarity`, `message_resonance`, `channel_fit`, `metric_specificity`, `budget_realism`, `anti_vanity_metrics`, `content_depth`, `competitive_awareness`, `launch_sequencing`. Each dimension scores 0–10; artifacts with any dimension below 7.0 are flagged for revision.

## After approval

Promoted artifacts in `_kernel/<slug>/` can be fed directly into any subsequent AgentSuite agent session, shared with design teams as creative direction grounding, or loaded into an engineering session to align technical roadmap with campaign timelines. The `brief-template-library/` folder contains 8 ready-to-fill templates for ad copy, blog posts, email campaigns, influencer briefs, landing pages, press releases, quarterly reports, and social post series.
