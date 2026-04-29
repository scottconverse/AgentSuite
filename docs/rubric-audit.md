# Founder Rubric Audit

**Status:** Reference / supporting evidence for [ADR-0001](adr/0001-rubric-dimensions.md)
**Last reviewed:** 2026-04-28 (v0.9.2)
**Source of truth:** `agentsuite/agents/<agent>/rubric.py`

This page is the side-by-side audit referenced in ADR-0001. It cross-references every dimension on every agent's rubric, groups semantic overlaps, and records the per-dimension uniqueness signal that justifies the dimension count.

---

## Headline finding

All seven agents currently ship a **9-dimension** rubric. The "Founder = 7, others = 9" framing in the original ADR-0001 narrative was true at the time the ADR was drafted but is no longer accurate: commit `2b1dda0` ("feat: add constraint_adherence and completeness to Founder rubric (9 dims)") brought Founder up to 9 alongside the other six. ADR-0001's *decision* (counts driven by signal, not symmetry) still stands; the *narrative* under "Decision" needs a one-line refresh to match current code. Tracked as a minor follow-up — not a code change.

The asymmetry concern that prompted ADR-0001 is therefore resolved in code. The remaining audit question is whether the **9 dimensions per rubric** are themselves redundant. The cross-reference below shows they are not: each rubric carries domain-specific signal that does not collapse cleanly into the others.

---

## Cross-reference table

Rows are conceptual themes recurring across agents. Columns are agents. A cell holds the dimension name (or `—` if absent). This is a semantic mapping, not a literal lexicon match — `anti_genericity` (Founder) and `anti_feature_creep` (Product) share the *anti-X* shape but score different things and are kept in separate rows.

| Theme | Founder | Design | Product | Engineering | Marketing | TrustRisk | CIO |
|---|---|---|---|---|---|---|---|
| Completeness / no placeholders | `completeness` | `spec_completeness` | `acceptance_completeness` | `operational_completeness` | `content_depth` | `threat_coverage` | — |
| Domain specificity / actionability | `template_specificity` | `craft_specificity` | `metric_specificity` | `implementation_specificity` | `metric_specificity` | `control_specificity` | — |
| Audience / brand fit | `voice_fit` + `brand_consistency` | `brand_fidelity` + `audience_fit` | `user_grounding` | — | `audience_clarity` + `message_resonance` | — | — |
| Goal / strategy alignment | `goal_alignment` | — | `problem_clarity` | — | — | — | `strategic_alignment` |
| Constraint / scope discipline | `constraint_adherence` | — | `scope_discipline` | `anti_overengineering` | `budget_realism` | — | `budget_realism` |
| Anti-cliché / anti-creep | `anti_genericity` | `anti_genericity` | `anti_feature_creep` | `anti_overengineering` | `anti_vanity_metrics` | — | — |
| Evidence / traceability | `claims_grounded` | — | — | `decision_traceability` | — | `audit_traceability` | — |
| Reusability / future use | `reusability` | — | — | — | — | — | — |
| Cross-artifact consistency | `brand_consistency` | `consistency` | — | — | — | — | — |
| Revision / actionability of QA | — | `revision_actionability` | — | — | — | — | — |
| Accessibility | — | `accessibility_rigor` | — | — | — | — | — |
| Image / artifact precision | — | `image_prompt_precision` | — | — | — | — | — |
| Stakeholder clarity | — | — | `stakeholder_clarity` | — | — | — | — |
| Sequencing / roadmap | — | — | `roadmap_sequencing` | — | `launch_sequencing` | — | — |
| Feasibility / risk awareness | — | — | `feasibility_awareness` | `scalability_awareness` | — | `risk_quantification` | `risk_tolerance_clarity` |
| Testability | — | — | — | `testability` | — | — | — |
| Security posture | — | — | — | `security_posture` | — | `zero_trust_posture` | — |
| Dependencies / vendors | — | — | — | `dependency_hygiene` | — | `vendor_risk_awareness` | `vendor_discipline` |
| API / contract clarity | — | — | — | `api_contract_clarity` | — | — | — |
| Channel / delivery fit | — | — | — | — | `channel_fit` | — | — |
| Competitive landscape | — | — | — | — | `competitive_awareness` | — | — |
| Regulatory / governance | — | — | — | — | — | `regulatory_alignment` | `governance_maturity` |
| Incident / response | — | — | — | — | — | `incident_readiness` | — |
| Residual risk | — | — | — | — | — | `residual_risk_acceptance` | — |
| Tech-debt / digital maturity | — | — | — | — | — | — | `technology_debt_awareness` + `digital_readiness` |
| Workforce capability | — | — | — | — | — | — | `workforce_capability` |
| Innovation / portfolio balance | — | — | — | — | — | — | `innovation_balance` |

