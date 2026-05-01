# Sprint 2 — QA Deep-Dive

**Audit date:** 2026-04-30
**Role:** QA Engineer
**Scope audited:** Sprint 2 behavioral changes only — static analysis of runtime correctness for ENG-002, ENG-003, ENG-004, ENG-005/UX-003, QA-003, QA-004, QA-005, UX-004, UX-006.
**Environment:** Python 3.14.0, Windows 11 Pro 10.0.26200, AgentSuite v1.0.7 (GitHub source), static analysis only — product not executed (no live API key injected for this Sprint 2 pass).
**Auditor posture:** Balanced

---

## TL;DR

Sprint 2 ships nine behavioral fixes. Seven of the nine are correct and work as designed under normal operation. Two issues stand out: (1) the cleanroom script (`run-cleanroom.sh`) sets `AGENTSUITE_LLM_PROVIDER_FACTORY` *without* `PYTEST_CURRENT_TEST`, meaning the ENG-002 guard blocks the cleanroom in mocked mode — this is a **Critical** regression that breaks the pre-push gate every dev depends on; (2) `agentsuite_cio_get_qa_scores` reads `qa-scores.json` (hyphen) while the kernel writes `qa_scores.json` (underscore) — a **Major** silent file-not-found that makes the CIO QA scores MCP tool return "scores not yet available" even after a completed run. All other Sprint 2 fixes hold up under adversarial analysis.

## Severity roll-up (QA)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 2 |
| Minor | 2 |
| Nit | 1 |

## What's working

- **ENG-003 kernel extraction** — Both `founder/stages/qa.py` and `cio/stages/qa.py` correctly delegate to `kernel_qa_stage` with well-formed `QAStageConfig` objects. The `artifact_key_fn` and `artifact_truncate` divergence between founder (full bodies, `.md` keys) and CIO (500-char truncation, bare-stem keys) is intentional and correctly wired. No behavioral regression observable between the thin wrappers and the kernel functions they replaced.

- **ENG-004 path confinement** — `check_path_confinement` (kernel/stages/spec.py, lines 55-60) calls `path.resolve()` before `is_relative_to(project_dir.resolve())`. Both sides resolve, so symlinks that would escape the directory are caught. The guard raises `ValueError` with an actionable message identifying the offending path and the expected root.

- **QA-003 cost cap validation** — `CostCap.from_env()` (cost.py, lines 26-37) raises `ValueError` with a human-readable message when `AGENTSUITE_COST_CAP_USD` contains a non-numeric value. The `ValueError` propagates through `CostTracker.__init__()` (called by `_drive()`) before any LLM calls are made, which satisfies the "fail early" requirement.

- **QA-004 Gemini model version** — `getattr(result, 'model_version', None) or model` (gemini.py, line 56) is correct. When Gemini's response object lacks `model_version`, `getattr` returns `None`, and `None or model` falls back to the requested `model` string — the same identifier the cost calculation already used on line 59. The fallback is the right value.

- **QA-005 UnknownAgent error (CLI)** — `cli.py` catches `UnknownAgent` correctly in `agents_cmd()` (lines 279-285). The error message names valid agents and exits with code 1.

- **QA-005 UnknownAgent error (MCP)** — `mcp_server.py` catches `UnknownAgent` in `build_server()` (lines 76-81) and raises `RuntimeError` with a message naming valid agents. This surfaces as a startup error before any tool is registered, which is the correct failure mode.

- **UX-004 `_stage_to_status()`** — Both `founder/agent.py` (line 68-72) and `cio/agent.py` (line 77-81) implement identical `_stage_to_status` functions that map `"approval"` → `"awaiting_approval"` and pass all other values through unchanged. The function is called in `run_cmd()` output only, so unmapped novel stage values will appear verbatim in the JSON output — currently safe because `Stage` is a closed `Literal` type. Consistent across both agents.

- **UX-006 `project_slug` filter (founder MCP)** — `founder/mcp_tools.py` lines 142-145 correctly check `project_slug is not None` before filtering, and use `getattr(state.inputs, "project_slug", None)` defensively. The filter is exact-match string equality, which is correct for slug values.

