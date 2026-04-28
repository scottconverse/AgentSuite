# Architecture Decision Records

Brief, dated records of the load-bearing design decisions in AgentSuite. Each
ADR is one page or less — context, decision, consequences. They exist so
future contributors (and future audits) don't have to re-litigate settled
decisions from scratch.

Format follows a shortened [MADR](https://adr.github.io/madr/) shape. New
ADRs get the next sequential number. Older ADRs are not edited in place —
if a decision is reversed, write a new ADR that supersedes the old one and
update the old one's status.

## Index

| #    | Title                                          | Status   |
|------|------------------------------------------------|----------|
| 0001 | [Rubric dimension count and selection](0001-rubric-dimensions.md) | Accepted |
| 0002 | [RunState shape and resume contract](0002-runstate-shape.md) | Accepted |
| 0003 | [LLM retry and timeout policy](0003-retry-timeout-policy.md) | Accepted |
| 0004 | [MCP tool naming convention](0004-mcp-tool-naming.md) | Accepted |
| 0005 | [Cost cap vs. cost telemetry split](0005-cost-cap-vs-telemetry-split.md) | Accepted |
| 0006 | [No-PyPI distribution policy](0006-no-pypi-distribution.md) | Accepted |
| 0007 | [Resume-from-failure idempotency contract](0007-resume-idempotency.md) | Accepted |

## Template

```markdown
# ADR-NNNN: Short title

**Status:** Proposed | Accepted | Superseded by ADR-NNNN | Deprecated
**Date:** YYYY-MM-DD

## Context

What problem prompted this decision? What constraints shaped the choice?

## Decision

The choice that was made, in one or two sentences.

## Consequences

What does this enable, restrict, or commit us to? Both upsides and trade-offs.
```
