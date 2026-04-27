# A/B Test Plan — {{ product_name }}

**Test name:** ___  **Owner:** ___  **Status:** [ ] Draft  [ ] Approved  [ ] Running  [ ] Complete
**Proposed start:** ___  **Proposed end:** ___

---

## Hypothesis

> We believe **{{ key_feature }}** will improve **{{ success_metric_goals }}**
> for **{{ target_users }}**
> because **___ [the mechanism / reasoning]**.

**If true, we will:** ___

**If false, we will:** ___

---

## Background

**Problem or opportunity:** {{ core_problem }}

**What prompted this test (data, qualitative signal, prior experiment):**

___

**Prior experiments on this surface (results):**

___

---

## Control vs. Variant

| | Control (A) | Variant (B) |
|---|-------------|-------------|
| **Description** | Current experience | ___ |
| **Screenshot / mockup** | [link] | [link] |
| **Key difference** | — | ___ |

**Additional variants (if multivariate):**

| Variant | Description | Hypothesis |
|---------|-------------|------------|
| C       |             |            |
| D       |             |            |

---

## Metrics

### Primary Metric

| Metric | Definition | Baseline | Target Lift | Direction |
|--------|------------|----------|-------------|-----------|
|        |            |          |             | ↑ increase |

*Why this is the right primary metric:*

___

### Secondary Metrics

| Metric | Definition | Baseline | Expected Direction |
|--------|------------|----------|--------------------|
|        |            |          |                    |
|        |            |          |                    |
|        |            |          |                    |

### Guardrail Metrics (must not regress)

| Metric | Threshold | Action if breached |
|--------|-----------|-------------------|
|        |           | Pause test         |
|        |           | Pause test         |

---

## Sample Size & Duration

**Statistical significance target:** 95%  **Statistical power:** 80%

**Minimum detectable effect (MDE):** ___

**Required sample size per variant:** ___  (calculated via: ___)

**Daily eligible users:** ___

**Estimated duration:** ___ days

**Timeline constraint:** {{ timeline_constraint }}

---

## Targeting

**Eligible population:** {{ target_users }}

**Inclusion filters:**

- ___
- ___

**Exclusion filters:**

- ___
- ___

**Traffic split:** Control ___ % / Variant ___ %

**Randomization unit:** [ ] User  [ ] Session  [ ] Device  [ ] Account

---

## Risks & Guardrails

| Risk | Likelihood (H/M/L) | Mitigation |
|------|-------------------|------------|
| Network effect (users interact across variants) | | |
| Novelty effect (short-term behavior change) | | |
| Seasonal confound | | |
| Instrumentation failure | | |
| ___ | | |

**Early-stopping criteria (pre-defined):**

___

---

## Success Threshold

**We will ship the variant if:**

- Primary metric improves by ≥ ___ % with p < 0.05
- No guardrail metric regresses beyond ___
- Test runs for ≥ ___ days (avoids novelty bias)

**We will iterate if:**

___

**We will abandon if:**

___

---

## Launch Plan (if variant wins)

**Rollout:** ___ % → ___ % → 100% over ___ days

**Monitoring period post-ship:** ___ days

**Owner for post-ship monitoring:** ___

---

## Approvals

| Role | Name | Status | Date |
|------|------|--------|------|
| PM |      | ☐ Approved | |
| Data / Analytics |  | ☐ Approved | |
| Eng Lead |  | ☐ Approved | |

---

*Template version: 1.0 — AgentSuite Product Agent*
