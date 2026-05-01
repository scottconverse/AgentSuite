# Engineering Deep-Dive Audit — AgentSuite v1.0.1
**Auditor role:** Principal Engineer  
**Date:** 2026-04-30  
**Posture:** Balanced (credit where due, sharp where warranted)  
**Scope:** Architecture correctness · Security · Data flow · Dependency hygiene · Performance · Error handling · Type safety

---

## TL;DR

AgentSuite v1.0.1 is a structurally sound Python project with commendable discipline in atomic state management, cost-cap enforcement, and LLM provider abstraction. The ENG-001 path-traversal fix landed cleanly in the kernel write/promote path. However, the blast radius of that fix was not fully traced: **the MCP-layer read paths and the cross-agent shared tool `agentsuite_kernel_artifacts` both accept user-supplied string identifiers and build filesystem paths from them without calling the new validators.** This is the dominant finding. Two Critical findings, one Major, four Minor, and one Nit are recorded below.

---

## Severity Roll-Up

| Severity | Count | IDs |
|----------|-------|-----|
| Blocker  | 0     | —   |
| Critical | 2     | ENG-001, ENG-002 |
| Major    | 1     | ENG-003 |
| Minor    | 4     | ENG-004, ENG-005, ENG-006, ENG-007 |
| Nit      | 1     | ENG-008 |

---

## What's Working Well

These are genuine engineering strengths, not pro forma credits:

1. **Atomic state writes** — `StateStore.save()` uses `tempfile.mkstemp` + `os.fsync` + `os.replace`. This is correct crash-safe write discipline; most projects in this weight class skip it.
2. **Cost-cap design** — `CostCap`, `HardCapExceeded`, and the `$10` live-test cap are first-class concepts, not afterthoughts. `CostCap.from_env()` is the right design; only its error path is missing (see ENG-005).
3. **Resume idempotency contract** — Stage transitions are guarded by `state.stage` checks and the `SCHEMA_VERSION = 2` gate. `RunStateSchemaVersionError` is a proper typed exception.
4. **MockLLMProvider longest-match semantics** — Length-descending keyword sort prevents shorter keys from shadowing longer ones. This is subtle and correct.
5. **CI pipeline** — Lint + test + provider-drift (weekly, auto-opens issue) + release (pip-audit) covers the bases for a solo-maintained open-source project at this scale.
6. **Schema versioning** — `SCHEMA_VERSION` in persisted JSON + typed exception on mismatch prevents silent data corruption across upgrades.
7. **`_resolve_safe` in ArtifactWriter** — Null-byte check + `is_relative_to` guard is layered correctly. The parametrized test suite for traversal paths is thorough.
8. **Terminal output discipline** — `AGENTSUITE_QUIET` env + `_emit_stage_progress()` keeps stdout clean for MCP stdio transport.

---

## What Couldn't Be Assessed

- **Live provider correctness** — No live credentials in audit environment. Anthropic/OpenAI/Gemini/Ollama responses untested.
- **Production telemetry** — `cost_summary.json` format and accuracy depend on real usage; only schema was reviewed.
- **pip-audit current state** — Release workflow runs pip-audit but no recent run output was available for review.
- **Windows path semantics** — Backslash traversal tests are `skipif(platform != "win32")` and could not be exercised in this session.

---

## Findings

---

### ENG-001 [CRITICAL] — `get_status` across all 7 agents accepts unvalidated `run_id`

**File:** `agentsuite/agents/founder/mcp_tools.py` lines 74, 80, 101, 138  
Same pattern confirmed in: `design/mcp_tools.py:97`, `engineering/mcp_tools.py:95`, `marketing/mcp_tools.py:95`, `product/mcp_tools.py:98`, `trust_risk/mcp_tools.py:149`, `cio/mcp_tools.py:153`

**Evidence:**
```python
def founder_get_status(run_id: str) -> RunState:
    run_dir = output_root_fn() / "runs" / run_id   # NO validate_run_id()
    state = StateStore(run_dir=run_dir).load()
```

The v1.0.1 ENG-001 fix correctly calls `validate_run_id(run_id)` inside `ArtifactWriter.__init__` (kernel write path). It does **not** call it in the MCP read path. An MCP caller supplying `run_id="../../etc"` causes `run_dir` to resolve outside `.agentsuite/runs/`, and `StateStore.load()` will attempt to read `../../etc/_state.json`. If that path exists and contains valid JSON, it is deserialized and returned to the caller. If it does not exist, `load()` returns `None` and `get_status` raises a generic `RuntimeError("Run not found")` — which leaks the resolved path in the error message on some Python versions.

