# Formal Risk Acceptance Form

**CONFIDENTIAL**

**Organization:** {{ product_name }}
**Risk Domain:** {{ risk_domain }}
**Threat Category:** {{ threat_category }}
**Form Reference:** RA-[YYYY]-[NNN]
**Submitted By:** _______________
**Submission Date:** _______________

---

## Purpose

This form documents the formal acceptance of a residual risk that the organization has evaluated and chosen not to remediate fully at this time. Risk acceptance is not the same as ignoring a risk — it is a deliberate, documented, authorized decision with defined review conditions.

---

## Risk Description

**Risk Title:** _______________

**Risk Statement:**
[Complete the sentence: "There is a risk that [event] will occur due to [cause], resulting in [consequence] for {{ product_name }}."]

There is a risk that _______________
will occur due to _______________,
resulting in _______________ for {{ product_name }}.

**Affected System / Asset / Process:** _______________

**Threat Category:** {{ threat_category }}

**Risk Domain:** {{ risk_domain }}

**Discovery Source:**
- [ ] Risk assessment
- [ ] Penetration test finding
- [ ] Audit finding
- [ ] Incident post-mortem
- [ ] Third-party assessment
- [ ] Other: _______________

**Source Reference:** _______________

---

## Risk Rating

| Factor | Rating | Rationale |
|---|---|---|
| **Likelihood** | Critical / High / Medium / Low | [Brief rationale — how probable is this event?] |
| **Impact** | Critical / High / Medium / Low | [Brief rationale — what is the worst-case outcome?] |
| **Inherent Risk** | Critical / High / Medium / Low | [Likelihood × Impact without any controls] |
| **Residual Risk** | Critical / High / Medium / Low | [Likelihood × Impact with existing controls applied] |

**Risk scoring methodology:** _______________

---

## Controls Considered

[List every control that was evaluated as a potential response to this risk. For each, state why it was not selected or why it provides insufficient coverage.]

| Control Option | Evaluated? | Decision | Reason Not Implemented |
|---|---|---|---|
| [Control name] | Yes / No | Accepted / Rejected / Partial | [Reason] |
| [Control name] | Yes / No | Accepted / Rejected / Partial | [Reason] |
| [Control name] | Yes / No | Accepted / Rejected / Partial | [Reason] |

**Existing compensating controls in place:**

[Describe any controls that are currently in place and reduce (but do not eliminate) this risk.]

---

## Reason for Acceptance

[State clearly and specifically why this risk is being accepted rather than remediated. Acceptable reasons include: cost of remediation exceeds risk value, technical remediation not currently feasible, business continuity requires maintaining the current state, or compensating controls reduce residual risk to acceptable levels. "We don't have time" is not an acceptable reason on its own.]

**Primary reason for acceptance:**

[Write 1–3 paragraphs. Be specific. Quantify cost or effort where possible. Reference the compensating controls. State what would change this decision.]

**Cost of full remediation (estimated):** _______________
**Cost of risk event (estimated):** _______________
**Cost-benefit analysis:** _______________

---

## Stakeholder Context

**Stakeholders informed of this risk acceptance:**

{{ stakeholder_context }}

Additional stakeholders:

| Name | Role | Notified Date |
|---|---|---|
| _____ | _____ | _____ |
| _____ | _____ | _____ |

---

## Accepted By

This risk acceptance requires sign-off at the appropriate authority level for the residual risk rating:

| Residual Risk | Required Approver |
|---|---|
| Critical | CEO + Board |
| High | CISO + Business Unit Head |
| Medium | Risk Manager + System Owner |
| Low | System Owner |

**Primary Approver:**

Name: _______________
Title: _______________
Signature: _______________ Date: _______________

**Secondary Approver (if required):**

Name: _______________
Title: _______________
Signature: _______________ Date: _______________

---

## Review Date

**This risk acceptance is valid until:** _______________

**Conditions that would trigger earlier review:**
- [Condition 1 — e.g., a related security incident occurs]
- [Condition 2 — e.g., regulatory requirements change]
- [Condition 3 — e.g., system architecture changes]
- Annual review regardless of conditions

---

## Expiry

**Expiry Date:** _______________

**Action at expiry:**
- [ ] Risk acceptance renewed (requires new sign-off)
- [ ] Risk remediated (tracking ticket: _______)
- [ ] Risk transferred (e.g., insurance or contract)
- [ ] Risk retired (risk no longer applicable)

**Owner responsible for expiry follow-up:** _______________

---

*Risk acceptance does not eliminate the risk. It is a documented business decision that this residual risk is within the organization's risk appetite at this time. This form must be stored in the risk register and reviewed at the stated review date.*
