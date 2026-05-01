# Sprint 2 — Engineering Deep-Dive

**Audit date:** 2026-04-30
**Role:** Principal Engineer
**Scope audited:** Sprint 2 changes only — commit eb9c175 vs base 63d844f (ENG-002/003/004/005, QA-003/004/005, UX-003/004/006)
**Auditor posture:** Balanced

---

## TL;DR

Sprint 2 lands a clean kernel extraction (ENG-003) that achieves its stated goal: 14 thin wrapper files with zero business logic leaked, and a shared QA/spec kernel that is correct and well-structured. The PYTEST_CURRENT_TEST guard (ENG-002), cost suppression (ENG-005), and ValueError message (QA-003) all work as intended. The primary concerns are: (1) a **security gap** — `check_path_confinement()` exists but is not called in the one place that actually reads user-supplied file paths at spec-stage time (`_read_voice_samples` in founder/stages/spec.py); (2) a **data provenance bug** in `gemini.py` where the cost calculation uses `model` (the request model) but `LLMResponse.model` is populated with the actual Gemini API `model_version` — creating a cost-reporting mismatch; and (3) a **filename bug** in `cio/mcp_tools.py` where `agentsuite_cio_get_qa_scores` reads `qa-scores.json` but the kernel writes `qa_scores.json` (underscore vs hyphen). No Blockers. Two Critical findings.

---

## Severity roll-up (engineering)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 2 |
| Major | 2 |
| Minor | 3 |
| Nit | 2 |

---

## What's working

- **Kernel extraction is architecturally clean.** All 14 agent-level `stages/qa.py` and `stages/spec.py` files are genuinely thin wrappers — they build a config object and call the kernel. Zero business logic leaked into the wrappers. The `QAStageConfig` and `SpecStageConfig` dataclasses are well-designed and cover all the variability (artifact count, key naming, truncation) without requiring inheritance.

- **`check_path_confinement()` is the right primitive.** The function is correctly implemented: `path.resolve()` followed by `is_relative_to(project_dir.resolve())` handles `..` traversal, absolute paths, and path normalization. The error message is actionable. The CIO `agentsuite_cio_get_artifact` MCP tool demonstrates correct usage (line 171 of `cio/mcp_tools.py`).

- **PYTEST_CURRENT_TEST guard (ENG-002) is robust.** The guard at `cli.py:78` correctly fires when `AGENTSUITE_LLM_PROVIDER_FACTORY` is set without `PYTEST_CURRENT_TEST`, and the `RuntimeError` message clearly names the variable, explains the risk, and tells the developer to unset it. The test coverage (test_cli.py lines 423–438) covers both arms.

- **Cost suppression ($0.0000) is correct.** The `base_agent.py:38` condition `if total_usd > 0` is exact — zero-cost Ollama runs suppress the dollar component, non-zero costs always display. Cannot suppress a legitimate cost because a non-zero USD will always be `> 0`.

- **`_stage_to_status()` is consistently applied across all 7 agents.** Every `agent.py` defines an identical 3-line helper and calls it in `run_cmd`. The `mcp_tools.py` files for all agents implement equivalent inline logic (`"awaiting_approval"` is hardcoded directly in `_result_from_state`). Both representations are consistent.

- **`project_slug` filter in `list_runs` is correctly implemented.** All 7 `mcp_tools.py` files use `getattr(state.inputs, "project_slug", None)` before filtering, which correctly handles input schemas that lack `project_slug` (no AttributeError). `None` project_slug skips filtering (return all runs), which is correct behavior.

- **ValueError messages in QA-003 are actionable.** `CostCap.from_env()` produces `"AGENTSUITE_COST_CAP_USD=<value> is not a valid dollar amount. Set it to a number like '5.00'."` — correct variable name, the bad value, and an example fix.

- **Import cycles are absent.** The `agentsuite/kernel/stages/` package only imports from `agentsuite.kernel.base_agent`, `agentsuite.kernel.qa`, `agentsuite.kernel.schema`, and `agentsuite.llm.*`. No upward imports into `agentsuite.agents.*`. Clean dependency direction.

---

## What couldn't be assessed

