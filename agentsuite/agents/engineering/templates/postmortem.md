# Postmortem

## Incident Summary
| Field | Value |
|-------|-------|
| Title | {{ incident_title }} |
| Severity | {{ severity }} |
| System | {{ system_name }} |
| Incident Start | |
| Incident End | |
| Total Duration | |
| Detection Time | |
| Time to Mitigate | |
| Time to Resolve | |
| Postmortem Owner | |
| Review Meeting | |

---

## Timeline

| Time (UTC) | Event | Who Acted |
|------------|-------|-----------|
| | Earliest known signal (log entry, metric spike, user report) | |
| | Alert fired | |
| | Oncall paged | |
| | Investigation begins | |
| | Initial hypothesis formed | |
| | [Hypothesis confirmed / ruled out] | |
| | Root cause identified | |
| | Mitigation applied | |
| | Service restored | |
| | All-clear declared | |
| | Postmortem opened | |

---

## Root Cause Analysis

### Root Cause Statement
[One sentence: the single underlying technical reason the incident occurred.]

### 5 Whys
| # | Why? | Answer |
|---|------|--------|
| 1 | Why did the incident occur? | |
| 2 | Why did [answer to #1] happen? | |
| 3 | Why did [answer to #2] happen? | |
| 4 | Why did [answer to #3] happen? | |
| 5 | Why did [answer to #4] happen? | |

**Root cause (Why #5 answer):** [The systemic cause — usually a process, tooling, or design gap]

---

## Contributing Factors
These are not the root cause but made the incident worse or harder to detect/resolve.

- [Factor 1 — e.g., no alerting on the leading indicator metric]
- [Factor 2 — e.g., runbook missing the correct recovery steps]
- [Factor 3 — e.g., recent deploy removed a guard that caught this case]
- [Factor 4 — e.g., oncall rotation had insufficient context on this subsystem]

---

## Impact

| Dimension | Measurement |
|-----------|-------------|
| Users affected | |
| Requests failed or degraded | |
| Error rate at peak | |
| Max p99 latency | |
| SLO breach | [ ] No  [ ] Yes — Error budget burned: |
| Data loss | [ ] None  [ ] Partial — describe: |
| Estimated revenue impact | |
| Regulatory / compliance impact | |

**Scale context:** {{ scale_requirements }}

---

## What Went Well
[Honest credit for things that worked — fast detection, clean rollback, good communication, etc.]

- [Item 1]
- [Item 2]
- [Item 3]

---

## What Could Be Better
[Honest gaps — slow detection, unclear runbook, poor escalation, delayed communication, etc.]

- [Item 1]
- [Item 2]
- [Item 3]

---

## Action Items

| Action | Owner | Due Date | Priority | Tracking |
|--------|-------|----------|----------|----------|
| [Fix root cause] | | | P0 | |
| [Add/improve alert for leading indicator] | | | P1 | |
| [Update runbook with correct recovery steps] | | | P1 | |
| [Review similar systems for same failure mode] | | | P2 | |
| [Architecture change to prevent recurrence] | | | P2 | |

---

## Follow-up Schedule

| Meeting / Milestone | Date | Purpose |
|--------------------|------|---------|
| Action item review | +1 week | Confirm P0/P1 items are in progress |
| Close-out review | +30 days | Verify all actions completed, SLO restored |

---

## Tech Stack Reference
{{ tech_stack }}

**Team:** {{ team_size }}

---

*Postmortem completed by: _______________  Date: _______________*
*Reviewed by: _______________  Date: _______________*
*Approved by (engineering manager): _______________  Date: _______________*
