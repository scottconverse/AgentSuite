---
name: engineering-agent
description: Use when the user wants to produce a complete engineering specification bundle — architecture decision record, system design, API spec, data model, security review, deployment plan, runbook, tech-debt register, and performance requirements — for a system, service, or technical initiative. Triggers when the user says "create an ADR", "write a system design", "architecture decision record", "API spec", "engineering spec", "engineering agent", "/engineering-agent", or describes an engineering artifact task. Invokes the AgentSuite Engineering agent via MCP.
---

# Engineering Agent Skill

This skill invokes the Engineering agent from the AgentSuite MCP server. It produces 9 engineering specification artifacts and 8 brief templates for sprint tickets, code review checklists, incident reports, and related engineering outputs in 30–120 seconds, then pauses for human approval before promoting to long-lived storage.

## When to use

User wants any of:
- Architecture Decision Record (ADR)
- System design document with component breakdown
- API specification (REST, GraphQL, or RPC)
- Data model with schema and relationships
- Security review with threat model and mitigations
- Deployment plan with rollout strategy
- Runbook for operational procedures
- Tech-debt register with prioritized items
- Performance requirements and SLO definitions
- Ready-to-fill brief templates for sprint tickets, code review checklists, incident reports, capacity plans, on-call handoffs, release checklists, postmortems, or vendor evaluations

## When NOT to use

- Product planning — use the Product agent
- Visual direction — use the Design agent
- One-off code or text tasks — write directly or use the Founder agent

## Steps

1. **Confirm required inputs.** Ask the user for:
   - `system_name` — the name of the system or service (required)
   - `problem_domain` — one sentence describing the technical problem being solved (required)
   - `tech_stack` — the languages, frameworks, and infrastructure involved (required)
   - `scale_requirements` — expected load, data volume, and availability targets (required)
   - `project_slug` — lowercase, hyphenated identifier for `_kernel/` promotion (required)

2. **Gather optional context.** Ask if the user has:
   - Existing codebase docs (architecture diagrams, API references, README files)
   - ADR history (prior decisions that constrain the current design)
   - Incident history (past failures that inform reliability requirements)
   These are optional — the agent can run without them.

3. **Set the environment.** Ensure `AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering` is set in the MCP env config. If "engineering" is not in `enabled` when you call `agentsuite_list_agents`, paste the snippet from `~/.claude/skills/engineering-agent/mcp-snippet.json` and ask the user to update their MCP config.

4. **Run the agent.** Execute:
   ```
   agentsuite engineering run --system-name "..." --problem-domain "..." --tech-stack "..." --scale-requirements "..."
   ```
   Optionally append `--existing-codebase-docs path/to/docs`, `--adr-history path/to/adrs`, or `--incident-history path/to/incidents` if the user provided those files.

5. **Artifacts appear in `.agentsuite/runs/{run_id}/`.** The primary output is `architecture-decision-record.md`. Additional artifacts: `system-design.md`, `api-spec.md`, `data-model.md`, `security-review.md`, `deployment-plan.md`, `runbook.md`, `tech-debt-register.md`, `performance-requirements.md`.

6. **Review QA scores.** Open `qa_scores.json`. If any score is < 7.0, read `revision_instructions` in that file for specific guidance on what to improve. Address revisions before approving.

7. **Approve when satisfied.** Call:
   ```
   agentsuite engineering approve --run-id {run_id} --approver {name} --project-slug {slug}
   ```
   This promotes artifacts to `_kernel/<slug>/` for use in downstream agents and sessions.

## Cost expectations

A typical run costs $0.10 – $0.50 against Claude Sonnet or GPT-4o (12 LLM calls: 9 spec artifacts + extract + consistency check + QA scoring). Cost varies with input context size. Hard cap is $5.00 per run — if `HardCapExceeded` is raised, reduce input size or raise `AGENTSUITE_COST_CAP_USD`.

## Failure modes

- **`ConsistencyCheckFailed`** — One of the 9 artifacts contradicts another on a critical dimension (e.g. scale requirements in the system design conflict with the performance requirements). Fix: add clearer constraints to your input, or narrow the `problem_domain` statement before re-running.
- **`Low QA scores`** — `requires_revision=true` in the result. Open `qa_scores.json` and read `revision_instructions` for each artifact scoring below 7.0. Apply the specific changes listed before approving.
- **`NoProviderConfigured`** — Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the MCP env.
- **`extract stage produced invalid JSON`** — Transient LLM formatting error. Re-run; it typically resolves on retry.

## Rubric dimensions

QA scoring evaluates each artifact on 9 dimensions: `implementation_specificity`, `testability`, `security_posture`, `scalability_awareness`, `dependency_hygiene`, `anti_overengineering`, `operational_completeness`, `decision_traceability`, `api_contract_clarity`. Each dimension scores 0–10; artifacts with any dimension below 7.0 are flagged for revision.

## After approval

Promoted artifacts in `_kernel/<slug>/` can be fed directly into any subsequent AgentSuite agent session, shared with product teams as grounding context, or loaded into a design session to align visual direction with engineering constraints. The `brief-template-library/` folder contains 8 ready-to-fill templates for sprint tickets, code review checklists, incident reports, capacity plans, on-call handoffs, release checklists, postmortems, and vendor evaluations.