- **Symlink behavior of `check_path_confinement()`** — `path.resolve()` follows symlinks by design in Python's pathlib. A symlink pointing outside the project directory will resolve to its target, making the check work correctly for symlinks. However, this means a symlink _inside_ the project directory that points _outside_ will be rejected (correct behavior), but the code cannot prevent a user from creating a symlink inside the project that points to a sensitive file — the check fires at the resolved path, which is correct. No issue, but worth noting.
- **Live Gemini API response shape** — The `getattr(result, 'model_version', None)` access was verified against the code and the google-genai SDK's documented response object, but not against a live API call. The finding below is based on the SDK documentation and code structure.

---

## Findings

> **Finding ID prefix:** `ENG-S2-`
> **Categories:** Architecture / Correctness / Security / Performance / Data provenance / Dependencies / Hygiene

---

### [ENG-S2-001] — Critical — Security — `_read_voice_samples` reads user-supplied paths without calling `check_path_confinement()`

**Evidence**

`agentsuite/agents/founder/stages/spec.py`, lines 41–51:

```python
def _read_voice_samples(inp: FounderAgentInput) -> str:
    if not inp.founder_voice_samples:
        return ""
    parts: list[str] = []
    for path in inp.founder_voice_samples:
        try:
            parts.append(Path(path).read_text(encoding="utf-8", errors="replace")[:5000])
        except OSError:
            continue
    return "\n---\n".join(parts)
```

`founder_voice_samples` is a `list[Path]` populated directly from user input (`FounderAgentInput.founder_voice_samples`). The function reads each path with `Path(path).read_text(...)` without calling `check_path_confinement()`. This is exactly the call site the Sprint 2 docstring on `kernel/stages/spec.py` (line 17–20) warns about:

> "Agent-level stages that read `manifest["sources"]` entries or `inp.founder_voice_samples` must call this before opening any path to prevent directory-traversal attacks."

The function can read any file on the filesystem reachable by the AgentSuite process — `/etc/passwd`, SSH keys, `.env` files, etc. — if an attacker can supply a path via the MCP or CLI input.

**Why this matters**

The `founder_run` MCP tool (`founder/mcp_tools.py:73–80`) accepts a `FounderRunRequest` which includes `founder_voice_samples: list[Path]`. An MCP client (e.g., Codex, Claude Code) can supply arbitrary paths. The contents of any readable file will be included in the LLM prompt sent to the configured provider — this is a data exfiltration path.

The CLI surface is narrower (user must have shell access) but the MCP surface is the primary integration mode for AgentSuite and is the higher-risk path.

**Blast radius**
- Adjacent code: The same gap exists in all agents that read user-supplied `list[Path]` fields during spec stage. Review `founder/stages/intake.py` (lines 41–52, reads `inputs_dir`, `explicit_brand_docs`, `founder_voice_samples`, `screenshots`), `design/stages/intake.py` (line 42–43), `trust_risk/stages/intake.py` (lines 39–46 — reads `existing_policies`, `incident_reports`), `cio/stages/intake.py` (line 21 — reads `existing_it_docs`). However, those are intake-stage reads that feed a manifest (path strings stored, not file content exfiltrated directly to LLM). `_read_voice_samples` at spec stage is the only current direct-read-to-LLM path; it is the most dangerous.
- Shared state: `founder_voice_samples` is part of `FounderAgentInput` which is serialized in `RunState`. A run_id replay also replays the paths.
- User-facing: no visible change after fix; legitimate uses are unaffected because voice samples should always be within the project directory.
- Migration: none required. The fix is additive.
- Tests to update: Add a test to `tests/unit/` that supplies a path outside the project directory and asserts that `ValueError` is raised.
- Related findings: ENG-S2-002 (also in founder/stages/spec.py).

**Fix path**

Add a `project_dir` parameter to `_read_voice_samples` (pass `ctx.writer.run_dir.parent.parent` or the configured project directory) and call `check_path_confinement(Path(path), project_dir)` before the `read_text` call. Import `check_path_confinement` from `agentsuite.kernel.stages.spec`.