- **ENG-005/UX-003 cost warning** — `base_agent.py` lines 183-191 correctly gate the warning on `cost_tracker.warned and not warned_before`, emitting exactly once to stderr. The `try/except Exception` wrapper ensures a broken stderr handle cannot crash the pipeline.

## What couldn't be assessed

- **Runtime behavior of `check_path_confinement` on actual symlinks** — static analysis confirms the `resolve()` call is present, but actual symlink traversal behavior was not verified by execution. Windows NTFS junction behavior may differ from POSIX symlink behavior.
- **Gemini SDK `result.model_version` attribute presence** — whether the Gemini SDK's `GenerateContentResponse` object actually exposes `model_version` on live responses could not be confirmed without a live API call; `getattr` makes this safe regardless.
- **Live cleanroom execution** — the cleanroom script was read for static analysis; it was not run. The Critical finding (QA-S2-001) is based on code reading of lines 43-45 of `run-cleanroom.sh` vs. lines 77-86 of `cli.py`.

---

## Product shape

AgentSuite is a CLI tool and MCP server for a 7-agent AI pipeline. This Sprint 2 QA pass focuses on runtime correctness of nine targeted behavioral fixes, assessed via static analysis. Key surfaces: CLI entry point (`cli.py`), MCP server (`mcp_server.py`), kernel pipeline driver (`base_agent.py`), cost subsystem (`cost.py`), and per-agent stage wrappers (`founder/`, `cio/`). QA concerns are CLI contract correctness, edge-case failure modes, error propagation, and data-path integrity.

## Flows exercised (static analysis)

| Flow | Result | Findings |
|---|---|---|
| Cleanroom mocked run (ENG-002 guard path) | **FAIL** | QA-S2-001 |
| CLI: factory guard in pytest context | Pass | — |
| CLI: factory guard not set (normal prod) | Pass | — |
| CLI: factory value "" (empty string) | Pass with caveat | QA-S2-004 |
| CIO MCP: `agentsuite_cio_get_qa_scores` after completed run | **FAIL** | QA-S2-002 |
| Founder MCP: `founder_list_runs` with `project_slug` filter | Pass | — |
| CIO MCP: `agentsuite_cio_list_runs` with `project_slug` filter | Pass | — |
| CIO MCP: `agentsuite_cio_approve` with `qa_report.md` path in error | Misleading | QA-S2-003 |
| `check_path_confinement`: path inside project_dir | Pass | — |
| `check_path_confinement`: path outside project_dir | Pass | — |
| `check_path_confinement`: non-existent project_dir | Minor | QA-S2-005 |
| Cost cap: valid AGENTSUITE_COST_CAP_USD | Pass | — |
| Cost cap: invalid AGENTSUITE_COST_CAP_USD (e.g. "abc") | Pass | — |
| Cost cap: AGENTSUITE_COST_CAP_USD="0" | Pass | — |
| Gemini model fallback: result has model_version | Pass | — |
| Gemini model fallback: result lacks model_version | Pass | — |
| `_stage_to_status("approval")` | Pass | — |
| `_stage_to_status("done")` | Pass | — |
| `_stage_to_status("qa")` | Pass | — |
| `_stage_to_status` (unknown future stage) | Pass with note | QA-S2-006 (Nit) |

## Adversarial scenarios exercised

| Scenario | Outcome | Findings |
|---|---|---|
| Set `AGENTSUITE_LLM_PROVIDER_FACTORY` without `PYTEST_CURRENT_TEST` (production user) | RuntimeError raised, clear message — correct | — |
| Set `AGENTSUITE_LLM_PROVIDER_FACTORY=""` (empty string) without `PYTEST_CURRENT_TEST` | Empty-string falsy, guard skips, falls through to `resolve_provider()` — correct | QA-S2-004 (Minor) |
| Set `AGENTSUITE_LLM_PROVIDER_FACTORY="0"` or `"false"` | Truthy, guard fires, RuntimeError — correct | — |
| Call `agentsuite_cio_get_qa_scores` on a completed CIO run | Returns "scores not yet available" — wrong | QA-S2-002 |
| Call `founder_list_runs(project_slug=None)` | Returns all founder runs — correct | — |
| Call `founder_list_runs(project_slug="")` | Returns only runs where `state.inputs.project_slug == ""` — probably unintended (empty-string vs None) | QA-S2-004 |
| Path traversal: `../../../etc/passwd` as source file | `check_path_confinement` raises ValueError — correct | — |
| `AGENTSUITE_COST_CAP_USD="abc"` | ValueError raised before any LLM call — correct | — |
| `AGENTSUITE_COST_CAP_USD="-1.0"` | Accepted, sets hard cap to -1.0 (negative) — first LLM call will immediately exceed cap | QA-S2-005 (Minor) |