**Why this matters:** The MCP interface is the primary attack surface for untrusted input. `run_id` arrives from any Codex / Claude Code client. Path traversal on read is lower severity than on write (no data corruption), but can expose filesystem contents and internal paths.

**Blast radius:** All 7 agents' `get_status` tools. All 4 stage-kick tools that also build `run_dir` from `run_id` without validation (`founder_run_intake`, `founder_run_extract`, etc.).

**Fix path:**
```python
from agentsuite.kernel.identifiers import validate_run_id

def founder_get_status(run_id: str) -> RunState:
    validate_run_id(run_id)           # add this line
    run_dir = output_root_fn() / "runs" / run_id
    state = StateStore(run_dir=run_dir).load()
```
Apply identically to all 7 agents' `mcp_tools.py`. A shared helper `_require_run_dir(run_id, output_root_fn)` in `agentsuite/agents/_common.py` would DRY this across all agents.

---

### ENG-002 [CRITICAL] — `agentsuite_kernel_artifacts` accepts unvalidated `project_slug`

**File:** `agentsuite/mcp_server.py` lines 100–111

**Evidence:**
```python
def agentsuite_kernel_artifacts(project_slug: str) -> dict[str, Any]:
    kernel_dir = _output_root() / "_kernel" / project_slug  # NO validate_project_slug()
    if not kernel_dir.exists():
        return {"artifacts": []}
    return {
        "artifacts": sorted(
            str(p.relative_to(kernel_dir))
            for p in kernel_dir.rglob("*")
            if p.is_file()
        )
    }
```

With `project_slug = "../../"`:
- `kernel_dir` = `.agentsuite/_kernel/../../` = project root
- `kernel_dir.exists()` → True
- `kernel_dir.rglob("*")` → lists every file in the project tree
- `p.relative_to(kernel_dir)` → returns paths like `agentsuite/kernel/state_store.py`, `pyproject.toml`, `.env` (if present)
- All file names returned as strings to the MCP caller

This is a directory traversal on a shared cross-agent MCP tool that returns file listings to unauthenticated callers. Unlike ENG-001 (which exposes content only when a valid JSON file exists at the traversed path), this one **always enumerates the filesystem** if the traversed path exists.

**Fix path:**
```python
from agentsuite.kernel.identifiers import validate_project_slug

def agentsuite_kernel_artifacts(project_slug: str) -> dict[str, Any]:
    validate_project_slug(project_slug)           # add this line
    kernel_dir = _output_root() / "_kernel" / project_slug
    ...
```

---

### ENG-003 [MAJOR] — Intake stage reads arbitrary filesystem paths supplied via `inputs_dir` / `brand_docs` / `screenshots`

**Files:** `agentsuite/agents/founder/stages/extract.py`, `agentsuite/agents/founder/input_schema.py`, `agentsuite/agents/design/input_schema.py` (and equivalents for all 7 agents)

**Evidence — schema definition:**
```python
class FounderAgentInput(BaseModel):
    inputs_dir: Path | None = None
    explicit_brand_docs: list[Path] = Field(default_factory=list)
    founder_voice_samples: list[Path] = Field(default_factory=list)
    screenshots: list[Path] = Field(default_factory=list)
```

**Evidence — intake reads up to 1,500 chars from each path into the LLM prompt:**
```python
if path.exists() and path.is_file():
    snippet = path.read_text(encoding="utf-8", errors="replace")[:1500]
    lines.append(f"[{kind}] {path}\n{snippet}\n")
```

An MCP caller supplying `inputs_dir="/etc"` or `explicit_brand_docs=["/etc/passwd"]` causes the agent to read and include the content of arbitrary files in the LLM prompt. The prompt content is returned to the caller (indirectly via LLM output) and also written to `.agentsuite/runs/<run_id>/inputs_manifest.json`.

This is distinct from path traversal (ENG-001/002): the caller is not bypassing a directory guard, they are supplying a legitimate absolute path that the code intentionally resolves. The design intent is to allow users to point at local documents. The security gap is that there is no restriction on what paths are allowed — specifically, no check that paths are beneath a user-controlled root or that they are not system files.