Alternatively — and more defensibly — move the confinement check into the intake stage when paths are first accepted, so the invariant is enforced at the trust boundary rather than deep in spec. The manifest could record only paths that passed confinement.

---

### [ENG-S2-002] — Critical — Data provenance — Gemini cost uses request model, not API-reported model version

**Evidence**

`agentsuite/llm/gemini.py`, lines 54–60:

```python
return LLMResponse(
    text=text,
    model=getattr(result, 'model_version', None) or model,
    input_tokens=in_tokens,
    output_tokens=out_tokens,
    usd=_cost_usd(model, in_tokens, out_tokens),  # ← uses `model` (request param)
)
```

`LLMResponse.model` is set to `getattr(result, 'model_version', None) or model` — the actual model version reported by the API. But `_cost_usd` on the same line uses `model` — the model name from the request. These are different values: when Gemini routes `gemini-2.5-flash` to a sub-version like `gemini-2.5-flash-preview-04-17`, `model_version` will be `"gemini-2.5-flash-preview-04-17"` and `model` will be `"gemini-2.5-flash"`.

As a result:
1. `CostTracker` records `response.model` (the API version) in `cost_summary.json`
2. `CostTracker` records `response.usd` which was calculated using `model` (the request alias)

If the pricing table has an entry for `"gemini-2.5-flash"` but not `"gemini-2.5-flash-preview-04-17"`, costs are reported correctly. But if the pricing table is keyed by the API-returned version string, `_cost_usd(model, ...)` computes the wrong tier.

More concretely: `cost_summary.json` will show `"model": "gemini-2.5-flash-preview-04-17"` (the API version) but the USD cost was computed using `"gemini-2.5-flash"` pricing. These are inconsistent and operators reading the cost summary will not know which model tier was billed.

**Why this matters**

The cost summary is the operator's signal before approving a run. An operator who sees `"model": "gemini-2.5-flash-preview-04-17"` and knows that model costs more than the base alias will get a false sense of the actual charge. In the other direction, if a more expensive API model is charged at the cheaper alias rate, the cost cap math is silently wrong — the hard cap may allow spend that exceeds the intended limit.

**Blast radius**
- Adjacent code: `cost.py` `CostTracker.add()` and `summary()` use `Cost.model` as written — no other code computes cost independently. The mismatch is confined to `gemini.py`.
- Shared state: `cost_summary.json` written to every run dir. Already-written summaries will have inconsistent model/cost pairs until fixed.
- User-facing: operators see the cost summary before approving. The approval UX is affected.
- Migration: existing `cost_summary.json` files on disk are already inconsistent. A migration is not practical — they should be treated as estimates.
- Tests to update: The existing Gemini unit tests likely mock `result.model_version`. Confirm the test covers a case where `model_version != model` and that the cost calculation uses the correct key.
- Related findings: none — this is isolated to the Gemini provider.

**Fix path**

Use the same `model` value for both cost calculation and `LLMResponse.model`. The simplest fix:

```python
actual_model = getattr(result, 'model_version', None) or model
return LLMResponse(
    text=text,
    model=actual_model,
    input_tokens=in_tokens,
    output_tokens=out_tokens,
    usd=_cost_usd(actual_model, in_tokens, out_tokens),
)
```

This requires `_cost_usd` / the pricing table to handle API-version strings (which may include preview suffixes). Confirm `GEMINI_PRICING` covers these keys, or add a prefix-match fallback in `pricing.py`.

---

### [ENG-S2-003] — Major — Correctness — `cio/mcp_tools.py` reads `qa-scores.json` (hyphen) but kernel writes `qa_scores.json` (underscore)

**Evidence**

`agentsuite/agents/cio/mcp_tools.py`, line 198:
```python
qa_path = run_dir / "qa-scores.json"
```

`agentsuite/kernel/stages/qa.py`, line 121:
```python
ctx.writer.write_json("qa_scores.json", report.model_dump(), kind="data", stage="qa")
```

The kernel consistently uses underscores (`qa_scores.json`). The CIO MCP tool uses a hyphen (`qa-scores.json`). This file will never exist, so `agentsuite_cio_get_qa_scores` always returns the fallback response:

