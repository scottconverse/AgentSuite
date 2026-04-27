# Capacity Plan

## System
{{ system_name }}

## Planning Period
**Created:** _______________  **Next review:** _______________  **Owner:** _______________

---

## Current State

### Scale Baseline
{{ scale_requirements }}

### Resource Inventory
| Resource | Current Allocation | Current Utilization | Headroom |
|----------|--------------------|---------------------|----------|
| Compute (CPU) | | | |
| Memory | | | |
| Storage (hot) | | | |
| Storage (cold/archive) | | | |
| Network egress | | | |
| Database connections | | | |
| Cache capacity | | | |
| Message queue depth | | | |

### Tech Stack
{{ tech_stack }}

---

## Growth Assumptions

### Business Drivers
[What user growth, feature launches, or product changes are driving load projections?]

### Load Model
| Metric | Current | Growth Rate / Month | Notes |
|--------|---------|---------------------|-------|
| Requests per second (peak) | | | |
| Active users (DAU) | | | |
| Data ingest rate | | | |
| Storage growth | | | |
| API call volume | | | |

---

## Resource Projections

| Resource | Current | 6 months | 12 months | 24 months |
|----------|---------|----------|-----------|-----------|
| Compute nodes | | | | |
| Memory (total) | | | | |
| Storage (total) | | | | |
| Database replicas | | | | |
| CDN / cache nodes | | | | |
| Monthly infra cost ($) | | | | |

**Projection methodology:** [Linear / exponential / seasonal model — describe assumptions]

---

## Scaling Triggers

Define the thresholds that should automatically or manually trigger a scaling action.

| Resource | Warning Threshold | Action Threshold | Response |
|----------|------------------|-----------------|----------|
| CPU utilization | 70% | 85% | Scale out compute |
| Memory utilization | 75% | 90% | Add nodes / optimize |
| Storage utilization | 70% | 85% | Provision additional volume |
| DB connection pool | 80% | 95% | Read replica / connection pooler |
| p99 latency | > 300ms | > 500ms | Cache layer / query optimization |
| Error rate | > 0.1% | > 1% | Incident response |

---

## Cost Projections

| Period | Infrastructure ($) | Licensing ($) | Support ($) | Total ($) |
|--------|-------------------|---------------|-------------|-----------|
| Current (monthly) | | | | |
| 6 months | | | | |
| 12 months | | | | |
| 24 months | | | | |

**Cost optimization opportunities:**
- [Reserved instance / committed use discounts at X-month mark]
- [Data tiering to cold storage after N days]
- [Right-sizing underutilized instances]

---

## Recommendations

### Immediate (0–3 months)
1. [Action — Owner — Cost — Impact]
2. [Action — Owner — Cost — Impact]

### Near-term (3–12 months)
1. [Action — Owner — Cost — Impact]
2. [Action — Owner — Cost — Impact]

### Strategic (12–24 months)
1. [Architecture change or platform migration to support 24-month projections]

---

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Traffic spike beyond projections | Medium | High | Auto-scaling headroom + load shedding |
| Single region outage | Low | Critical | Multi-region failover plan |
| Cost overrun | Medium | Medium | Monthly budget alerts at 80% |

---

**Team:** {{ team_size }}

*Approved by: _______________  Date: _______________*
