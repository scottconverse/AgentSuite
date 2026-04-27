---
name: trust-risk-agent
description: Use when the user wants to produce a complete trust and risk artifact bundle — threat model, risk register, control framework, incident response plan, compliance matrix, vendor risk assessment, security policy, audit readiness report, and residual risk acceptance — for a product, service, or organization. Triggers when the user says "create a threat model", "risk assessment", "security policy", "compliance matrix", "trust risk agent", "/trust-risk-agent", or describes a trust or risk artifact task. Invokes the AgentSuite Trust/Risk agent via MCP.
---

# Trust/Risk Agent Skill

This skill invokes the Trust/Risk agent from the AgentSuite MCP server. It produces 9 trust and risk specification artifacts and 8 brief templates for breach notifications, executive risk summaries, penetration test briefs, remediation trackers, risk acceptance forms, security awareness briefs, tabletop exercise scenarios, and vendor security questionnaires in 30–120 seconds, then pauses for human approval before promoting to long-lived storage.

## When to use

User wants any of:
- Threat model with attack surface analysis and adversary scenarios
- Risk register with likelihood, impact, and priority ratings
- Control framework mapping controls to risks and compliance requirements
- Incident response plan with roles, playbooks, and escalation paths
- Compliance matrix mapping requirements to evidence and ownership
- Vendor risk assessment with third-party due diligence criteria
- Security policy with acceptable use, access control, and data handling rules
- Audit readiness report with gap analysis and remediation roadmap
- Residual risk acceptance with documented owner sign-off
- Ready-to-fill brief templates for breach notifications, executive risk summaries, penetration test briefs, remediation trackers, risk acceptance forms, security awareness briefs, tabletop exercise scenarios, or vendor security questionnaires

## When NOT to use

- Technical architecture — use the Engineering agent
- Product requirements — use the Product agent
- Visual/brand direction — use the Design agent
- One-off copy or text tasks — write directly or use the Founder agent

## Steps

1. **Confirm required inputs.** Ask the user for:
   - `product_name` — the name of the product, service, or organization (required)
   - `risk_domain` — one sentence describing the primary risk or threat context (required)
   - `stakeholder_context` — the intended audience and risk ownership structure (required)
   - `project_slug` — lowercase, hyphenated identifier for `_kernel/` promotion (required)

2. **Gather optional context.** Ask if the user has:
   - Regulatory context (applicable laws, standards, or frameworks such as SOC 2, ISO 27001, HIPAA, GDPR, PCI-DSS)
   - Threat model scope (system boundaries, data flows, trust boundaries)
   - Compliance frameworks already in use or being targeted
   - Existing policies directory (prior security policies, acceptable use policies)
   - Incident reports directory (past incident postmortems, near-miss reports)
   These are optional — the agent can run without them.

3. **Set the environment.** Ensure `AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk` is set in the MCP env config. If "trust_risk" is not in `enabled` when you call `agentsuite_list_agents`, paste the snippet from `~/.claude/skills/trust-risk-agent/mcp-snippet.json` and ask the user to update their MCP config.

4. **Run the agent.** Execute:
   ```
   agentsuite trust-risk run --product-name "..." --risk-domain "..." --stakeholder-context "..."
   ```
   Optionally append `--regulatory-context "..."`, `--threat-model-scope "..."`, `--compliance-frameworks "..."`, `--existing-policies path/to/policies`, or `--incident-reports path/to/incidents` if the user provided those inputs.

5. **Artifacts appear in `.agentsuite/runs/{run_id}/`.** The primary output is `threat-model.md`. Additional artifacts: `risk-register.md`, `control-framework.md`, `incident-response-plan.md`, `compliance-matrix.md`, `vendor-risk-assessment.md`, `security-policy.md`, `audit-readiness-report.md`, `residual-risk-acceptance.md`.

6. **Review QA scores.** Open `qa_scores.json`. If any score is < 7.0, read `revision_instructions` in that file for specific guidance on what to improve. Address revisions before approving.

7. **Approve when satisfied.** Call:
   ```
   agentsuite trust-risk approve --run-id {run_id} --approver {name} --project-slug {slug}
   ```
   This promotes artifacts to `_kernel/<slug>/` for use in downstream agents and sessions.

## Cost expectations

A typical run costs $0.10 – $0.50 against Claude Sonnet or GPT-4o (12 LLM calls: 9 spec artifacts + extract + consistency check + QA scoring). Cost varies with input context size. Hard cap is $5.00 per run — if `HardCapExceeded` is raised, reduce input size or raise `AGENTSUITE_COST_CAP_USD`.

## Failure modes

- **`ConsistencyCheckFailed`** — One of the 9 artifacts contradicts another on a critical dimension (e.g. the control framework references a compliance requirement not present in the compliance matrix, or the incident response plan assigns ownership to a role not defined in the stakeholder context). Fix: add clearer constraints to your input, or narrow the `risk_domain` statement before re-running.
- **`Low QA scores`** — `requires_revision=true` in the result. Open `qa_scores.json` and read `revision_instructions` for each artifact scoring below 7.0. Apply the specific changes listed before approving.
- **`NoProviderConfigured`** — Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the MCP env.
- **`extract stage produced invalid JSON`** — Transient LLM formatting error. Re-run; it typically resolves on retry.

## Rubric dimensions

QA scoring evaluates each artifact on 9 dimensions: `threat_specificity`, `control_coverage`, `compliance_traceability`, `risk_prioritization`, `incident_response_completeness`, `vendor_due_diligence_depth`, `policy_enforceability`, `audit_evidence_quality`, `residual_risk_clarity`. Each dimension scores 0–10; artifacts with any dimension below 7.0 are flagged for revision.

## After approval

Promoted artifacts in `_kernel/<slug>/` can be fed directly into any subsequent AgentSuite agent session, shared with engineering teams as security requirements grounding, or loaded into a product session to align roadmap decisions with risk posture. The `brief-template-library/` folder contains 8 ready-to-fill templates for breach notifications, executive risk summaries, penetration test briefs, remediation trackers, risk acceptance forms, security awareness briefs, tabletop exercise scenarios, and vendor security questionnaires.