```python
return {"run_id": run_id, "scores": None, "note": "QA scores not yet available — run may still be in progress"}
```

Even for a completed run where QA has been scored, this tool always returns `scores: null`.

**Why this matters**

`agentsuite_cio_get_qa_scores` is a dedicated CIO MCP tool that MCP clients will call to retrieve QA scores before deciding whether to approve. It silently returns null scores for every completed run. An MCP client (Codex, Claude Code) that queries this tool before triggering approval will think QA hasn't run and may approve blindly — defeating the QA gate for the CIO agent.

**Blast radius**
- Adjacent code: `agentsuite_cio_list_artifacts` (line 180) and `agentsuite_cio_get_artifact` (line 167) reference SPEC_ARTIFACTS correctly. Only `get_qa_scores` is affected.
- User-facing: CIO runs always show `scores: null` via MCP. Any workflow that reads QA scores before approval is broken for this agent.
- Migration: none — just a filename fix.
- Tests to update: Add a test that runs the CIO QA stage and then calls the MCP `get_qa_scores` function, asserting scores are not null.
- Related findings: none — all other agents don't expose a `get_qa_scores` MCP tool.

**Fix path**

Change line 198 of `cio/mcp_tools.py`:
```python
qa_path = run_dir / "qa_scores.json"   # was qa-scores.json
```

---

### [ENG-S2-004] — Major — Security — `check_path_confinement()` is not enforced at the trust boundary; it is advisory-only

**Evidence**

`agentsuite/kernel/stages/spec.py`, lines 36–60 (the function definition), plus its docstring (lines 17–20):

> "Agent-level stages that read `manifest["sources"]` entries or `inp.founder_voice_samples` **must** call this before opening any path."

The word "must" is documentation. There is no structural enforcement. The function is available to callers but nothing prevents a future agent stage from reading a user-supplied path without calling it. Sprint 2 added this function specifically to protect against directory traversal, but then did not call it in `_read_voice_samples` (ENG-S2-001) — demonstrating that the advisory-only pattern does not hold even within Sprint 2 itself.

**Why this matters**

This is a systemic architectural concern, not just a one-off miss. The pattern of "here is a helper you must call" for security-critical checks is fragile. New agent stages, new input fields, and future contributors are all load-bearing assumptions. The check needs to either be structural (called automatically in a common read path) or enforced by a test that scans all call sites.

**Blast radius**
- Adjacent code: `founder/stages/extract.py:26–27` reads paths from `manifest["sources"]` without confinement (this is the `_summarize_sources` function — it reads path strings from the manifest JSON and calls `path.read_text()`). This is another live gap. The manifest is written by intake, which doesn't confine paths either.
- Shared state: every agent that accepts `list[Path]` inputs is a potential vector: founder (voice_samples, explicit_brand_docs, screenshots), trust_risk (existing_policies, incident_reports), cio (existing_it_docs).
- User-facing: no visible change after fix.
- Migration: none.
- Tests to update: Add a directory traversal test for each agent that accepts file paths as input.
- Related findings: ENG-S2-001 (specific instance of this pattern in founder/stages/spec.py).

**Fix path**

Two options, in order of preference:

1. **Enforce at intake, not at read.** In each agent's `intake_stage`, call `check_path_confinement` for every user-supplied path before writing it to the manifest. If any path fails confinement, raise `ValueError` before the run starts. The manifest then contains only pre-validated paths, and downstream readers are safe by construction.

2. **Add a CI test that scans for `read_text` and `open()` calls on user-supplied path fields** to confirm `check_path_confinement` was called upstream in the same function. This is harder to maintain but cheaper to implement today.

Option 1 is strongly recommended as the architectural fix.

---

### [ENG-S2-005] — Minor — Correctness — `UnknownAgent` catch in `cli.py:agents_cmd` uses `click.echo` instead of `typer.echo`

**Evidence**

`agentsuite/cli.py`, lines 278–285:

```python
@app.command("agents")
def agents_cmd() -> None:
    reg = default_registry()
    try:
        enabled = reg.enabled_names()
    except UnknownAgent:
        click.echo(
            "Unknown agent name. Valid agents: ...",
            err=True,
        )
        raise SystemExit(1)
```