---

## Per-agent uniqueness signal

For each agent, the question is: would removing a dimension materially weaken QA? Audit answer per dimension below.

### Founder (9)
- **reusability** — unique. No other rubric scores whether the artifact is rerunnable next week without restating context. Keep.
- **brand_consistency** — overlaps with Design's `brand_fidelity` semantically but Founder owns the source-of-truth definition; the score on Founder is *self-consistency across artifacts*, not fidelity to an upstream brief. Keep.
- **claims_grounded** — Founder is the only agent producing strategic claims at this level of generality. Keep.
- **voice_fit** — unique. No other agent scores voice match against samples. Keep.
- **template_specificity** — analogous to other agents' `*_specificity` but applied to *brief templates* (i.e. the artifact others will consume). Keep.
- **goal_alignment** — Founder owns business_goal as input; downstream agents inherit it. Keep.
- **anti_genericity** — shared shape with Design's `anti_genericity`. Different surface (founder voice vs. design clichés). Keep.
- **constraint_adherence** — added in `2b1dda0` to score budget/timeline/resource realism. Distinct from Product's `scope_discipline` (scope ≠ resource). Keep.
- **completeness** — added in `2b1dda0`. Mirrors `spec_completeness` etc. across agents but applies to the founder spec set. Keep.

### Design (9)
All nine are domain-specific (accessibility, image prompt precision, revision actionability are Design-only). No collapse opportunity.

### Product (9)
All nine are PM-domain. `stakeholder_clarity` and `roadmap_sequencing` are Product-only.

### Engineering (9)
All nine are eng-domain. `testability`, `security_posture`, `api_contract_clarity` are Engineering-only.

### Marketing (9)
All nine are marketing-domain. `channel_fit`, `competitive_awareness`, `launch_sequencing` are Marketing-only.

### TrustRisk (9)
All nine are security-domain. `incident_readiness`, `regulatory_alignment`, `residual_risk_acceptance`, `zero_trust_posture` are TrustRisk-only.

### CIO (9)
All nine are CIO-domain. `technology_debt_awareness`, `digital_readiness`, `governance_maturity`, `workforce_capability`, `innovation_balance` are CIO-only.

---

## Recommendation

1. **No code change.** Every dimension on every rubric carries unique signal in its agent's domain. Removals would weaken QA coverage.
2. **Refresh ADR-0001 narrative** in a follow-up doc-only PR: change "Founder remains at 7 dimensions; the other six agents remain at 9" to reflect the post-`2b1dda0` reality (all seven agents at 9). The ADR's *decision* (signal-driven, not symmetry-driven) is unchanged.
3. **Future audits** should look at signal-per-dimension correlation on representative runs (low correlation = redundant = candidate for collapse), not raw count or label similarity. This page is the cross-reference baseline for that future work.

---

## How this page is maintained

- Update the cross-reference table whenever any agent's `rubric.py` adds, renames, or removes a dimension.
- Update the per-agent uniqueness section in the same commit as the rubric change.
- Linked from `docs/adr/0001-rubric-dimensions.md` and `CONTRIBUTING.md` (under "Modifying rubrics").
