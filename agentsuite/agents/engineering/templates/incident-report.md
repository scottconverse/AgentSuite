# Incident Report

## Incident Title
{{ incident_title }}

## Summary
| Field | Value |
|-------|-------|
| Severity | {{ severity }} |
| System | {{ system_name }} |
| Status | [ ] Open  [ ] Mitigated  [ ] Resolved |
| Incident Start | |
| Incident End | |
| Total Duration | |
| Reported By | |
| Incident Commander | |

---

## Timeline

| Time (UTC) | Action / Observation | Who |
|------------|---------------------|-----|
| | First alert fired / issue noticed | |
| | Initial investigation begins | |
| | Root cause hypothesis formed | |
| | Mitigation applied | |
| | Service restored | |
| | All-clear declared | |

---

## Root Cause
[Single sentence: the underlying technical reason the incident occurred.]

**Detailed explanation:**
[Full technical narrative. What failed, why it failed, and how the failure propagated.]

---

## Contributing Factors
- [Factor 1 — e.g., missing alerting threshold]
- [Factor 2 — e.g., recent deploy without rollback tested]
- [Factor 3 — e.g., runbook out of date]

---

## Impact
| Dimension | Detail |
|-----------|--------|
| Users affected | |
| Requests failed / degraded | |
| Data loss | [ ] None  [ ] Partial — describe: |
| SLO breach | [ ] No  [ ] Yes — describe: |
| Revenue impact | |
| Regulatory / compliance impact | |

Scale context: {{ scale_requirements }}

---

## Immediate Fix
[What was done to stop the bleeding and restore service? Include commands run, config changed, etc.]

---

## Follow-up Actions

| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| [Permanent fix for root cause] | | | High |
| [Add/improve alerting] | | | High |
| [Update runbook] | | | Medium |
| [Review similar systems for same issue] | | | Medium |
| [Post-incident review meeting] | | | Low |

---

## Lessons Learned

### What went well
- [Detection was fast because…]
- [Rollback worked cleanly because…]

### What could be better
- [Alert threshold too high — missed early signal]
- [Runbook was missing step X]
- [Oncall handoff was unclear]

### Process improvements
- [Improvement 1]
- [Improvement 2]

---

## Tech Stack Reference
{{ tech_stack }}

**Team:** {{ team_size }}

---

*Report completed by: _______________  Date: _______________*
*Reviewed by: _______________  Date: _______________*
