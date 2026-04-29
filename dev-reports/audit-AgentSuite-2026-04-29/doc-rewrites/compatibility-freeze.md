# Compatibility Freeze — Replacement Copy (drop-in for CHANGELOG and README)

> **Use this block** in three places to replace the current contradictory text:
>
> 1. `CHANGELOG.md` — `## [1.0.0]` "Compatibility (carried forward from 1.0.0rc1)" section.
> 2. `CHANGELOG.md` — `## [1.0.0rc1]` "Compatibility" section.
> 3. `README.md` — replace any narrative that names the pipeline stage count.

The current text is wrong on two load-bearing facts:
1. Pipeline stage count: `agentsuite/kernel/base_agent.py` defines `PIPELINE_ORDER = ["intake", "extract", "spec", "execute", "qa"]` — **five stages**. `approval` is a post-pipeline gate handled by the kernel after the stage loop completes. The `done` value also exists in the `Stage` literal as a terminal marker. Calling it "six stages (intake → extract → spec → execute → qa → approval)" misrepresents the contract you're freezing.
2. MCP tool naming: v0.8.2 renamed all primary tools to `agentsuite_<agent>_<verb>` (per ADR-0004 and the `agentsuite/agents/<name>/mcp_tools.py` `register_tools()` calls). The compatibility section currently says `<agent>_run` / `<agent>_resume` / `<agent>_approve`, which is the v0.8.1 surface that was deprecated in v0.8.2.
3. Public API surface list: the current text claims `ArtifactRef`, `Cost`, `Stage`, `QARubric`, `RubricDimension`, `MockLLMProvider` are part of the locked public surface, but `agentsuite/__init__.py` does **not** re-export those names. Either re-export them in `__init__.py` (and add tests pinning the surface) or remove them from the freeze.

---

## Replacement copy

### Compatibility — locked from 1.0.0rc1 onward

The following are part of the public contract from 1.0.0 onward; breaking changes require an explicit major-version bump or a documented deprecation cycle.

**Public API surface (re-exported from `agentsuite/__init__.py`)**

The names listed below are guaranteed to import from the top-level `agentsuite` package. Internal modules (`agentsuite.kernel.*`, `agentsuite.llm.*`, `agentsuite.agents.*.input_schema`) remain importable but are not part of the locked surface — names there may be renamed or moved in a minor release.

- Agent classes: `FounderAgent`, `DesignAgent`, `ProductAgent`, `EngineeringAgent`, `MarketingAgent`, `TrustRiskAgent`, `CIOAgent`.
- Kernel base types: `BaseAgent`, `AgentRequest`, `RunState`, `ArtifactWriter`.
- Registry: `AgentRegistry`, `default_registry`.
- Provider plumbing: `LLMProvider`, `ProviderNotInstalled`, `NoProviderConfigured`, `resolve_provider`.
- Module metadata: `__version__`.

> **Deferred to v1.1.0:** the rc1 compatibility section additionally named `ArtifactRef`, `Cost`, `Stage`, `QARubric`, `RubricDimension`, and `MockLLMProvider` as locked. They are *importable* from their kernel/llm submodules but were never re-exported at top-level. v1.1.0 will either add them to `agentsuite/__init__.py` and ship a `tests/test_public_api.py` pin, or drop them from this list. They are tracked in [issue TBD] and not part of the v1.0.0 freeze.

**Persisted state schema**

`_state.json` carries `schema_version: 2`. Future shape changes ship a migrator or raise `RunStateSchemaVersionError` with a documented remediation path (per ADR-0002 + ADR-0007).

**MCP tool naming (per ADR-0004)**

All primary MCP tools are namespaced as:

```
agentsuite_<agent>_run
agentsuite_<agent>_resume
agentsuite_<agent>_approve
agentsuite_<agent>_get_status
agentsuite_<agent>_list_runs
```

Optional per-stage tools (gated by `AGENTSUITE_EXPOSE_STAGES=true`) follow:

```
agentsuite_<agent>_stage_<stage>     # stage ∈ {intake, extract, spec, execute, qa}
```

Cross-agent tools are unprefixed-but-namespaced to `agentsuite_`:

```
agentsuite_list_agents
agentsuite_kernel_artifacts
agentsuite_cost_report
```

**Kernel pipeline**

The `BaseAgent._drive()` loop walks **five stages** in this fixed order:

```
intake → extract → spec → execute → qa
```

After the loop, the kernel transitions the run into either `approval` (when QA scores below the rubric pass threshold) or `done` (when QA passes). `approval` and `done` are kernel-managed states, not pipeline stages — agents do not implement handlers for them. Stage names are part of the public contract; reordering or splitting requires the same deprecation discipline as an API change.

The `Stage` literal in `agentsuite/kernel/schema.py` enumerates all seven values (`intake`, `extract`, `spec`, `execute`, `qa`, `approval`, `done`) for typing purposes; only the first five are pipeline stages.
