# Release Checklist

## Release
**System:** {{ system_name }}
**Version:** vX.X.X
**Release Manager:** _______________
**Release Window:** _______________  (UTC)
**Rollback Deadline:** _______________  (UTC — after this, hotfix instead of rollback)

---

## Pre-Release Checks

All items must be checked before the release window opens. No exceptions.

### Code & Testing
- [ ] Full test suite is green on the release branch (paste CI link: _______________)
- [ ] All acceptance criteria for included tickets verified in staging
- [ ] Performance test completed — no regression vs. baseline (link: _______________)
- [ ] Security scan completed — no new HIGH or CRITICAL findings (link: _______________)
- [ ] No `TODO`, `FIXME`, or `HACK` comments introduced in this release

### Data & Migrations
- [ ] Database migrations reviewed by DBA or senior engineer
- [ ] Migrations are backward-compatible (old code can run against new schema)
- [ ] Migration dry-run executed in staging — estimated duration: _______________
- [ ] Rollback migration scripted and tested

### Documentation
- [ ] CHANGELOG.md updated with all user-facing changes
- [ ] API documentation updated if public interface changed
- [ ] Runbooks updated for any new operational behavior
- [ ] README version number updated

### Deployment Readiness
- [ ] Staging environment verified — matches production config
- [ ] Rollback plan written and reviewed (see Rollback Procedure below)
- [ ] Feature flags configured for staged rollout (if applicable)
- [ ] Oncall team briefed on what's changing and what to watch

### Stakeholder Notification
- [ ] Engineering team notified of release window
- [ ] Customer-facing teams notified if behavior changes for users
- [ ] Status page update scheduled (if applicable)

---

## Release Steps

Execute in order. Do not skip steps. Record actual times.

1. [ ] **Open maintenance window** — update status page: _______________
2. [ ] **Create release tag:** `git tag -a vX.X.X -m "Release vX.X.X"`
3. [ ] **Run pre-deploy smoke test** against production (read-only): _______________
4. [ ] **Execute database migrations** — start: _______________ end: _______________
5. [ ] **Deploy to 10% of traffic** (canary): _______________
6. [ ] **Monitor canary for 10 minutes** — error rate: _____ latency p99: _____
7. [ ] **Deploy to 100% of traffic**: _______________
8. [ ] **Run post-deploy smoke tests**: _______________
9. [ ] **Close maintenance window**: _______________

**Tech stack:** {{ tech_stack }}
**Scale context:** {{ scale_requirements }}

---

## Post-Release Verification

Complete within 30 minutes of full deployment.

- [ ] Error rate is at or below pre-release baseline
- [ ] p99 latency is at or below pre-release baseline
- [ ] Key user flows verified in production (list below)
- [ ] No new alerts firing that weren't present before release
- [ ] Database migration completed cleanly — no lock timeout or deadlock logged

**Key flows verified:**
1. _______________
2. _______________
3. _______________

---

## Rollback Procedure

Use if post-release error rate exceeds 1% or p99 latency exceeds SLO within 60 minutes.

1. [ ] Notify oncall lead and engineering manager
2. [ ] Revert deploy to previous version: [command / runbook link]
3. [ ] If migrations ran: execute rollback migration: [command / runbook link]
4. [ ] Verify previous version is serving traffic correctly
5. [ ] Update status page — incident in progress
6. [ ] File incident report (use incident-report template)

**Rollback authorized by:** _______________
**Rollback executed by:** _______________

---

**Team:** {{ team_size }}

*Release sign-off: _______________  Date/Time (UTC): _______________*
