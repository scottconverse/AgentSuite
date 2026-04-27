# Vulnerability Remediation Tracker

**Organization:** {{ product_name }}
**Control Area:** {{ control_name }}
**Severity Threshold:** {{ severity }}
**Last Updated:** _______________
**Tracker Owner:** _______________

---

## Summary Dashboard

| Severity | Total | Open | In Progress | Remediated | Accepted |
|---|---|---|---|---|---|
| Critical | — | — | — | — | — |
| High | — | — | — | — | — |
| Medium | — | — | — | — | — |
| Low | — | — | — | — | — |
| **Total** | — | — | — | — | — |

**Overall remediation rate:** ___%
**Average time-to-remediate (critical):** ___ days
**Average time-to-remediate (high):** ___ days
**SLA compliance rate:** ___%

---

## Finding Detail Records

*Duplicate this block for each finding.*

---

### Finding ID: [FIND-001]

**Description:**
[Clear, concise description of the vulnerability. State what the issue is, where it exists, and what an attacker could do with it. Write for someone who did not perform the original assessment.]

**Severity:** {{ severity }}

**CVSS Score:** _____ (v3.1)
**CVSS Vector:** CVSS:3.1/AV:_/AC:_/PR:_/UI:_/S:_/C:_/I:_/A:_

**Affected Component:**
- System / Application: _______________
- Module / Endpoint / Host: _______________
- Version: _______________
- Environment: [ ] Production  [ ] Staging  [ ] Development

**Discovery Source:**
- [ ] Penetration test
- [ ] Automated scan (tool: _______)
- [ ] Bug bounty / external report
- [ ] Internal audit
- [ ] Threat intelligence
- [ ] Other: _______________

**Discovery Date:** _______________
**Source Report / Reference:** _______________
**CVE Reference (if applicable):** _______________

---

**Owner:** _______________
**Owner Team:** _______________
**Due Date:** _______________

**SLA (based on severity):**
- Critical: 24 hours (emergency patch) or 7 days (full remediation)
- High: 30 days
- Medium: 90 days
- Low: 180 days or next planned maintenance

---

**Status:** [ ] Open  [ ] In Progress  [ ] Remediated  [ ] Risk Accepted  [ ] False Positive

**Status Notes:**
[Current status, blockers, escalation needs, or reason for delay.]

---

**Remediation Plan:**
[Specific steps to fix this finding. Not "upgrade the library" — include the exact library, target version, affected files, config changes, and test steps to verify the fix.]

1. [Step 1]
2. [Step 2]
3. [Step 3]

**Target Patch/Fix Version:** _______________
**Deployment Window:** _______________

---

**Evidence of Remediation:**

| Evidence Type | Description | Date Verified | Verified By |
|---|---|---|---|
| [ ] Retesting confirmed fix | [Scanner output, manual test result] | _____ | _____ |
| [ ] Patch applied — version confirmed | [Version string or build hash] | _____ | _____ |
| [ ] Configuration change validated | [Config diff or screenshot] | _____ | _____ |
| [ ] Code review of fix | [PR / commit reference] | _____ | _____ |

**Remediation Verified:** [ ] Yes  [ ] No  [ ] Partial
**Verified By:** _______________
**Verification Date:** _______________
**Ticket / Change Reference:** _______________

---

**Control Mapping:**
- **Control:** {{ control_name }}
- **Framework Reference:** _______________
- **Risk Reduced:** [ ] Yes — describe: _______________  [ ] Residual risk remains — describe: _______________

---

*Add additional Finding ID blocks above for each tracked vulnerability.*

---

## Escalation Log

| Date | Finding ID | Escalated To | Reason | Resolution |
|---|---|---|---|---|
| [Date] | [FIND-XXX] | [Name / Role] | [Reason for escalation] | [Outcome] |

---

## Changelog

| Date | Change | Author |
|---|---|---|
| [Date] | Tracker created | _____ |
| [Date] | [Change description] | _____ |
