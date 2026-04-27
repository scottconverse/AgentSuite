# On-Call Handoff

## System
{{ system_name }}

## Handoff Details
| Field | Value |
|-------|-------|
| Outgoing oncall | |
| Incoming oncall | |
| Handoff time (UTC) | |
| Rotation end | |
| Team size | {{ team_size }} |

---

## Active Incidents

### Open Incidents
| Incident | Severity | Status | Owner | Started | Slack / ticket |
|----------|----------|--------|-------|---------|----------------|
| | | | | | |

**If no active incidents:** System is green. No open incidents at handoff time.

### Mitigated but Watching
| Issue | Context | What to Watch | Runbook |
|-------|---------|---------------|---------|
| | | | |

---

## Monitoring Links

| Dashboard | URL | What it shows |
|-----------|-----|---------------|
| Primary APM | | Latency, error rate, throughput |
| Infrastructure | | CPU, memory, disk, network |
| Alerting | | Active alerts and silences |
| Log aggregation | | Structured logs, error spikes |
| Database | | Query perf, replication lag, connections |
| On-call schedule | | Who's next in rotation |

**Alert routing:** [Where do pages land? PagerDuty / OpsGenie / Slack — channel name]

**Scale context:** {{ scale_requirements }}

---

## Pending Work

### In Progress (do not interrupt without discussion)
| Task | Owner | ETA | Context |
|------|-------|-----|---------|
| | | | |

### Queued for This Rotation
| Task | Priority | Runbook / ticket | Notes |
|------|----------|-----------------|-------|
| | | | |

---

## Known Issues (not yet incidents)
| Issue | Severity | Workaround | Tracking ticket |
|-------|----------|------------|----------------|
| | | | |

---

## Recent Changes

Changes deployed in the last 72 hours — highest regression risk.

| Time (UTC) | Change | Deployed by | Rollback plan |
|------------|--------|-------------|---------------|
| | | | |

**Tech stack:** {{ tech_stack }}

---

## Emergency Contacts

| Role | Name | Contact | When to page |
|------|------|---------|-------------|
| Escalation (oncall lead) | | | P1 / no response in 15 min |
| Database owner | | | DB incidents, data integrity |
| Security | | | Suspected breach, data exposure |
| Product owner | | | User-facing outage > 30 min |
| Vendor support | | | [Vendor name + contract SLA] |

---

## Escalation Path

1. **First response:** Incoming oncall (you)
2. **No resolution in 15 min:** Page oncall lead
3. **No resolution in 30 min:** Page engineering manager
4. **Customer impact confirmed:** Notify product owner immediately; post in #incidents

---

## Runbook Index

| Scenario | Runbook location |
|----------|-----------------|
| Service restart | |
| Database failover | |
| Cache flush | |
| Rollback deploy | |
| Scaling up compute | |
| Credential rotation | |

---

**Outgoing oncall sign-off:** _______________  Time: _______________
**Incoming oncall acknowledged:** _______________  Time: _______________