The rest of `cli.py` exclusively uses `typer.echo`. This is the only `click.echo` call. The behavior is equivalent (`typer` wraps `click`) but it is inconsistent and indicates the `UnknownAgent` handler was written without noticing the module's own convention.

**Fix path**

Change `click.echo(...)` to `typer.echo(..., err=True)` and remove the `import click` if it becomes unused after the change.

---

### [ENG-S2-006] — Minor — Hygiene — `kernel_qa_stage` advances stage to `"approval"` unconditionally regardless of `requires_revision`

**Evidence**

`agentsuite/kernel/stages/qa.py`, lines 122–125:

```python
return state.model_copy(update={
    "stage": "approval",
    "requires_revision": report.requires_revision,
})
```

When `requires_revision` is `True`, the state still advances to `"approval"`. The approval gate itself blocks the run (`ApprovalGate` checks `requires_revision` and raises `RevisionRequired`). This means a run that fails QA reaches `"approval"` stage — which reads as "ready for approval" in the status output — when it actually requires revision first.

The `mcp_tools.py` files handle this correctly by checking `state.requires_revision` before setting `status = "awaiting_approval"` vs `status = "needs_revision"`. But the stage name itself is misleading.

This is not a correctness bug in the pipeline (the approval gate enforces it) but it creates a confusing status message for operators checking `state.stage` directly.

**Fix path**

Either: (a) keep the current design and document it clearly in `BaseAgent._drive` and `kernel_qa_stage` as "approval stage = awaiting gate check; see `requires_revision` flag for actionability"; or (b) add a `"needs_revision"` stage value and advance there when `requires_revision=True`. Option (a) is lower risk and consistent with the current `mcp_tools.py` approach.

---

### [ENG-S2-007] — Minor — Hygiene — `kernel/stages/qa.py` uses `ctx.edits["llm"]` without a KeyError guard

**Evidence**

`agentsuite/kernel/stages/qa.py`, line 77:

```python
llm = ctx.edits["llm"]
```

`kernel/stages/spec.py` does the same on line 110. Both assume `"llm"` was injected into `edits` by the agent's `_wrap` handler. The `_wrap` handlers do inject it (`ctx.edits.setdefault("llm", self.llm)`). But if the kernel functions are ever called outside the `_wrap` path (e.g., in a test, or a future agent that forgets to set up `edits`), the error will be `KeyError: 'llm'` — not a helpful diagnostic.

**Fix path**

Change to:
```python
llm = ctx.edits.get("llm")
if llm is None:
    raise ValueError("StageContext.edits['llm'] is not set — did the agent's _wrap handler inject the LLM?")
```

---

### [ENG-S2-008] — Nit — Hygiene — `QAStageConfig` module-level instances are mutated-if-shared risk

**Evidence**

All 14 agent stage files create module-level `_QA_CONFIG` and `_SPEC_CONFIG` instances (e.g., `founder/stages/qa.py:25–31`). These are `@dataclass` instances. Python `@dataclass` does not provide deep-freeze semantics — fields can be reassigned at runtime. If `kernel_qa_stage` or `kernel_spec_stage` ever mutates the config (e.g., adding a field to the dataclass with a mutable default), module-level state will bleed between test runs.

Currently the kernel functions treat configs as read-only, so this is not an active bug — it is a pattern to be aware of as the config dataclasses evolve.

**Fix path**

Add `frozen=True` to both `@dataclass` decorators in `kernel/stages/qa.py` and `kernel/stages/spec.py`. This makes mutation a `FrozenInstanceError` at dev time rather than a silent production bug.

---

### [ENG-S2-009] — Nit — Hygiene — `artifact_snippet_truncate=10_000_000` magic number in founder and design spec configs

**Evidence**

`founder/stages/spec.py:84` and `design/stages/spec.py:118`:
```python
artifact_snippet_truncate=10_000_000,  # effectively unlimited
```

The comment explains the intent but the magic number is fragile — if `SpecStageConfig` ever changes `artifact_snippet_truncate` to have hard-capped semantics, these silently change behavior. The dataclass default is `500`, which is not "unlimited." A sentinel value (`None`) or a named constant (`_UNLIMITED_TRUNCATION = None`) would express the intent clearly.

