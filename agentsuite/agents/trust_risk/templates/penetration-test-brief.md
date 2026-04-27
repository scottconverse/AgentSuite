# Penetration Test Scope Brief

**CONFIDENTIAL — AUTHORIZED TESTING ONLY**

**Organization:** {{ product_name }}
**Testing Period:** {{ quarter }}
**Point of Contact:** {{ team_lead }}
**Threat Category:** {{ threat_category }}
**Document Version:** 1.0

---

## Scope

**Systems and assets authorized for testing:**

[List every system, application, network range, or environment explicitly authorized. Be exhaustive — anything not listed here is out of scope by default.]

| Asset | Type | Environment | Notes |
|---|---|---|---|
| [System name / IP range] | Web app / API / Network / Cloud | Prod / Staging / Dev | [Any special conditions] |
| [System name / IP range] | Web app / API / Network / Cloud | Prod / Staging / Dev | [Any special conditions] |
| [System name / IP range] | Web app / API / Network / Cloud | Prod / Staging / Dev | [Any special conditions] |

**Authorized entry points:**
- [ ] External perimeter (internet-facing)
- [ ] Internal network (post-VPN)
- [ ] Web application layer
- [ ] API endpoints
- [ ] Social engineering / phishing (if approved — requires separate written authorization)
- [ ] Physical access (if approved — requires separate written authorization)

---

## Out of Scope

**The following are explicitly excluded from testing:**

[List all systems, data, actions, or techniques that are NOT authorized. This section is as important as the scope — it protects both the tester and the organization.]

- [System or asset name] — Reason: _______________
- [System or asset name] — Reason: _______________
- Production database writes or destructive actions
- Denial-of-service attacks against production systems
- Testing of third-party systems without written consent from that third party
- Data exfiltration beyond proof-of-concept (no real data leaves the environment)

---

## Rules of Engagement

**Authorization:** This test is authorized by {{ product_name }} executive sign-off. Testers must carry a copy of this brief during all testing activities.

**Notification protocol:**
- Testing hours: _______________
- Emergency stop contact: {{ team_lead }} — [Phone number]
- If critical vulnerability found mid-test: stop and notify {{ team_lead }} immediately before continuing

**Safe harbor:**
Testing conducted within this scope and these rules constitutes authorized security research. {{ product_name }} will not pursue legal action against testers operating within scope.

**Data handling:**
- All findings and data gathered during testing must be treated as confidential
- Raw data must be destroyed within 30 days of final report delivery
- Findings must not be disclosed to any third party without written consent from {{ product_name }}

---

## Target Systems

**Primary targets for {{ threat_category }} testing:**

[Describe the specific systems to focus testing effort on, based on the threat category. Include context on technology stack, known architecture, and any areas of particular concern.]

**Technology stack notes:**
- [Framework / language / platform details relevant to testing approach]
- [Known dependencies or third-party components]
- [Recent changes or deployments that may introduce new attack surface]

---

## Testing Timeline

| Phase | Activity | Start Date | End Date |
|---|---|---|---|
| Reconnaissance | Passive + active information gathering | [Date] | [Date] |
| Scanning | Automated vulnerability scanning | [Date] | [Date] |
| Exploitation | Manual exploitation of findings | [Date] | [Date] |
| Post-exploitation | Lateral movement, persistence (if in scope) | [Date] | [Date] |
| Reporting | Draft report + review | [Date] | [Date] |
| Debrief | Technical debrief with {{ team_lead }} | [Date] | [Date] |

**Total testing window:** {{ quarter }}

---

## Deliverables Expected

1. **Executive Summary** — Non-technical findings overview for {{ product_name }} leadership. 2–3 pages.
2. **Technical Report** — Full findings with CVE references, CVSS scores, evidence (screenshots/logs), and reproduction steps.
3. **Remediation Guidance** — Prioritized list of findings with specific recommended fixes, not just "patch the software."
4. **Retesting Scope** — After remediation, defined retesting scope to verify critical and high findings are closed.
5. **Raw Evidence Archive** — Logs, screenshots, and tool output in a password-protected archive.

**Report delivery deadline:** _______________
**Report format:** [ ] PDF  [ ] Word  [ ] Both

---

## Contact

**Primary contact during testing:**

Name: {{ team_lead }}
Title: _______________
Organization: {{ product_name }}
Email: _______________
Phone (emergency stop): _______________

**Secondary contact (if primary unavailable):**

Name: _______________
Email: _______________
Phone: _______________

---

*This brief constitutes the written authorization for penetration testing of {{ product_name }} systems as described above. Any testing activity outside this scope is unauthorized. Both parties must sign below before testing begins.*

**Authorized by ({{ product_name }}):** _______________ Date: _______________

**Acknowledged by (Testing Team Lead):** _______________ Date: _______________