**Blast radius:** All 7 agents accept path-typed fields. Any agent that reads from `inputs_dir` or individual `Path` fields in its extract stage is affected.

**Fix path (defense in depth):**
1. Add path allowlist validation in `FounderRunRequest` (and equivalents): reject paths outside the user-specified `inputs_dir` root or a configurable `AGENTSUITE_INPUT_ROOT` env variable.
2. Add a CONTRIBUTING.md note that `Path` fields in `AgentInput` subclasses require allowlist validation before use.
3. At minimum, add a warning log when an absolute path outside CWD is supplied.

---

### ENG-004 [MINOR] — `RunStateSchemaVersionError` propagates uncaught from `agentsuite_cost_report` and `agentsuite_kernel_artifacts`

**Files:** `agentsuite/mcp_server.py` lines 113–137, `agentsuite/cli.py` (cost/status commands)

**Evidence:**
```python
store = StateStore(run_dir=d)
state = store.load()          # raises RunStateSchemaVersionError if schema < 2
```

`store.load()` raises `RunStateSchemaVersionError` (a `RuntimeError` subclass) for any run directory written by AgentSuite v1.0.0 or earlier. This exception propagates through `agentsuite_cost_report` as an unhandled Python exception, which FastMCP will surface to the MCP client as a tool error with a Python traceback in the message.

Users who upgrade from v1.0.0 to v1.0.1 and have existing run directories will see `agentsuite_cost_report` throw on every call until they manually delete old runs.

**Fix path:**
```python
try:
    state = store.load()
except RunStateSchemaVersionError:
    _log.warning("Skipping legacy run dir %s (schema version mismatch)", d)
    continue
```

---

### ENG-005 [MINOR] — `CostCap.from_env()` raises unhandled `ValueError` on invalid env var

**File:** `agentsuite/kernel/cost.py`

**Evidence:**
```python
raw = os.environ.get("AGENTSUITE_COST_CAP_USD")
if raw is not None:
    hard = float(raw)   # raises ValueError on "ten" or "1,000"
```

Any non-numeric value in `AGENTSUITE_COST_CAP_USD` causes an unhandled `ValueError` at agent startup, with a Python traceback rather than an actionable error message. Given the project's stated goal of clean error messages, this is inconsistent.

**Fix path:**
```python
try:
    hard = float(raw)
except ValueError:
    raise ValueError(
        f"AGENTSUITE_COST_CAP_USD must be a number (e.g. '10.00'), got: {raw!r}"
    ) from None
```

---

### ENG-006 [MINOR] — `OpenAIProvider.default_model()` returns `"gpt-5.4"` which is not a known production model

**File:** `agentsuite/llm/openai.py` line 32

**Evidence:**
```python
def default_model(self) -> str:
    return "gpt-5.4"
```

`"gpt-5.4"` does not appear in OpenAI's documented production model list as of the audit date. The pricing table in `agentsuite/llm/pricing.py` lists it (marked `# Verified: 2026-04-29`) but the provider-drift CI check exists specifically to catch this kind of drift. If this model does not exist on the OpenAI API, every call through `OpenAIProvider` will fail with a 404 from the API unless the caller overrides the model explicitly.

**Fix path:** Verify the model ID against the OpenAI API before the next release. If the ID is correct (e.g., OpenAI released it after the knowledge cutoff), add an integration test. If it is wrong, revert to `"gpt-4o"` or the current recommended chat model and update the pricing table.

---

### ENG-007 [MINOR] — Secrets-scan regex misses Anthropic key format

**File:** `scripts/verify-release.sh`

**Evidence:**  
The secrets scan uses `grep -rE 'sk-[A-Za-z0-9]{20,}'`. Anthropic API keys have the format `sk-ant-api03-<base64url-body>`, e.g.:
```
sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789_-AAAA...
```
The hyphens in `ant-api03-` break the `[A-Za-z0-9]{20,}` match because hyphens are not in the character class. The regex matches `sk-` then requires 20+ consecutive alphanumeric characters, but `ant` is only 3 chars before the next hyphen.

**Fix path:**
```bash
grep -rE 'sk-[A-Za-z0-9_-]{20,}'
```
Or use a dedicated secrets scanner (`truffleHog`, `gitleaks`, `detect-secrets`) rather than a hand-rolled regex.