**Fix path**

Either: (a) add `artifact_snippet_truncate: int | None = 500` to `SpecStageConfig` with `None` meaning "no truncation", and update `kernel_spec_stage` to skip slicing when `None`; or (b) define a module-level constant `_NO_TRUNCATION: int = sys.maxsize` and use that. Option (a) is cleaner and consistent with the existing `artifact_truncate: int | None` field in `QAStageConfig`.

---

## Patterns and systemic observations

**The "helper you must call" security anti-pattern.** Sprint 2 introduced `check_path_confinement()` with a docstring mandate but no structural enforcement. Within the same sprint, the function was not called at the one spec-stage call site (`_read_voice_samples`) where it was most needed. This pattern — advisory security check — does not survive contributor turnover or feature additions. The fix is structural enforcement at intake, not documentation.

**Path-to-LLM exfiltration is a systemic surface.** Every agent that accepts `list[Path]` inputs (founder, trust_risk, cio) has a path from user input → file read → LLM prompt. The intake stage currently writes paths to a manifest without confinement checks. The extract stage (`founder/stages/extract.py:_summarize_sources`) reads those paths directly into the LLM prompt. The `_read_voice_samples` path in founder/stages/spec.py is a second direct-read path. Fixing ENG-S2-001 closes the spec-stage gap; ENG-S2-004 proposes closing it structurally at intake.

**CIO agent has distinct behavior patterns that diverge silently from the other six.** The CIO agent skips `qa_report.md` (correct per business requirements), uses bare-stem artifact keys (no `.md` extension in QA dict), and has 10 MCP tools vs 5 for others. The `qa-scores.json` filename bug (ENG-S2-003) is a downstream consequence of this divergence — the CIO's extra MCP tools were written without checking the kernel's actual output filename. This suggests the CIO agent's extra tools need a dedicated test pass every time the kernel changes its output filenames.

---

## Dependency snapshot

No new dependencies were added in Sprint 2. The `google-genai` SDK's `result.model_version` attribute (used in ENG-S2-002) is undocumented in some SDK versions — confirm availability against the pinned version in `pyproject.toml`.

| Dependency | Concern |
|---|---|
| `google-genai` (pinned version) | `result.model_version` attribute availability should be confirmed against the pinned version; `getattr(..., None)` fallback handles absence gracefully |

---

## Appendix: artifacts reviewed

- `agentsuite/kernel/stages/__init__.py`
- `agentsuite/kernel/stages/qa.py`
- `agentsuite/kernel/stages/spec.py`
- `agentsuite/kernel/base_agent.py`
- `agentsuite/kernel/cost.py`
- `agentsuite/llm/gemini.py`
- `agentsuite/cli.py`
- `agentsuite/mcp_server.py`
- `agentsuite/agents/founder/stages/qa.py`
- `agentsuite/agents/founder/stages/spec.py`
- `agentsuite/agents/founder/stages/extract.py`
- `agentsuite/agents/founder/stages/intake.py`
- `agentsuite/agents/founder/agent.py`
- `agentsuite/agents/founder/mcp_tools.py`
- `agentsuite/agents/founder/input_schema.py`
- `agentsuite/agents/design/stages/qa.py`
- `agentsuite/agents/design/stages/spec.py`
- `agentsuite/agents/design/agent.py`
- `agentsuite/agents/design/mcp_tools.py`
- `agentsuite/agents/engineering/stages/spec.py`
- `agentsuite/agents/engineering/agent.py`
- `agentsuite/agents/product/agent.py`
- `agentsuite/agents/marketing/agent.py`
- `agentsuite/agents/trust_risk/stages/spec.py`
- `agentsuite/agents/trust_risk/agent.py`
- `agentsuite/agents/cio/stages/spec.py`
- `agentsuite/agents/cio/stages/qa.py`
- `agentsuite/agents/cio/agent.py`
- `agentsuite/agents/cio/mcp_tools.py`
- Reference: `tests/unit/test_cli.py` (ENG-002 test coverage verification)
