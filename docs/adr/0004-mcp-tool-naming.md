# ADR-0004: MCP tool naming convention

**Status:** Accepted
**Date:** 2026-04-28

## Context

AgentSuite exposes each agent over the Model Context Protocol so Codex,
Claude Code, and Cowork can call them as tools. Through v0.8.1 the tools
were named after their verbs only (`founder_run`, `founder_stage_intake`,
`design_run`, etc.). When a host registered AgentSuite alongside other MCP
servers, naming collisions and ambiguous trigger words ("which `run` did
the user mean?") became likely.

## Decision

All MCP tools are namespaced as `agentsuite_<agent>_<verb>` for primary
tools and `agentsuite_<agent>_stage_<stage>` for per-stage tools. The
prefix is `agentsuite_`, not the looser `as_` or `agent_`, because the
prefix is what disambiguates AgentSuite from any other MCP server in the
host's tool list. v0.8.2 ships the rename as a `BREAKING:` change with no
alias shim — the pre-rename surface had no known external adopters and
shipping an alias-then-deprecation cycle in a pre-1.0 product earns
maintenance cost it doesn't repay.

## Consequences

- New agents inherit the convention automatically: `agentsuite_<name>_run`
  for the primary, `agentsuite_<name>_stage_<stage>` for per-stage tools.
- Hosts that registered the v0.8.1 surface must update their tool
  configuration. The v0.8.2 CHANGELOG `BREAKING:` line is the
  authoritative migration note.
- Future protocol versions of MCP that introduce explicit namespaces
  (vs. flat tool names) may make this prefix redundant. When that
  happens, supersede this ADR rather than dropping the prefix unilaterally.
