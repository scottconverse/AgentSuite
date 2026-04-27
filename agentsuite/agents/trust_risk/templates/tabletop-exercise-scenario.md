# Tabletop Exercise Scenario

**CONFIDENTIAL — EXERCISE MATERIALS**

**Organization:** {{ product_name }}
**Scenario Title:** {{ incident_title }}
**Severity Classification:** {{ severity }}
**Threat Category:** {{ threat_category }}
**Exercise Date:** _______________
**Facilitator:** _______________
**Participants:** _______________

---

## Facilitator Notes

This document contains the full scenario, including injects the participants will not see until the appropriate phase. Distribute only the Scenario Description and Initial Indicators sections to participants before the exercise begins. Reveal each phase's injects at the designated time.

**Exercise objectives:**
1. Test the organization's detection and escalation procedures
2. Identify gaps in communication between teams during a {{ severity }}-severity incident
3. Validate the incident response plan against a realistic {{ threat_category }} scenario
4. Surface decision-making bottlenecks before a real incident occurs

**Ground rules for participants:**
- Respond as if this is a real incident — no "well in a real incident we'd…"
- Decisions made in the exercise are the decisions your plan would produce
- All communications in the exercise should mirror real-world communication channels
- There are no wrong answers — the goal is to learn, not to pass a test

---

## Scenario Description

**Scenario Title:** {{ incident_title }}

**Severity:** {{ severity }}

**Threat Category:** {{ threat_category }}

[Write a 2–3 paragraph narrative describing the scenario. This is the backstory — what has happened leading up to the exercise start. Set the scene. Include: the nature of the threat ({{ threat_category }}), the systems or data at risk, the business context for {{ product_name }}, and any relevant background that participants need to respond realistically. Do not include initial indicators — those go in the next section.]

**Business context:**
It is [day of week], [time]. Normal business operations are underway at {{ product_name }}. Key personnel are available. [Add any relevant context about business cycles, upcoming events, or staffing that affects the scenario.]

---

## Initial Indicators

*[These indicators are distributed to participants at exercise start. They represent what the security team actually knows at T+0.]*

At [time], the following indicators are observed:

1. [Indicator 1 — specific, realistic signal. E.g., "SIEM alert: 47 failed authentication attempts against the VPN gateway in a 10-minute window, all from a single IP in [country]"]
2. [Indicator 2 — a second, corroborating or confounding signal]
3. [Indicator 3 — optional: a business-facing signal, e.g., a user complaint or anomaly]

**Discussion question for Phase 1 start:**
- What is your immediate assessment of these indicators?
- Who needs to be notified right now?
- What additional information do you need, and how will you get it?

---

## Phase 1 Inject — [T+30 minutes]

*[Facilitator reveals this inject 30 minutes into the exercise.]*

**New information:**

[Describe escalation of the scenario. What does the team discover as they investigate the initial indicators? This inject should increase the stakes or complexity — a second system is now affected, a data exfiltration is confirmed, a business partner is impacted, a regulatory clock starts, etc.]

**Phase 1 Discussion Questions:**

1. [Question testing incident classification and escalation decision]
2. [Question testing communication — who gets notified now, and what do you say?]
3. [Question testing containment decision — what do you isolate, and what stays up?]
4. [Question testing regulatory awareness — does this trigger a notification obligation?]

**Expected actions at this phase:**
- [ ] Incident formally declared at appropriate severity level
- [ ] Incident commander / CISO notified
- [ ] Containment actions initiated
- [ ] Legal / compliance team engaged if applicable
- [ ] Evidence preservation begun

---

## Phase 2 Inject — [T+60 minutes]

*[Facilitator reveals this inject 60 minutes into the exercise.]*

**New information:**

[Escalate further. Introduce a complication that tests a specific gap you want to probe — a key person is unavailable, a backup system fails, media inquiry arrives, a third-party vendor is implicated, a ransom demand is received, or a regulator makes contact. Make it realistic and uncomfortable.]

**Phase 2 Discussion Questions:**

1. [Question testing decision-making under pressure and incomplete information]
2. [Question testing external communication — customer notification, press, regulator]
3. [Question testing recovery prioritization — what comes back up first and why?]
4. [Question testing vendor / third-party coordination]

**Expected actions at this phase:**
- [ ] External communications plan activated
- [ ] Recovery priorities agreed and documented
- [ ] Vendor / third-party contacts engaged
- [ ] Regulatory notification decision made (notify / defer with documentation)
- [ ] Executive leadership briefed

---

## Phase 3 Inject — [T+90 minutes]

*[Facilitator reveals this inject 90 minutes into the exercise.]*

**New information:**

[Resolution or partial resolution. The immediate crisis is under control, but new challenges emerge: the root cause is identified and it's embarrassing or systemic, a second wave of the attack begins, a regulatory authority requests documentation, or the remediation plan reveals a larger architectural problem.]

**Phase 3 Discussion Questions:**

1. [Question testing post-incident review readiness — what do you document and when?]
2. [Question testing lessons-learned process — what changes after this?]
3. [Question testing long-term remediation — what systemic fix is required?]
4. [Question testing stakeholder communication after the incident is resolved]

**Expected actions at this phase:**
- [ ] Incident formally closed with documented timeline
- [ ] Post-incident review (PIR) scheduled within 5 business days
- [ ] Remediation items logged in risk register / tracking system
- [ ] Customer / partner communication issued if applicable
- [ ] Regulatory notification submitted if required

---

## Discussion Questions — Cross-Phase

*[These questions can be raised at any point or used to close the exercise.]*

1. At what point did you know this was a {{ severity }}-severity incident? What confirmed it?
2. Were your playbooks / runbooks specific enough to guide actual decisions, or were they too generic?
3. What information did you need that you couldn't get quickly enough?
4. Which team or role had the most confusion about their responsibilities?
5. What would you do differently in the first 15 minutes if this happened tomorrow?

---

## Success Criteria

The exercise is successful if participants can demonstrate:

- [ ] Correct incident classification within 15 minutes of initial indicators
- [ ] Clear escalation chain followed — right people reached, in the right order
- [ ] Containment decision made with documented rationale within 30 minutes
- [ ] Regulatory notification decision made with documented rationale
- [ ] Communication plan for affected parties activated
- [ ] Evidence preserved without contamination
- [ ] Recovery priorities agreed before restoration begins
- [ ] Post-incident review scheduled before exercise ends

---

## After-Action Report Template

**Exercise:** {{ incident_title }}
**Date:** _______________

| Area | What Worked | What Didn't | Action Item | Owner | Due |
|---|---|---|---|---|---|
| Detection | | | | | |
| Escalation | | | | | |
| Containment | | | | | |
| Communication | | | | | |
| Recovery | | | | | |
| Documentation | | | | | |

**Overall exercise rating:** [ ] Excellent  [ ] Satisfactory  [ ] Needs improvement

**Top 3 action items from this exercise:**

1. [Action item — specific, owned, time-bound]
2. [Action item — specific, owned, time-bound]
3. [Action item — specific, owned, time-bound]

---

*This scenario was designed for {{ product_name }} tabletop exercise purposes only. It is fictional and does not represent actual events. Findings from this exercise are used to improve incident response readiness.*