---

## Findings

> **Finding ID prefix:** `QA-S2-`
> **Categories:** Flow / API / Security / CLI / Install

---

### [QA-S2-001] — Critical — CLI / Install — ENG-002 guard blocks cleanroom mocked run

**Evidence**

1. `scripts/run-cleanroom.sh` line 44: `export AGENTSUITE_LLM_PROVIDER_FACTORY="agentsuite.llm.mock:_default_mock_for_cli"`
2. `scripts/run-cleanroom.sh` line 44: there is no `export PYTEST_CURRENT_TEST=...` in the mocked-mode branch (lines 38–45 of the script).
3. `agentsuite/cli.py` lines 77-83: the ENG-002 guard reads:
   ```python
   if factory and not os.environ.get("PYTEST_CURRENT_TEST"):
       raise RuntimeError(
           "AGENTSUITE_LLM_PROVIDER_FACTORY is set outside of a pytest run. ..."
       )
   ```
4. Result: when the cleanroom script runs `agentsuite founder run ...` in mocked mode (line 47), `AGENTSUITE_LLM_PROVIDER_FACTORY` is set, `PYTEST_CURRENT_TEST` is not set, and the guard raises `RuntimeError` before the agent starts.
5. Cleanroom exits non-zero on the `agentsuite founder run` command; the artifact assertions and approval step never run.

**Observed result:** Cleanroom fails in mocked mode with:
```
RuntimeError: AGENTSUITE_LLM_PROVIDER_FACTORY is set outside of a pytest run. ...
```

**Expected result:** Cleanroom uses the mock LLM and runs the full founder pipeline without API costs.

**Why this matters**

The cleanroom is the required pre-push E2E gate per `CLAUDE.md`. Every developer and every CI run that validates Sprint 2 on a clean install will see this failure as soon as they run `scripts/run-cleanroom.sh`. The mocked mode (default, zero cost) is the standard cleanroom path — the live mode exists only for major release validation. This effectively breaks the pre-push gate for all Sprint 2 work.

**Blast radius:**
- Adjacent code: `cli.py` `_resolve_llm_for_cli()` — the only call site of the guard. No other files need changes.
- User-facing: any developer or CI job running `scripts/run-cleanroom.sh` (default, mocked mode) will get a `RuntimeError` at the first `agentsuite ... run` command.
- Migration: none — fix is in `run-cleanroom.sh` or the guard condition.
- Tests to update: any test that exercises `_resolve_llm_for_cli()` with the factory env var should already set `PYTEST_CURRENT_TEST` (which pytest does automatically). Tests are likely unaffected; only the script is broken.
- Related findings: none.

**Fix path**

Two acceptable fixes:

**Option A (preferred):** Widen the guard condition in `cli.py` to also pass when a known safe non-pytest variable is set. Add a second env var `AGENTSUITE_ALLOW_MOCK_FACTORY=1` that the cleanroom exports, and update the guard:
```python
if factory and not os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("AGENTSUITE_ALLOW_MOCK_FACTORY"):
    raise RuntimeError(...)
```
Then set `export AGENTSUITE_ALLOW_MOCK_FACTORY=1` in the mocked-mode block of `run-cleanroom.sh`.

