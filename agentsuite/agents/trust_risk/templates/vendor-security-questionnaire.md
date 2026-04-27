# Vendor Security Questionnaire

**CONFIDENTIAL**

**Issuing Organization:** {{ product_name }}
**Vendor / Supplier Name:** {{ vendor_name }}
**Assessment Date:** _______________
**Assessment Reference:** VSQ-[YYYY]-[NNN]
**Compliance Frameworks:** {{ compliance_frameworks }}
**Completed By:** _______________
**Vendor Point of Contact:** _______________

---

## Instructions

This questionnaire is required as part of {{ product_name }}'s third-party risk management program. Please complete all sections truthfully and completely. Incomplete responses will delay vendor onboarding or renewal.

Supporting evidence (certifications, audit reports, policies) is required where indicated. Attach documents to the completed questionnaire or provide secure links.

If a question does not apply to your organization, mark it "N/A" and provide a brief explanation.

---

## Section 1: Vendor Information

| Field | Response |
|---|---|
| Legal entity name | |
| Parent company (if applicable) | |
| Primary business address | |
| Countries of operation | |
| Number of employees | |
| Year founded | |
| Publicly traded? (Y/N — if yes, ticker) | |
| Primary point of contact for security matters | |
| Contact email / phone | |

**Describe your organization's primary service or product and how it relates to your engagement with {{ product_name }}:**

[Response]

---

## Section 2: Data Handling

**2.1 What categories of {{ product_name }} data will your organization access, process, store, or transmit?**

- [ ] Personal data (names, contact information)
- [ ] Sensitive personal data (health, financial, government IDs)
- [ ] Customer data ({{ product_name }} customer records)
- [ ] Intellectual property / proprietary business data
- [ ] Authentication credentials or secrets
- [ ] {{ product_name }} employee data
- [ ] Other: _______________

**2.2 Where will {{ product_name }} data be stored? (List all locations — country and facility type)**

[Response]

**2.3 Do you use subprocessors or subcontractors who will have access to {{ product_name }} data?**

- [ ] No
- [ ] Yes — list all subprocessors below:

| Subprocessor Name | Country | Data Accessed | Contractual Protections in Place |
|---|---|---|---|
| | | | |

**2.4 What is your data retention policy for {{ product_name }} data? How is data disposed of at contract termination?**

[Response]

**2.5 Do you have a documented data classification policy?**

- [ ] Yes — attach or link to policy
- [ ] No

---

## Section 3: Access Controls

**3.1 Describe your identity and access management (IAM) approach:**

- [ ] Multi-factor authentication (MFA) required for all users accessing {{ product_name }} data
- [ ] MFA required for privileged accounts only
- [ ] MFA not currently implemented — timeline for implementation: _______________

**3.2 How is access to {{ product_name }} data provisioned and deprovisioned?**

[Response — describe the process, including approval workflow and timing for offboarding]

**3.3 Is access to {{ product_name }} data restricted to a need-to-know basis?**

- [ ] Yes — describe controls: _______________
- [ ] No — explain: _______________

**3.4 Do you conduct privileged access reviews?**

- [ ] Yes — frequency: _______________
- [ ] No

**3.5 Do you use shared or service accounts to access {{ product_name }} systems?**

- [ ] No
- [ ] Yes — describe governance controls: _______________

---

## Section 4: Encryption Standards

**4.1 Data in transit:**

- [ ] TLS 1.2 or higher enforced for all data in transit
- [ ] TLS 1.1 or lower still in use — remediation plan: _______________
- [ ] Other protocol: _______________

**4.2 Data at rest:**

- [ ] AES-256 or equivalent encryption for all {{ product_name }} data at rest
- [ ] AES-128 — explain rationale: _______________
- [ ] Encryption not applied — explain: _______________

**4.3 Key management:**

- [ ] Hardware Security Module (HSM) used
- [ ] Cloud-native KMS (specify provider): _______________
- [ ] Software-based key management — describe: _______________

**4.4 Do you support customer-managed encryption keys (CMEK)?**

- [ ] Yes
- [ ] No
- [ ] On roadmap — estimated availability: _______________

---

## Section 5: Incident Response Capability

**5.1 Do you have a documented Incident Response Plan (IRP)?**

- [ ] Yes — last tested (date): _______________  Last updated: _______________
- [ ] No — timeline to develop: _______________

**5.2 What is your committed notification timeline for security incidents affecting {{ product_name }} data?**

- [ ] Within 24 hours of discovery
- [ ] Within 48 hours of discovery
- [ ] Within 72 hours of discovery (GDPR minimum)
- [ ] Not defined — will commit to: _______________

**5.3 Who is the designated point of contact for incident notification to {{ product_name }}?**

Name: _______________
Role: _______________
Email: _______________
Phone (24/7): _______________

**5.4 Have you experienced a security incident affecting customer data in the past 24 months?**

- [ ] No
- [ ] Yes — describe (nature of incident, data affected, actions taken):

[Response]

**5.5 Do you conduct tabletop exercises or incident response drills?**

- [ ] Yes — frequency: _______________
- [ ] No

---

## Section 6: Compliance Certifications

**6.1 Current certifications and audit reports held:**

| Certification / Standard | Scope | Issue Date | Expiry / Next Audit | Evidence Attached |
|---|---|---|---|---|
| [ ] SOC 2 Type II | | | | |
| [ ] ISO 27001 | | | | |
| [ ] PCI DSS | | | | |
| [ ] HIPAA (BAA in place) | | | | |
| [ ] FedRAMP | | | | |
| [ ] CSA STAR | | | | |
| [ ] {{ compliance_frameworks }} | | | | |
| Other: _______ | | | | |

**6.2 Have you had any audit findings (non-conformances, qualified opinions) in the past 24 months?**

- [ ] No
- [ ] Yes — describe and explain remediation:

[Response]

**6.3 Are you subject to any regulatory investigations or enforcement actions related to data security or privacy?**

- [ ] No
- [ ] Yes — describe:

[Response]

---

## Section 7: SLA / SLO Commitments

**7.1 Service availability commitment:**

- Target uptime SLA: ____%
- Measurement period: _______________
- Historical uptime (past 12 months): ____%
- Status page / availability history: [URL]

**7.2 Incident response SLAs:**

| Severity | Initial Response | Status Updates | Resolution Target |
|---|---|---|---|
| Critical | ___ hours | Every ___ hours | ___ hours |
| High | ___ hours | Every ___ hours | ___ hours |
| Medium | ___ hours | Every ___ hours | ___ hours |
| Low | ___ hours | Every ___ hours | ___ hours |

**7.3 Data portability and exit:**

- Can {{ product_name }} export all its data on request? [ ] Yes  [ ] No
- Export format: _______________
- Time to complete full data export: _______________
- Data deletion after contract termination: confirmed within ___ days, with written confirmation: [ ] Yes  [ ] No

**7.4 Disaster recovery:**

- Recovery Time Objective (RTO): _______________
- Recovery Point Objective (RPO): _______________
- Last DR test performed: _______________
- DR test results available upon request: [ ] Yes  [ ] No

---

## Certification

I certify that the responses provided in this questionnaire are accurate and complete to the best of my knowledge. I am authorized to provide these representations on behalf of {{ vendor_name }}.

**Completed By:**

Name: _______________
Title: _______________
Organization: {{ vendor_name }}
Email: _______________
Signature: _______________ Date: _______________

---

*This questionnaire is provided to {{ product_name }} as part of its vendor risk management process. Responses will be treated as confidential. {{ product_name }} reserves the right to request additional information, conduct follow-up interviews, or perform on-site audits to verify responses.*