---

### ENG-008 [NIT] — Inline imports inside hot-path methods

**File:** `agentsuite/kernel/base_agent.py`

**Evidence:**
```python
def _emit_stage_progress(self, ...):
    import os    # inline import on every call
    import sys   # inline import on every call
    ...

def _drive(self, ...):
    ...
    import time  # inside the stage loop
```

Python caches imports after the first call, so this is not a correctness issue. It is a style inconsistency with the rest of the codebase (all other modules import at the top) and misleads readers into thinking the import is conditional or deferred for a reason.

**Fix path:** Move `import os`, `import sys`, and `import time` to the module top-level.

---

## Systemic Observations

**Pattern: ENG-001 fix stopped at the kernel boundary.** The `validate_run_id` and `validate_project_slug` functions were introduced in v1.0.1 and applied in `ArtifactWriter` (kernel write path). The validators were not propagated to the MCP layer (read path) or the shared cross-agent tools. Future security fixes in `kernel/identifiers.py` should trigger a grep sweep for all call sites that build paths from the same user-supplied identifiers.

**Pattern: `Path`-typed Pydantic fields are semantically unrestricted.** Pydantic validates that `Path` is a valid path object, not that it points somewhere safe. Any `list[Path]` field in an `AgentInput` subclass is an implicit arbitrary-read surface if the agent reads from it. A project-level convention (e.g., a `SafePath` type that validates against an allowlist) would prevent this class of issue from recurring.

**Pattern: Error handling at MCP boundaries is inconsistent.** Some tools return structured error dicts; others let Python exceptions propagate. The MCP client experience degrades when it receives a Python traceback instead of a structured error. A thin `@mcp_safe` decorator that catches known exception types and returns structured error responses would enforce consistency.

---

## Dependency Snapshot

| Package | Pinned range | Notes |
|---------|-------------|-------|
| pydantic | ≥2.5,<3 | Correct — v2 API; upper bound prevents v3 surprise |
| tenacity | ≥8.2,<10 | Correct — RetryingLLMProvider uses v8 API |
| typer | ≥0.12,<1 | Correct — CLI scaffold |
| httpx | ≥0.27,<1 | Suspect — no `import httpx` found in `agentsuite/` source. May be an artifact from an earlier design. |
| jinja2 | ≥3.1,<4 | Used in template rendering — appears legitimate |

`httpx` should be audited: if it is not imported in the main package, it should be removed from `[project.dependencies]` or moved to an optional extra. Unnecessary dependencies add install weight and attack surface.

---

## Artifacts Reviewed

- `pyproject.toml` — v1.0.1, dependency matrix
- `agentsuite/kernel/identifiers.py` — ENG-001 fix (validators)
- `agentsuite/kernel/artifacts.py` — `ArtifactWriter`, `_resolve_safe`, `promote`
- `agentsuite/kernel/state_store.py` — `StateStore.save/load`, schema version guard
- `agentsuite/kernel/cost.py` — `CostCap`, `CostTracker`, `HardCapExceeded`
- `agentsuite/kernel/base_agent.py` — `_drive`, `_emit_stage_progress`
- `agentsuite/mcp_server.py` — `build_server`, all cross-agent shared tools
- `agentsuite/agents/founder/mcp_tools.py` — `get_status`, run request tools
- `agentsuite/agents/founder/input_schema.py` — `FounderAgentInput`, `FounderRunRequest`
- `agentsuite/agents/founder/stages/extract.py` — `_summarize_sources`, file read pattern
- `agentsuite/agents/design/input_schema.py` — `DesignAgentInput` path fields
- `agentsuite/agents/registry.py` — `AgentRegistry`, `default_registry`
- `agentsuite/llm/openai.py` — `OpenAIProvider`, `default_model`
- `agentsuite/llm/pricing.py` — `lookup_pricing`, `normalize_model_id`, `OPENAI_PRICING`
- `agentsuite/llm/base.py` — `LLMProvider` Protocol, `LLMRequest`, `LLMResponse`
- `tests/unit/kernel/test_artifacts.py` — traversal test coverage
- `scripts/verify-release.sh` — secrets scan regex
- `.github/workflows/test.yml`, `provider-drift.yml`, `release.yml` — CI configuration
