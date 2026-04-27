# QA Deep-Dive — AgentSuite

**Auditor:** QA Engineer  
**Date:** 2026-04-27  
**Scope:** Runtime behavior, installation, import chain, pipeline correctness, error paths, cross-platform

---

## Executive Summary

AgentSuite v0.7.0 imports cleanly, all 7 agents register correctly, and the core artifact/state machinery is solid. Two error-path gaps are the headline findings: the CLI does not catch `NoProviderConfigured`, so a first-time user with no API keys configured gets a raw Python traceback instead of an actionable message; and `mcp_server.py:build_server()` swallows agent-load exceptions silently with `except Exception: continue`, making MCP debugging very hard. Additionally, two agents (Engineering, Marketing) have no `approve` CLI command, creating a workflow dead-end for those pipelines. No blockers to core functionality when a provider is configured; the top findings are Critical and Major.

---

## What's Working Well

- **Version**: `agentsuite.__version__` returns `0.7.0` — correct.
- **Import chain**: All three spot-checked agents (`FounderAgent`, `CIOAgent`, `TrustRiskAgent`) plus `MockLLMProvider` import without errors.
- **Registry**: All 7 agents (`cio`, `design`, `engineering`, `founder`, `marketing`, `product`, `trust_risk`) enumerate correctly when `AGENTSUITE_ENABLED_AGENTS` is set.
- **Artifact writer**: Path handling is clean — `ArtifactWriter` uses `pathlib.Path` throughout, `mkdir(parents=True, exist_ok=True)` guards all writes, SHA-256 tracking is correct, idempotent writes work as documented.
- **Resolver error messages**: `NoProviderConfigured` carries a clear, specific message listing all four provider options with exact env var names. The resolver logic (explicit > env > auto-detect) is correct and well-structured.
- **CIO intake stage**: `agentsuite/agents/cio/stages/intake.py` exists and is present.
- **CLI structure**: All 7 agents have `run` subcommands with well-documented options. `list-runs` is present for `trust-risk` and `cio`.

---

## Findings

### Critical

**CRIT-01 — CLI does not catch `NoProviderConfigured`; first-run UX is a raw traceback**

- **File**: `agentsuite/cli.py`, `_resolve_llm_for_cli()` (line 37–49); all `run` commands call this without try/except.
- **Evidence**: `_resolve_llm_for_cli()` calls `resolve_provider()` which raises `NoProviderConfigured` (a `RuntimeError` subclass). No caller in `cli.py` wraps this. A user who installs AgentSuite and runs `agentsuite founder run --business-goal "..."` with no API keys set will receive a Python traceback ending in `agentsuite.llm.resolver.NoProviderConfigured: No provider configured. Set AGENTSUITE_LLM_PROVIDER...`.
- **Blast radius**: All 7 agent `run` commands, all 5 `approve` commands (same `_resolve_llm_for_cli()` call).
- **Fix path**: Wrap `_resolve_llm_for_cli()` in a try/except that calls `typer.echo(f"Error: {e}", err=True); raise typer.Exit(1)`. One change in `_resolve_llm_for_cli()` fixes all callers.

---

**CRIT-02 — `mcp_server.py:build_server()` silently swallows agent-load exceptions**

- **File**: `agentsuite/mcp_server.py`, lines 55–58.
- **Evidence** (source read directly):
  ```python
  for name in enabled:
      try:
          agent_class = registry.get_class(name)
      except Exception:
          continue
  ```
  If `registry.get_class(name)` raises for any reason (import error, missing dependency, bad config), the agent is silently skipped. The MCP server starts with zero tools registered for that agent. No log line, no warning, no way for the operator to know.
- **Blast radius**: MCP-mode deployments (Claude Code / Codex / Cowork integration). An operator could run `agentsuite mcp` and have 3 of 7 agents silently absent, with no diagnostic.
- **Fix path**: Either log a warning (`import logging; logging.warning("Agent %s failed to load: %s", name, e)`) or re-raise after logging. At minimum: `except Exception as e: logging.warning("Skipping agent %s: %r", name, e); continue`.

