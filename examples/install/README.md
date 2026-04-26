# AgentSuite MCP install snippets

These are reference snippets for wiring `agentsuite-mcp` into different AI coding harnesses.

## Codex

Copy `codex.mcp.toml` content into `~/.codex/mcp.toml`. Restart Codex.

## Claude Code

Copy `claude-code.mcp.json` content into your project-root `.mcp.json` (or merge into an existing one). Restart Claude Code.

## Cowork

Same `.mcp.json` shape as Claude Code. Drop it in the workspace root.

## API keys

Never put API keys in the harness config files. Set them in your shell environment:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...
```

## Verifying the install

After restarting your harness, ask it: "List the agentsuite tools available." It should report `founder_run`, `founder_approve`, etc.
