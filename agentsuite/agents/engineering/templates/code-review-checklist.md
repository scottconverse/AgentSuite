# Code Review Checklist

## PR Information
| Field | Value |
|-------|-------|
| System | {{ system_name }} |
| Component | {{ component }} |
| PR Author | |
| Reviewer | |
| Review Date | |
| PR Link | |

---

## Functionality
- [ ] The code does what the ticket/PR description says it does
- [ ] Edge cases and boundary conditions are handled correctly
- [ ] Error conditions produce clear, actionable error messages
- [ ] No regression in existing behavior (check blast radius)
- [ ] The implementation matches the agreed acceptance criteria

---

## Tests
- [ ] Unit tests cover the new/changed logic paths
- [ ] Integration tests updated where API surface changed
- [ ] Edge cases and failure modes are tested explicitly
- [ ] Code coverage does not decrease from baseline
- [ ] Tests are self-contained (no dependency on external state or ordering)

---

## Security
- [ ] All inputs are validated and sanitized before use
- [ ] Authentication and authorization checks are in place and correct
- [ ] No secrets, credentials, or internal URLs appear in the diff
- [ ] OWASP Top 10 concerns reviewed for this change (XSS, SQLi, CSRF, etc.)
- [ ] Dependency changes audited for known CVEs

---

## Performance
- [ ] No N+1 query patterns introduced
- [ ] No blocking I/O on the main thread (or hot paths) without justification
- [ ] Memory allocations in hot paths are intentional and bounded

---

## Docs & Comments
- [ ] Public APIs, functions, and classes have accurate docstrings
- [ ] Inline comments explain *why*, not *what* (code should explain what)
- [ ] README, ADR, or runbook updated if behavior visible to operators changed

---

## Tech Stack Alignment
{{ tech_stack }}

Scale context: {{ scale_requirements }}

---

## Reviewer Notes
[Free-form observations, questions, or suggestions not captured in the checklist above]

---

## Reviewer Sign-off

| Reviewer | Decision | Date | Comment |
|----------|----------|------|---------|
| | [ ] Approved  [ ] Request Changes  [ ] Comment | | |
| | [ ] Approved  [ ] Request Changes  [ ] Comment | | |