---

### Major

**MAJ-01 — Engineering and Marketing agents have no `approve` CLI command**

- **File**: `agentsuite/cli.py` — `engineering_app` and `marketing_app` subtrees.
- **Evidence**: `cli.py` defines `@engineering_app.command("run")` (line 203) and `@marketing_app.command("run")` (line 236) but neither subtree has an `approve` command. By contrast, `founder`, `design`, `product`, `trust_risk`, and `cio` all have `approve`.
- **Blast radius**: Any user who runs `agentsuite engineering run` or `agentsuite marketing run` can produce artifacts but has no CLI path to promote them to `_kernel/`. They must call the Python API directly.
- **Fix path**: Add `@engineering_app.command("approve")` and `@marketing_app.command("approve")` matching the pattern from `product_approve_cmd` (lines 190–200).

---

**MAJ-02 — `NoProviderConfigured` is a `RuntimeError` subclass, not caught by Typer's default handler**

- **File**: `agentsuite/llm/resolver.py`, line 16: `class NoProviderConfigured(RuntimeError)`.
- **Evidence**: Typer's default error handling catches `typer.Exit` and `typer.Abort`; unhandled `RuntimeError` subclasses propagate as tracebacks. This compounds CRIT-01 — the error type itself is correct for programmatic use but wrong for CLI surfaces.
- **Fix path**: Either handle in `_resolve_llm_for_cli()` (see CRIT-01 fix) or add a Typer exception handler at app level.

---

### Minor

**MIN-01 — `agentsuite agents` command exposes internal `_registered` private attribute**

- **File**: `agentsuite/cli.py`, line 457: `reg._registered.keys()`.
- **Evidence**: The `agents` command reads `reg._registered` directly, bypassing any future access-control logic on the registry.
- **Fix path**: Add a `registered_names()` public method to the registry class and use that instead.

---

**MIN-02 — `promote()` uses flat `run_dir.iterdir()` — nested run subdirectories are copied as trees but top-level structure may differ from per-agent expectations**

- **File**: `agentsuite/kernel/artifacts.py`, lines 108–119.
- **Evidence**: `promote()` iterates `run_dir` (one level), copies dirs with `copytree` and files with `copy2`. If an agent writes deeply nested relative paths (e.g. `subdir/file.md`), the `subdir` directory lands in `_kernel/<slug>/subdir/file.md` — consistent. However, if two runs promote to the same slug, `shutil.rmtree(dest)` nukes the previous copy of any directory-level artifact before replacing it. Flat file copies (`copy2`) overwrite silently. No merge behavior.
- **Blast radius**: Multi-run promote-to-same-slug workflows lose previous run's directory artifacts without warning.
- **Fix path**: Document the overwrite semantics in the docstring (quick fix) or add a `merge=False` parameter.

---

**MIN-03 — `engineering_run_cmd` and `marketing_run_cmd` do not accept a `project_slug` parameter**

- **File**: `agentsuite/cli.py`, lines 203–233 (engineering), 236–270 (marketing).
- **Evidence**: `founder_run_cmd`, `design_run_cmd`, and `product_run_cmd` all accept `project_slug: Optional[str]`. Engineering and Marketing `run` commands do not, so `_kernel/` promotion is not possible even from the Python API via CLI round-trip.
- **Fix path**: Add `project_slug: Optional[str] = typer.Option(None, ...)` to both commands, consistent with the other agents.

---

### Nits

**NIT-01 — `founder_run_cmd` hardcodes `role_domain="creative-ops"` and `user_request` pattern**

- **File**: `agentsuite/cli.py`, line 69. `user_request=f"build creative ops for {business_goal}"` — the phrase "creative ops" is baked in regardless of what the business goal is.
- The user passed `--business-goal "Launch a SaaS product"` and gets `user_request="build creative ops for Launch a SaaS product"`. Consider using `business_goal` directly.

**NIT-02 — `list-runs` missing for `founder`, `design`, `product`, `engineering`, `marketing`**

