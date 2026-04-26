# AgentSuite

> Seven role-specific reasoning agents that turn vague intent into precise operating artifacts.
>
> **v0.1.0** — Specification Kernel + Founder Agent

AgentSuite is a Python package and MCP server. It exposes role-specific agents (Founder first; Design, Product, Engineering, Marketing, Trust/Risk, and CIO in subsequent releases) that take loose human intent and produce structured, reusable artifacts: brand systems, brief libraries, voice guides, prompt templates, and more.

The agents are reasoning agents, not content generators. Output is a reusable system, not a one-off asset.

## Why this exists

Modern AI tools generate fast. They do not generate *consistently*. Without a reusable brand system and brief library, every new asset re-introduces context, drifts on voice, and slowly turns into generic SaaS copy. AgentSuite codifies the operating system around generation: every agent persists its output to disk, runs through a six-stage pipeline (intake → extract → spec → execute → qa → approval), and promotes approved artifacts into a long-lived `_kernel/` that downstream agents consume.

## Install

```bash
pip install agentsuite
# or, no install:
uvx agentsuite-mcp
```

Requirements: Python 3.11+. One of `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` (also accepts `GOOGLE_API_KEY`) set in your environment.

## Quick start (CLI)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
agentsuite founder run \
  --business-goal "Launch PatentForgeLocal v1" \
  --project-slug pfl \
  --inputs-dir ./examples/patentforgelocal
```

The agent walks five stages, writes 26 artifacts under `.agentsuite/runs/<run-id>/`, and pauses at the approval gate. Review `brand-system.md` + `qa_report.md`, then:

```bash
agentsuite founder approve --run-id <run-id> --approver you --project-slug pfl
```

Approved artifacts get promoted to `.agentsuite/_kernel/pfl/` for downstream agents.

## Quick start (MCP — Codex)

Add to `~/.codex/mcp.toml`:

```toml
[servers.agentsuite]
command = "uvx"
args = ["agentsuite-mcp"]

[servers.agentsuite.env]
AGENTSUITE_ENABLED_AGENTS = "founder"
```

Restart Codex. Tools `founder_run`, `founder_approve`, `founder_get_status`, `founder_list_runs`, `founder_resume`, plus the cross-agent `agentsuite_list_agents`, `agentsuite_kernel_artifacts`, `agentsuite_cost_report` are now callable.

## Quick start (MCP — Claude Code / Cowork)

Add to project-root `.mcp.json`:

```json
{
  "mcpServers": {
    "agentsuite": {
      "command": "uvx",
      "args": ["agentsuite-mcp"],
      "env": {"AGENTSUITE_ENABLED_AGENTS": "founder"}
    }
  }
}
```

Restart the harness.

## What the Founder agent produces

26 artifacts per run:

| Stage | Artifacts |
|---|---|
| 1 intake | `inputs_manifest.json` |
| 2 extract | `extracted_context.json` |
| 3 spec | `brand-system.md`, `founder-voice-guide.md`, `product-positioning.md`, `audience-map.md`, `claims-and-proof-library.md`, `visual-style-guide.md`, `campaign-production-workflow.md`, `asset-qa-checklist.md`, `reusable-prompt-library.md`, `consistency_report.json` |
| 4 execute | `brief-template-library/` (11 brief templates) + `export-manifest-template.json` |
| 5 qa | `qa_report.md`, `qa_scores.json` |
| state | `_state.json`, `_meta.json` |

On `founder_approve`, the spec artifacts + brief-template-library are promoted to `.agentsuite/_kernel/<project_slug>/` for use by downstream agents (Design, Product, Marketing — coming in v0.2 onward).

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `AGENTSUITE_ENABLED_AGENTS` | `founder` | Comma-separated agent names to expose |
| `AGENTSUITE_OUTPUT_DIR` | `.agentsuite` | Where artifacts are written |
| `AGENTSUITE_LLM_PROVIDER` | (auto-detect) | Force `anthropic`, `openai`, or `gemini` |
| `AGENTSUITE_COST_CAP_USD` | `5.0` | Hard kill cap per run |
| `AGENTSUITE_EXPOSE_STAGES` | (off) | Set `true` to expose `founder_intake`/`extract`/`spec`/`execute`/`qa` as MCP tools |

## Architecture

```
                    ┌───────────────┐
                    │  Harness      │  (Codex / Claude Code / Cowork)
                    └─────┬─────────┘
                          │ stdio MCP
                    ┌─────▼─────────┐
                    │ agentsuite-mcp│
                    └─────┬─────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
        ┌─────▼──────┐         ┌──────▼──────┐
        │  Kernel    │◄────────│ FounderAgent│
        │            │         │             │
        │ schema/    │         │ stages/     │
        │ qa/        │         │ rubric.py   │
        │ cost/      │         │ templates/  │
        │ artifacts/ │         │ prompts/    │
        │ approval/  │         └─────────────┘
        │ base_agent │
        └────────────┘
```

Full architecture diagram with all agents: see `docs/README-FULL.pdf`.

## Status

v0.1.0 ships the kernel + Founder agent. Roadmap:

- v0.2.0 — Design Agent (brief generation, brand QA scoring)
- v0.3.0 — Product Agent (PM intent → UI spec → coding handoff)
- v0.4.0 — Engineering Agent (annotated bug reports, PR review visuals)
- v0.5.0 — Marketing Agent (multilingual localization briefs)
- v0.6.0 — Trust/Risk Agent (synthetic-evidence red team)
- v0.7.0 — CIO Agent (vendor capability decomposition)

## Documentation

- [USER-MANUAL.md](docs/USER-MANUAL.md) — plain-language walkthrough
- [README-FULL.pdf](docs/README-FULL.pdf) — full reference with architecture diagrams
- [CONTRIBUTING.md](CONTRIBUTING.md) — dev setup + agent-implementation guide
- [CHANGELOG.md](CHANGELOG.md) — release notes

## License

MIT — see [LICENSE](LICENSE).