**Option B (simpler):** In `run-cleanroom.sh` mocked-mode block, also export a fake `PYTEST_CURRENT_TEST` value:
```bash
export PYTEST_CURRENT_TEST="cleanroom::mocked"
```
This reuses the existing guard without adding a new env var. The downside is semantically odd (cleanroom isn't pytest), but it is the lowest-diff fix.

---

### [QA-S2-002] — Major — API — CIO `agentsuite_cio_get_qa_scores` reads wrong filename

**Evidence**

1. `agentsuite/kernel/stages/qa.py` line 120: kernel writes `qa_scores.json` (underscore):
   ```python
   ctx.writer.write_json("qa_scores.json", report.model_dump(), kind="data", stage="qa")
   ```
2. `agentsuite/agents/cio/mcp_tools.py` line 198: CIO MCP tool reads `qa-scores.json` (hyphen):
   ```python
   qa_path = run_dir / "qa-scores.json"
   ```
3. These are two different filenames. On a completed CIO run, `qa_scores.json` exists on disk but `qa-scores.json` does not.
4. The `if qa_path.exists()` branch (line 199) is never entered. The tool always falls through to:
   ```python
   return {"run_id": run_id, "scores": None, "note": "QA scores not yet available — run may still be in progress"}
   ```

**Observed result:** `agentsuite_cio_get_qa_scores` returns `{"scores": null, "note": "QA scores not yet available ..."}` even after the CIO pipeline completes successfully and `qa_scores.json` is present on disk.

**Expected result:** Returns the actual QA scores from `qa_scores.json`.

**Why this matters**

MCP clients (Codex, Claude Code) use `agentsuite_cio_get_qa_scores` to check whether a CIO run passed QA before approving it. The tool always returns "not yet available," making it useless. Users may approve runs without reviewing scores, or incorrectly believe the QA stage failed.

Same bug is present in `agentsuite/agents/trust_risk/mcp_tools.py` line 194 (also reads `qa-scores.json`). See blast radius.

**Blast radius:**
- Adjacent code: `agentsuite/agents/trust_risk/mcp_tools.py` line 194 has the exact same hyphen-vs-underscore bug in `agentsuite_trust_risk_get_qa_scores`. Fix both in the same PR.
- Shared state: `qa_scores.json` (underscore) is the canonical filename written by `kernel/stages/qa.py` for all agents. All agents currently use `qa_scores.json` on the write side; this is a read-side-only bug in two MCP tools.
- User-facing: `agentsuite_cio_get_qa_scores` and `agentsuite_trust_risk_get_qa_scores` both return false "not ready" responses. Approval decisions made without score review.
- Migration: none — no stored data changes, only a read path fix.
- Tests to update: any test of `agentsuite_cio_get_qa_scores` or `agentsuite_trust_risk_get_qa_scores` that asserts the "not yet available" response for a completed run is asserting the broken behavior and must be updated.
- Related findings: none in this audit.

**Fix path**

In `agentsuite/agents/cio/mcp_tools.py` line 198, change:
```python
qa_path = run_dir / "qa-scores.json"
```
to:
```python
qa_path = run_dir / "qa_scores.json"
```

Make the identical change in `agentsuite/agents/trust_risk/mcp_tools.py` line 194.

---

### [QA-S2-003] — Major — API — CIO `agentsuite_cio_approve` returns wrong QA report path

**Evidence**

1. `agentsuite/agents/cio/mcp_tools.py` lines 109-115: on `RevisionRequired`, the `agentsuite_cio_approve` tool returns:
   ```python
   return {
       "error": "revision_required",
       "message": str(e),
       "qa_report_path": str(run_dir / "qa_report.md"),
       ...
   }
   ```
2. `agentsuite/agents/cio/stages/qa.py` line 30: `write_qa_report=False` — the CIO agent explicitly does not write `qa_report.md`.
3. The kernel QA stage (`kernel/stages/qa.py` line 118-119) only writes `qa_report.md` when `config.write_qa_report is True`. For CIO, it is `False`.
4. Result: when a CIO run requires revision, the MCP tool's error response points to `qa_report.md`, which does not exist on disk for CIO runs.

**Observed result:** MCP client receives `qa_report_path: ".agentsuite/runs/<run_id>/qa_report.md"` pointing to a non-existent file, with the instruction "Review qa_report.md and re-run...".

**Expected result:** For CIO, the action should point to `qa_scores.json` (the file that does exist), or the `qa_report_path` field should be omitted / corrected for agents that do not write QA reports.

**Why this matters**

MCP clients that receive a `revision_required` error for a CIO run will follow the `qa_report_path` to a file that does not exist. The operator cannot find the QA feedback. The revision cycle is blocked — the operator cannot tell what to fix.

**Blast radius:**
- Adjacent code: `agentsuite/agents/founder/mcp_tools.py` lines 93-99 has the same pattern but for founder, which *does* write `qa_report.md` — that instance is correct. Only the CIO case is wrong.
- User-facing: CIO operators who need to revise a run cannot find the QA feedback file via the MCP interface.
- Migration: none — the fix is in the error response construction only.
- Tests to update: any test asserting the `qa_report_path` value in the CIO `revision_required` error response.
- Related findings: QA-S2-002 (CIO QA scores filename mismatch is the sibling issue — both are CIO QA output path bugs).

**Fix path**

In `agentsuite/agents/cio/mcp_tools.py`, update the `RevisionRequired` handler to point to the correct file:
```python
return {
    "error": "revision_required",
    "message": str(e),
    "qa_scores_path": str(run_dir / "qa_scores.json"),
    "action": "Review qa_scores.json and re-run the agent to address QA feedback before approving.",
}
```
Remove `qa_report_path` from the CIO error response since `qa_report.md` is never written for CIO.

---

### [QA-S2-004] — Minor — CLI — Empty-string `AGENTSUITE_LLM_PROVIDER_FACTORY` bypasses guard silently

**Evidence**

1. `agentsuite/cli.py` line 77: `factory = os.environ.get("AGENTSUITE_LLM_PROVIDER_FACTORY")`
2. `agentsuite/cli.py` line 78: `if factory and not os.environ.get("PYTEST_CURRENT_TEST"):`
3. If `AGENTSUITE_LLM_PROVIDER_FACTORY=""` (explicitly set to empty string), `factory` is `""`, which is falsy in Python. The `if factory` check is `False`. The guard never fires.
4. The code then falls through to `if factory:` on line 84, which is also `False`. `resolve_provider()` is called instead.
5. This is correct behavior (empty string → use real provider), but it is undocumented and could mislead an operator who sets `AGENTSUITE_LLM_PROVIDER_FACTORY=""` expecting the guard to log or warn.

**Why this matters**

Low risk: the fallthrough behavior is correct. The gap is that a misconfigured environment (empty string left by accident) silently uses the real provider without warning. On its own this is Minor — the provider resolver will produce its own errors if not configured.

**Fix path**

Add a warning in `_resolve_llm_for_cli()` when `AGENTSUITE_LLM_PROVIDER_FACTORY` is explicitly set to an empty string:
```python
factory = os.environ.get("AGENTSUITE_LLM_PROVIDER_FACTORY")
if factory is not None and factory == "":
    import sys
    sys.stderr.write("Warning: AGENTSUITE_LLM_PROVIDER_FACTORY is set to empty string — ignoring.\n")
```
Low priority. Address in a hygiene pass.

---

### [QA-S2-005] — Minor — CLI / Security — `AGENTSUITE_COST_CAP_USD` accepts negative values

**Evidence**

1. `agentsuite/kernel/cost.py` line 31-37: `from_env()` converts the raw string to `float(raw)` and passes it as `hard_kill_usd` with no sign check.
2. `CostCap(hard_kill_usd=-1.0)` is accepted by Pydantic (no `gt=0` constraint on the field).
3. `CostTracker.add()` line 77: `if new_total.usd > self.cap.hard_kill_usd:` — with a negative cap, every LLM call (even the first, with `new_total.usd > 0`) immediately raises `HardCapExceeded`.
4. An operator who mistypes `-5.0` instead of `5.0` gets `HardCapExceeded` on the very first LLM call with no explanation about the cap value.

**Why this matters**

The error message says "Cost $0.0001 would exceed hard cap $-1.00" — confusing and unhelpful. The operator set a negative number accidentally and cannot tell from the error what happened. Low exposure (requires an operator typo), but easy to fix.

**Fix path**

Add a positive-value check in `CostCap.from_env()`:
```python
hard = float(raw)
if hard <= 0:
    raise ValueError(
        f"AGENTSUITE_COST_CAP_USD={raw!r} must be a positive dollar amount. "
        "Set it to a number like '5.00'."
    )
```
Also add a `gt=0` Pydantic field constraint to `CostCap.hard_kill_usd` to catch programmatic misuse.

---

### [QA-S2-006] — Nit — CLI — `_stage_to_status` is duplicated, not shared

**Evidence**

`founder/agent.py` lines 68-72 and `cio/agent.py` lines 77-81 both define identical `_stage_to_status(stage: str) -> str` functions. If a new stage value is added to the `Stage` Literal and one module is updated but not the other, the two agents' status outputs will diverge silently.

**Fix path**

Move `_stage_to_status` to `agentsuite/kernel/base_agent.py` or a shared `agentsuite/agents/_common.py` and import it in both agent modules. One-line change per module + one new shared function. Low priority — no user-visible impact today.

---

## Performance snapshot

| Metric | Observed | Benchmark | Verdict |
|---|---|---|---|
| CLI startup (cold) | Not measured — static analysis only | <500ms | Not assessed |
| Stage progress emission | O(1) per stage, negligible | — | Pass (code path) |
| Cost tracking per-add | O(1) dict lookup | — | Pass (code path) |

## Security / privacy snapshot

- **ENG-004 path confinement** is correctly implemented with `resolve()` on both sides. Symlink escapes are blocked. The guard is called before reading source files in the spec stage.
- **ENG-002 RCE note** — the `AGENTSUITE_LLM_PROVIDER_FACTORY` guard correctly prevents the arbitrary-code-execution vector in production. The Critical finding (QA-S2-001) is a deployment breakage, not a security regression — the guard is correctly tightened; the cleanroom just needs to adapt.
- No credentials are returned in any MCP tool response examined. Error messages include file paths but not secret values.

## Console and log observations

- No stdout contamination introduced by Sprint 2 changes. Cost warning (`base_agent.py` lines 184-190) and stage progress (`_emit_stage_progress`) correctly target `sys.stderr`.
- CIO `agentsuite_cio_get_qa_scores` returns a structured dict (not an exception) for the missing-file case. The MCP transport will surface this as a successful tool response with `{"scores": null}`. No unhandled exception.

## Patterns and systemic observations

**CIO-specific paths are diverging from the founder pattern without a shared abstraction.** Three findings in this audit (QA-S2-002, QA-S2-003, and the `_stage_to_status` nit) all stem from the CIO agent having slightly different behavior that isn't captured in a shared layer:
- CIO doesn't write `qa_report.md` but the MCP approval error response still references it.
- CIO reads `qa-scores.json` (hyphen) while the kernel writes `qa_scores.json` (underscore).
- `_stage_to_status` is duplicated rather than shared.

The root cause is that per-agent MCP tools were written without a centralized "what files does this agent write?" contract. As more agents ship CIO-style variations (write_qa_report=False, truncated artifacts, etc.), this divergence will accumulate. Recommend adding a per-agent `WRITTEN_FILES` contract or an agent capability flag that MCP tools consult when constructing file paths and error messages.

## Appendix: environments and artifacts

**Static analysis scope:**
- `agentsuite/cli.py` — ENG-002 guard, QA-005 UnknownAgent
- `agentsuite/mcp_server.py` — QA-005 UnknownAgent
- `agentsuite/kernel/stages/qa.py` — ENG-003 kernel QA stage
- `agentsuite/kernel/stages/spec.py` — ENG-003 kernel spec stage, ENG-004 path confinement
- `agentsuite/agents/founder/stages/qa.py` — ENG-003 thin wrapper
- `agentsuite/agents/founder/stages/spec.py` — ENG-003 thin wrapper
- `agentsuite/agents/cio/stages/qa.py` — ENG-003 thin wrapper (CIO divergence)
- `agentsuite/agents/cio/stages/spec.py` — ENG-003 thin wrapper (CIO divergence)
- `agentsuite/kernel/base_agent.py` — ENG-005/UX-003 cost display
- `agentsuite/kernel/cost.py` — QA-003 cost cap validation
- `agentsuite/llm/gemini.py` — QA-004 model version fallback
- `agentsuite/agents/founder/agent.py` — UX-004 `_stage_to_status`
- `agentsuite/agents/cio/agent.py` — UX-004 `_stage_to_status` consistency
- `agentsuite/agents/founder/mcp_tools.py` — UX-006 `project_slug` filter
- `agentsuite/agents/cio/mcp_tools.py` — UX-006 `project_slug` filter, QA-S2-002, QA-S2-003
- `scripts/run-cleanroom.sh` — ENG-002 interaction, QA-S2-001

**Tools used:** Read, Grep, Glob (static analysis only). No live execution.