- Only `trust-risk` and `cio` have `list-runs`. The other 5 agents have no way to enumerate runs from the CLI. The top-level `agentsuite list-runs` covers all agents but doesn't filter by agent name consistently.

**NIT-03 — `ArtifactWriter.__init__` calls `mkdir` in constructor**

- **File**: `agentsuite/kernel/artifacts.py`, line 26. Side-effecting I/O in `__init__` makes unit-testing harder (requires a real temp dir or mock). Consider lazy `mkdir` on first write.

---

## Runtime Verification Log

| Command | Result | Pass/Fail |
|---|---|---|
| `agentsuite.__version__` | `0.7.0` | PASS |
| `from agentsuite.agents.founder.agent import FounderAgent` | No error | PASS |
| `from agentsuite.agents.cio.agent import CIOAgent` | No error | PASS |
| `from agentsuite.agents.trust_risk.agent import TrustRiskAgent` | No error | PASS |
| `from agentsuite.llm.mock import MockLLMProvider` | No error | PASS |
| Registry with all 7 agents enabled | `['cio', 'design', 'engineering', 'founder', 'marketing', 'product', 'trust_risk']` | PASS |
| `agentsuite/agents/cio/stages/intake.py` exists | EXISTS | PASS |
| `ArtifactWriter` write + SHA roundtrip | path exists, sha256 len 64 | PASS |
| `resolve_provider()` with no keys, no Ollama | `NoProviderConfigured` raised with full message | PASS |
| CLI catches `NoProviderConfigured` gracefully | Raw traceback (no handler) | FAIL — CRIT-01 |
| MCP `build_server()` logs agent load failures | Silent `continue`, no log | FAIL — CRIT-02 |
| `agentsuite engineering approve` command exists | Not present | FAIL — MAJ-01 |
| `agentsuite marketing approve` command exists | Not present | FAIL — MAJ-01 |

---

## Error Path Analysis

### Path 1: No API keys configured (most common first-run failure)
User installs, runs any `agentsuite <agent> run` command → `_resolve_llm_for_cli()` → `resolve_provider()` → `NoProviderConfigured` → **unhandled RuntimeError traceback**. The error message text is correct and actionable, but it's buried in a traceback. A first-time user will not know what to do.

### Path 2: Agent import fails during MCP server startup
`build_server()` calls `registry.get_class(name)` → import error → `except Exception: continue` → agent silently absent from MCP tool list. Operator has no signal. This is only detectable by calling a tool that should exist and getting "unknown tool" back from the MCP host.

### Path 3: Engineering/Marketing pipeline reaches approval stage
Agent `run` produces artifacts, returns state with `stage="approval"`. User tries `agentsuite engineering approve` → `Error: No such command 'approve'`. No path forward without dropping to Python API.

### Path 4: Provider explicitly named but key missing
`AGENTSUITE_LLM_PROVIDER=anthropic` with no `ANTHROPIC_API_KEY` → `NoProviderConfigured("ANTHROPIC_API_KEY not set (provider 'anthropic')")` — message is clear and correct. Same CLI surfacing problem as Path 1.

### Path 5: `promote()` called twice to same slug
Second `promote()` call silently replaces all directory artifacts from the first run. No warning, no merge. This is a data-loss edge case for multi-run workflows.

---

## Cross-Platform Notes

- `ArtifactWriter` uses `pathlib.Path` throughout — forward-slash path sep issues are not present.
- `agentsuite/cli.py` uses `Path(os.environ.get("AGENTSUITE_OUTPUT_DIR", ".agentsuite"))` — clean, platform-neutral.
- The `.venv/Scripts/python.exe` path confirms Windows venv layout is correct and functional.
- `shutil.rmtree` + `shutil.copytree` in `promote()` work cross-platform without issue.
- No hardcoded Unix path separators found in any audited file.
- Windows-specific risk: if `AGENTSUITE_OUTPUT_DIR` is set to a path with spaces, `Path()` handles it correctly (no shell quoting needed).
