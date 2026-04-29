<!--
Replacement for README.md MCP quick-start sections.
Fixes:
  - trust-risk hyphen -> trust_risk underscore (registry key, agentsuite/mcp_server.py:24)
  - MCP tool names use the agentsuite_ prefix (per ADR-0004)
  - Adds explicit Naming-Conventions paragraph
-->

## Quick start (MCP - Codex)

Add to `~/.codex/mcp.toml`:

```toml
[servers.agentsuite]
command = "uvx"
args = ["agentsuite-mcp"]

[servers.agentsuite.env]
AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust_risk,cio"
```

Restart Codex. Tools `agentsuite_founder_run`, `agentsuite_founder_approve`, `agentsuite_founder_get_status`, `agentsuite_founder_list_runs`, `agentsuite_founder_resume`, plus the cross-agent `agentsuite_list_agents`, `agentsuite_kernel_artifacts`, and `agentsuite_cost_report` are now callable. Each enabled agent contributes its own `agentsuite_<agent>_*` tool family - see ADR-0004.

## Quick start (MCP - Claude Code / Cowork)

Add to project-root `.mcp.json`:

```json
{
  "mcpServers": {
    "agentsuite": {
      "command": "uvx",
      "args": ["agentsuite-mcp"],
      "env": {"AGENTSUITE_ENABLED_AGENTS": "founder,design,product,engineering,marketing,trust_risk,cio"}
    }
  }
}
```

Restart the harness.

### Naming conventions

AgentSuite agent names use **hyphens in CLI subcommands** (`agentsuite trust-risk run`) and **underscores everywhere else** - env-var values, MCP tool prefixes, Python imports (`agentsuite.agents.trust_risk`). The CLI translates. If you see `UnknownAgent: trust-risk`, check that `AGENTSUITE_ENABLED_AGENTS` uses the underscore form. See [troubleshooting](docs/troubleshooting.md) section 2.
