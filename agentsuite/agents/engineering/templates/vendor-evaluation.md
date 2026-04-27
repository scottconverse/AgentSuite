# Vendor Evaluation

## Vendor
{{ vendor_name }}

## System Context
{{ system_name }}

## Evaluation Details
| Field | Value |
|-------|-------|
| Evaluation lead | |
| Team | {{ team_size }} |
| Evaluation period | |
| Decision deadline | |
| Tech stack | {{ tech_stack }} |
| Scale requirements | {{ scale_requirements }} |

---

## Problem Being Solved
{{ problem_domain }}

### Build vs. Buy Rationale
[Why are we evaluating a vendor rather than building in-house or using an existing tool?]

---

## Evaluation Criteria

Scores: 1 (poor) — 5 (excellent). Weight column must sum to 100%.

| Criterion | Weight | Score (1–5) | Weighted Score | Notes |
|-----------|--------|-------------|----------------|-------|
| Functional fit — does it solve our problem? | 25% | | | |
| Reliability — SLA, uptime history, incident history | 20% | | | |
| Security — certifications, data handling, pen test history | 20% | | | |
| Support — response SLA, escalation path, account team quality | 10% | | | |
| Cost — TCO over 3 years including integration and migration | 15% | | | |
| Integration — API quality, SDK ecosystem, our stack compatibility | 10% | | | |
| **Total** | **100%** | | | |

**Composite score:** _____ / 5.0

---

## Technical Deep-Dive

### Integration Architecture
[How does this vendor connect to {{ system_name }}? Describe the data flow and integration points.]

### API / SDK Assessment
| Dimension | Assessment |
|-----------|-----------|
| API style (REST / GraphQL / gRPC / etc.) | |
| SDK language support | |
| Authentication mechanism | |
| Rate limits | |
| Webhook / event support | |
| Versioning and deprecation policy | |
| Documentation quality | |

### Performance Testing Results
| Test | Scenario | Result | SLA Requirement | Pass/Fail |
|------|----------|--------|----------------|-----------|
| Latency (p50) | [describe] | | | |
| Latency (p99) | [describe] | | | |
| Throughput | [describe] | | | |
| Error rate under load | [describe] | | | |

### Tech Stack Compatibility
[Does the vendor work with {{ tech_stack }}? List any adapters, custom code, or limitations.]

---

## Security Assessment

| Dimension | Detail |
|-----------|--------|
| Certifications | SOC 2 Type II / ISO 27001 / FedRAMP / other |
| Data residency | Where is our data stored? |
| Encryption at rest | |
| Encryption in transit | |
| Access controls | RBAC, SSO, MFA support |
| Audit logging | |
| Penetration test | Last conducted, available on NDA? |
| Vulnerability disclosure | Responsible disclosure policy? |
| Incident notification SLA | How quickly must they notify us of a breach? |
| Data deletion | How is data deleted on contract end? |

---

## Pricing Model

| Component | Price | Notes |
|-----------|-------|-------|
| Base / platform fee | | |
| Usage-based component | | |
| Overages | | |
| Professional services / onboarding | | |
| Support tier | | |
| Contract term options | | |

**3-Year TCO Estimate:**
| Year | License ($) | Integration ($) | Support ($) | Total ($) |
|------|------------|-----------------|-------------|-----------|
| Year 1 | | | | |
| Year 2 | | | | |
| Year 3 | | | | |
| **3-Year Total** | | | | **$ ________** |

---

## References

| Company | Contact | Use Case | Outcome |
|---------|---------|----------|---------|
| | | | |
| | | | |

**Reference call notes:** [Key themes from reference conversations]

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Vendor lock-in | | | |
| Pricing increase at renewal | | | |
| Vendor acquisition or shutdown | | | |
| Data sovereignty change | | | |
| SLA breach with inadequate remedy | | | |

---

## Recommendation

**Decision:** [ ] Proceed  [ ] Do Not Proceed  [ ] Needs Further Evaluation

**Recommended contract terms / commitments:**
[Annual vs. monthly, term length, minimum commit, exit clause, SLA remedies]

**Next steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

---

*Evaluation completed by: _______________  Date: _______________*
*Approved by: _______________  Date: _______________*
