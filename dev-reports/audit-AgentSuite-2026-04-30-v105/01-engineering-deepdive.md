# Engineering Deep-Dive — AgentSuite v1.0.5

**Audit date:** 2026-04-30
**Role:** Principal Engineer
**Scope audited:** Full — `agentsuite/kernel/`, `agentsuite/llm/`, `agentsuite/agents/founder/` (specimen), `agentsuite/agents/cio/`, `agentsuite/agents/trust_risk/`, `agentsuite/mcp_server.py`, `agentsuite/cli.py`, `agentsuite/__init__.py`, `pyproject.toml`, all 7 agents' stage handlers (survey), stress test suite
**Auditor posture:** Balanced

---

## TL;DR

AgentSuite v1.0.5 is a well-structured Python library with a coherent kernel-pipeline design, solid path-traversal defenses at the `run_id`/`project_slug` boundary, and an impressive recent surge of defensive hardening (JSON fence stripping, QA rubric graceful degradation, cost provenance). The architectural bones are sound and the 908-test suite reflects genuine discipline. Two security findings need attention before the next PyPI release: an unvalidated `artifact_name` path parameter in two agents' MCP tools that allows reading arbitrary files from the local filesystem, and an `AGENTSUITE_LLM_PROVIDER_FACTORY` env var that executes arbitrary Python from any module path — both are within expected developer-tool scope, but the first is a genuine local-file read vulnerability. The dominant systemic issue is unavoidable per-agent code duplication across 7 agents × 5 stages — tolerable today, but a maintenance tax that compounds with each new agent and each cross-cutting fix.

---

## Severity roll-up (engineering)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 4 |
| Minor | 5 |
| Nit | 3 |
| **Total** | **13** |

---

## What's working

- **Path-traversal defense at the kernel boundary** — `ArtifactWriter.__init__` calls `validate_run_id`, then double-checks `run_dir.is_relative_to(output_root)`. The `identifiers.py` module with its `_ID_RE` regex is the right move: a single, tested, documented validator rather than per-callsite ad-hoc sanitization. The comment chain from `ENG-001` in `identifiers.py` and `artifacts.py` shows the team understands why this matters.

- **Atomic state writes** — `StateStore.save` uses `tempfile.mkstemp` + `os.fsync` + `os.replace` so a crash mid-write never corrupts `_state.json`. This is the right pattern; many projects skip it and then wonder why resume fails.

- **Cost provenance fix (CR-102 / ENG-002)** — `pricing.py` now has `lookup_pricing()` returning `(rates, provenance)` with a structured warning on fallback. Previously every production billed call silently used a hardcoded rate. The comment block in `pricing.py` calling out the pre-v1.0.1 bug is honest and useful.

- **QA rubric graceful degradation** — `QARubric.score()` coerces string/null/missing scores to `float` and assigns `0.0` to missing dimensions with a revision instruction. The stress suite in `tests/stress/test_qa_rubric_variants.py` has 30+ parametrized cases covering all the LLM output shapes that caused production crashes. Exactly the right test investment for a defensive code path.

- **JSON fence stripping** — `extract_json` handles all realistic LLM output shapes (fenced, preamble prose, trailing prose, whitespace variants). The accompanying `tests/stress/test_json_extraction_variants.py` with 26 accept-cases and 14 reject-cases gives high confidence in the implementation.

- **MockLLMProvider.complete longest-match semantics** — The switch from insertion-order to `sorted(items, key=lambda kv: -len(kv[0]))` prevents silent mock prompt-drift. `NoMockResponseConfigured` raising on no-match keeps tests honest.

- **`RetryingLLMProvider` design** — Wraps any `LLMProvider` via composition, not inheritance. `retry_if_not_exception_type(_NO_RETRY_EXCEPTIONS)` correctly exempts `ProviderNotInstalled`, `KeyboardInterrupt`, `SystemExit`. The `tenacity` `before_sleep_log` hook means operators see retry events in logs without any extra wiring.

- **`SequentialMockLLMProvider`** — A proper tool for testing pipelines where the same pattern fires N times but you want the Nth call to behave differently. Rare to see this in a test infrastructure at this stage; it suggests genuine test discipline.

- **Dependency surface** — Five direct dependencies (`pydantic`, `tenacity`, `typer`, `httpx`, `jinja2`), all with bounded version ranges. Provider SDKs are optional extras. No transitive bloat. `httpx` is currently unused in production code (likely a residual from a prior plan) but the inclusion is benign.

---

## What couldn't be assessed

- **`pip-audit` / CVE scan** — Not run in this pass. The dependency surface is minimal and all major dependencies are current-generation, so the risk is low, but the team should run `pip-audit` before every PyPI release.
- **Live provider integration** — All provider adapters reviewed by code inspection only. The Anthropic adapter's `temperature=0.0` usage in production stage calls was not verified against Anthropic's current API constraints (some model families may reject `temperature` entirely on structured-output endpoints).
- **Jinja2 template contents** — Prompt templates (`.jinja2`) were not read. Injection risk exists if user-controlled strings are interpolated without escaping; could not assess without reading every template.
- **`agentsuite/agents/cio/mcp_tools.py` lines 159–204 beyond `get_brief_template`** — Rest of file reviewed; no additional path issues found, but detailed review of the `list_brief_templates` and `get_revision_instructions` tools was light.

---

## Findings

> **Finding ID prefix:** `ENG-`
> **Categories:** Architecture / Correctness / Security / Performance / Data provenance / Dependencies / Hygiene

---

### [ENG-001] — Critical — Security — Unvalidated `artifact_name` and `template_name` parameters enable local-file read via MCP

**Evidence**

File: `agentsuite/agents/cio/mcp_tools.py`, lines 153–157
```python
artifact_path = run_dir / f"{artifact_name}.md"
if not artifact_path.exists():
    return {"error": ...}
return {..., "content": artifact_path.read_text(encoding="utf-8"), ...}
```

File: `agentsuite/agents/cio/mcp_tools.py`, lines 196–199 (same pattern for `template_name`)
File: `agentsuite/agents/trust_risk/mcp_tools.py`, lines 150–153 and 192–195

`run_id` is correctly validated by `require_run_dir` → `validate_run_id` before path construction. `artifact_name` and `template_name` are **not** validated. An MCP client can pass `artifact_name = "../../.env"` to construct `output_root/runs/myrun/../../.env.md`. On Windows, `../../.env.md` resolves to a real path outside `run_dir`, and `.exists()` may return `True` if that path happens to exist; `read_text()` then returns its contents to the caller.

Verified by constructing the path programmatically:
```python
>>> Path('C:/test/runs/myrun') / '../../etc/passwd'
WindowsPath('C:/test/runs/myrun/../../etc/passwd')
```
The `.md` suffix does not prevent traversal — it makes the traversal slightly less flexible, but any target file with or without a `.md` extension that happens to exist is still reachable because the path string `../../some-file` is valid before `.md` is appended, and the full resolved path still escapes `run_dir`.

This is an MCP server endpoint, so the attack surface is any MCP client that can call these tools — including any LLM that has been told to call `agentsuite_cio_get_artifact` with a user-controlled argument.

**Why this matters**

An agent or user with MCP access can read arbitrary `.md`-suffixed files (or any file whose name happens to end in `.md`) from the host filesystem outside the `.agentsuite/` output root. In a developer workstation context this could expose `README.md` files, documentation, or markdown-formatted config files placed outside the output root. In a shared CI/server context the blast radius is wider. The `path` field in the returned dict also discloses the resolved path of any file, confirming the traversal to a caller who probes systematically.

**Blast radius**
- Adjacent code: `agentsuite/agents/cio/mcp_tools.py` (both `get_artifact` and `get_brief_template`), `agentsuite/agents/trust_risk/mcp_tools.py` (both `get_artifact` and `get_brief_template`). Other agents (founder, design, product, engineering, marketing) do not expose `get_artifact` MCP tools in their current implementations — no fix needed there.
- Shared state: `require_run_dir` in `agentsuite/agents/_common.py` already validates `run_id` and is the right pattern to extend. Adding `validate_artifact_name` to `identifiers.py` and calling it at the head of each function is a one-line fix per callsite.
- User-facing: No visible change to legitimate MCP consumers — all legal artifact names already match the identifier shape.
- Migration: None. Additive enforcement only.
- Tests to update: Add tests for traversal-attempt rejection in `tests/unit/agents/cio/test_mcp_tools.py` and the trust_risk equivalent.
- Related findings: None; this is isolated to the two named MCP tool files.

**Fix path**

Add `validate_identifier(artifact_name, kind="artifact_name")` (reusing `agentsuite/kernel/identifiers.py`) at the top of `agentsuite_cio_get_artifact` and `agentsuite_cio_get_brief_template`, and the trust_risk equivalents. Alternatively, add an allowlist check: `if artifact_name not in SPEC_ARTIFACTS: raise ValueError(...)` — this is actually stricter and already documented in the tool's docstring as the intended constraint. The allowlist check is the right first fix; the `validate_identifier` call is a belt-and-suspenders addition.

---

### [ENG-002] — Major — Security — `AGENTSUITE_LLM_PROVIDER_FACTORY` executes arbitrary Python from any importable module

**Evidence**

File: `agentsuite/cli.py`, lines 71–74:
```python
factory = os.environ.get("AGENTSUITE_LLM_PROVIDER_FACTORY")
if factory:
    module_name, fn_name = factory.split(":", 1)
    return getattr(importlib.import_module(module_name), fn_name)()
```

Any string of the form `module_name:fn_name` set in the environment will be imported and called. There is no validation of `module_name` or `fn_name`. A value like `os:system` with a separate env var or a wrapping lambda would execute arbitrary code. The previous audit (`dev-reports/audit-AgentSuite-2026-04-29/05-qa-deepdive.md`, line 394) flagged this and recommended a docstring warning; none has been added.

**Why this matters**

This feature is intentionally a test-only escape hatch — it is used extensively in the test suite via `monkeypatch.setenv`. But it is enabled unconditionally in the published CLI binary with no documentation, no allowlist, and no warning. A developer who misconfigures this env var (typo, leftover from a test run, or CI env pollution) silently executes arbitrary Python. In a shared CI environment where multiple pipelines share environment variables, this is a real misconfiguration risk.

**Blast radius**
- Adjacent code: Only `agentsuite/cli.py` reads this env var; the MCP server does not. No other callsite.
- User-facing: Legitimate test users are unaffected if the path is unchanged. Adding a docstring or warning does not change behavior.
- Migration: None.
- Tests to update: No new tests needed; this is a documentation/warning gap.
- Related findings: None.

**Fix path**

Add a docstring to `_resolve_llm_for_cli` stating this is for testing only and should never be set in production. Consider adding a runtime warning when `AGENTSUITE_LLM_PROVIDER_FACTORY` is set outside a `pytest` context (detectable via `sys.modules.get('pytest') is not None`). An allowlist of known-safe module paths (e.g., only paths under `agentsuite.*`) would be the strongest mitigation, but may be over-engineered for a developer tool. At minimum, document the risk in `CONTRIBUTING.md`.

---

### [ENG-003] — Major — Architecture — Per-agent duplication of 5-stage qa patterns is a maintenance tax

**Evidence**

All 7 agents implement essentially identical `qa_stage` functions. Inspecting `agentsuite/agents/founder/stages/qa.py`, `agentsuite/agents/cio/stages/qa.py`, `agentsuite/agents/design/stages/qa.py` shows the same 40-line pattern with only the rubric name and artifact list differing:

```
# repeated 7 times, one per agent:
parsed = extract_json(response.text)
if not isinstance(parsed, dict): parsed = {}
raw_scores = parsed.get("scores")
if not isinstance(raw_scores, dict): raw_scores = {}
raw_revisions = parsed.get("revision_instructions")
if not isinstance(raw_revisions, list): raw_revisions = {}
report = AGENT_RUBRIC.score(scores=raw_scores, revision_instructions=raw_revisions)
ctx.writer.write_json("qa_scores.json", ...)
return state.model_copy(update={"stage": "approval", "requires_revision": report.requires_revision})
```

Similarly, `extract_stage` and `spec_stage` share a nearly identical outer shell across all 7 agents. The recent CR-101/CR-102/CR-104 fixes had to be applied identically 7 times. The stress test `test_qa_rubric_variants.py` explicitly documents: "Uses the Founder agent as a representative specimen; the defensive code path in qa_stage is identical across all 7 agents" — which is a test-coverage gap as much as an architectural one: the stress tests exercise the Founder specimen, but if a future fix is missed in one of the other 6 agents, no stress test catches it.

**Why this matters**

This is the highest-leverage architectural finding in the audit. Every cross-cutting fix (CR-101, CR-102, CR-104) is applied 7 times manually. Every missed application of a fix to one agent produces a silent regression. The `test_qa_rubric_variants.py` comment acknowledging this risk confirms the team is aware of it. As AgentSuite adds a 8th or 9th agent, the cost compounds.

**Blast radius**
- Adjacent code: All 7 agents' `stages/qa.py`, `stages/extract.py`, `stages/spec.py`. The kernel already provides `BaseAgent`, `QARubric`, and `QAReport`; the shared logic belongs there.
- Shared state: `QARubric.score()` is already centralized; the remaining duplication is the callsite boilerplate.
- User-facing: Refactoring is a purely internal change if done without changing behavior. Public API (`BaseAgent`, `QARubric`, stage interfaces) would not change.
- Migration: None if refactored correctly. Additive helper in kernel; agents call the helper.
- Tests to update: Stress tests should be expanded to cover all 7 agents' QA stages, not just Founder, even post-refactor.
- Related findings: ENG-004 (source-file read from unrooted paths) is the same copy-paste root cause.

**Fix path**

Extract a `kernel_qa_stage` helper in `agentsuite/kernel/qa.py` or `agentsuite/kernel/base_agent.py` that takes a rubric, a list of artifact stems, a prompt-render callable, and a `StageContext`, and runs the full extract-parse-guard-score-write loop. Each agent's `qa_stage` becomes a 5-line wrapper that calls this helper with its own rubric and artifact list. This eliminates 7 × ~35 lines of duplicate code and ensures all agents get fixes atomically.

---

### [ENG-004] — Major — Security — User-supplied file paths from `inputs_dir` and `founder_voice_samples` are read without output-root bounds check

**Evidence**

File: `agentsuite/agents/founder/stages/extract.py`, lines 24–28:
```python
for s in manifest["sources"]:
    path = Path(s["path"])
    ...
    if path.exists() and path.is_file():
        snippet = path.read_text(encoding="utf-8", errors="replace")[:1500]
```

File: `agentsuite/agents/founder/stages/spec.py`, lines 45–49:
```python
for path in inp.founder_voice_samples:
    try:
        parts.append(Path(path).read_text(encoding="utf-8", errors="replace")[:5000])
```

Both callsites read from absolute filesystem paths that originate from user-supplied `FounderAgentInput.inputs_dir`, `explicit_brand_docs`, `founder_voice_samples`, `screenshots`, etc. These paths are populated from the CLI (`--inputs-dir`) or MCP (`FounderRunRequest`). There is no check that the resolved path is within any trusted root. A caller can supply `/etc/shadow` (POSIX) or `C:\Windows\System32\drivers\etc\hosts` (Windows) as a source material path and its contents will be included verbatim in the LLM prompt.

The same pattern exists in all 7 agents' `extract_stage` and `spec_stage` implementations (confirmed via code survey).

**Why this matters**

This differs from ENG-001 (which reads artifacts back out to the caller). Here the vulnerability is that local file contents are silently included in the LLM prompt and then reflected in generated artifacts. On a developer workstation the immediate risk is credential leak into LLM prompts (API keys in `~/.env`, SSH keys if pasted as a voice sample). In an automated/CI context where agents run unattended, this could be exploited to exfiltrate secrets through the LLM output artifacts.

The `:1500` and `:5000` truncation limits the blast radius per file, but does not prevent the attack.

**Blast radius**
- Adjacent code: All 7 agents' `stages/extract.py` and `stages/spec.py` where source materials are read. The intake stage merely lists paths; the extract stage actually reads them.
- Shared state: `FounderAgentInput` and the other 6 agents' input schemas all accept `inputs_dir`, `explicit_*`, and `*_voice_samples` fields.
- User-facing: A CLI operator providing `--inputs-dir` is the primary user. The fix — requiring paths to be under a configurable trusted root, defaulting to the user's home directory or the explicitly passed directory — would require a CONTRIBUTING.md note but no breaking API change.
- Migration: None. Could be implemented as a soft warning initially.
- Tests to update: Add a test asserting that paths outside a trusted root are rejected (or warned). Currently no such test exists.
- Related findings: ENG-001 (different direction — reading out to caller vs. feeding into LLM), ENG-003 (same root cause: copy-paste across 7 agents).

**Fix path**

In `_summarize_sources` and `_read_voice_samples` (and their equivalents in other agents), add a path confinement check:
```python
try:
    resolved = path.resolve()
    if not resolved.is_relative_to(trusted_root):
        lines.append(f"[{kind}] {s['path']} (outside trusted root — skipped)")
        continue
except Exception:
    ...
```
`trusted_root` should default to `Path.home()` (generous, but catches `/etc` and `C:\Windows`). Document the env var `AGENTSUITE_SOURCE_TRUSTED_ROOT` to let operators tighten it. The kernel's existing `identifiers.py` pattern provides a template for how to add this cleanly. Extract the helper into kernel to fix all 7 agents at once (ties to ENG-003 refactor).

---

### [ENG-005] — Major — Data provenance — `soft_warn_usd` threshold is tracked but never surfaced to the operator during a run

**Evidence**

File: `agentsuite/kernel/cost.py`, lines 80–82:
```python
if not self.warned and self.total.usd > self.cap.soft_warn_usd:
    self.warned = True
```

`self.warned` is set to `True` and `cap_warned: true` appears in `cost_summary.json`. However, `BaseAgent._drive` (`base_agent.py`) never reads `cost_tracker.warned` and emits no runtime warning. `_emit_stage_progress` emits `[OK] stage complete (Xs, $N)` to stderr but does not check or emit the soft-warn flag. The operator only learns about the soft warn after the run completes by reading `cost_summary.json` — by which time the full cap has already been consumed.

**Why this matters**

The soft warning exists precisely to let an operator halt a run before it hits the hard cap. If it is never surfaced during the run, it provides no value as an early warning. An operator monitoring cost in real time sees the same progress lines whether cost is $0.05 or $4.80. The only protection is the hard cap, which terminates the run rather than allowing a graceful exit. This is not a correctness bug — costs are tracked and capped correctly — but it degrades the operator experience for high-cost runs.

**Blast radius**
- Adjacent code: `agentsuite/kernel/base_agent.py` (`_drive` and `_emit_stage_progress`). No other callers.
- User-facing: Operators running high-cost agents (especially the 9-artifact spec stage) see no intermediate cost signal until after the run.
- Migration: None. Additive stderr line.
- Tests to update: Add an integration test asserting that a stderr warning line is emitted when soft_warn_usd is exceeded mid-run.
- Related findings: None.

**Fix path**

In `BaseAgent._drive`, after each `store.save(state)` / `_emit_stage_progress` call, add:
```python
if cost_tracker.warned and not _soft_warn_emitted:
    _soft_warn_emitted = True
    try:
        sys.stderr.write(
            f"[WARN] cost ${cost_tracker.total.usd:.4f} exceeds soft warn "
            f"${cost_tracker.cap.soft_warn_usd:.2f}. "
            f"Hard cap: ${cost_tracker.cap.hard_kill_usd:.2f}\n"
        )
        sys.stderr.flush()
    except Exception:
        pass
```
This respects `AGENTSUITE_QUIET` if the same env-check guard is applied.

---

### [ENG-006] — Minor — Correctness — `extract_json` fallback for objects with trailing prose uses `rfind(end_char)` which can match the wrong closing brace in nested JSON

**Evidence**

File: `agentsuite/llm/json_extract.py`, lines 31–38:
```python
for start_char, end_char in (("{", "}"), ("[", "]")):
    start_idx = stripped.find(start_char)
    if start_idx >= 0:
        end_idx = stripped.rfind(end_char)
        if end_idx > start_idx:
            try:
                return json.loads(stripped[start_idx:end_idx + 1])
```

`rfind` finds the **last** occurrence of `}` in the string. For a response like `{"a": 1} some prose {"b": 2}`, `rfind("}")` returns the index of the second `}`, so the extracted substring is `{"a": 1} some prose {"b": 2}` — which fails `json.loads`. This case is handled benignly (falls through to `raise ValueError`), so the failure mode is "raises on valid JSON with trailing same-structure prose" rather than "returns wrong data". The stress tests do not cover this case.

More importantly: for a response like `{"k": "v"} trailing prose `, `rfind("}")` correctly finds the only `}`, so the common case works. The bug only surfaces when trailing prose itself contains `}` characters (e.g., code examples, JSON fragments in the prose). In that specific case, the fallback will attempt to parse a malformed substring and raise rather than returning the valid first object.

**Why this matters**

The failure mode is a `ValueError` propagation (`qa stage produced invalid JSON`), not a silent data corruption. It would cause a stage failure rather than a wrong result. However, it can produce confusing failures on LLM responses that look like valid JSON to a human but fail the fallback heuristic. It's Minor because the common paths (clean JSON, fenced JSON, single leading preamble) are all correct.

**Blast radius**
- Adjacent code: All 7 agents' qa, extract, and spec stages that call `extract_json`.
- Migration: None.
- Tests to update: Add one parametrized case to `test_json_extraction_variants.py` covering `{"k":"v"} prose with }brace{inside}`.

**Fix path**

Replace the `rfind` with a left-to-right balanced-brace scan that finds the matching closing bracket for the opening one:
```python
def _find_matching_close(s: str, start: int, open_c: str, close_c: str) -> int:
    depth = 0
    for i, c in enumerate(s[start:], start):
        if c == open_c: depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return i
    return -1
```
This is O(n) and handles all nesting correctly. Alternatively, use `json.JSONDecoder().raw_decode(stripped, start_idx)` which does exactly this and is stdlib.

---

### [ENG-007] — Minor — Correctness — `CostCap.from_env` silently accepts negative or zero hard_kill_usd

**Evidence**

File: `agentsuite/kernel/cost.py`, lines 27–31:
```python
raw = os.environ.get("AGENTSUITE_COST_CAP_USD")
if raw is None:
    return cls()
hard = float(raw)
return cls(soft_warn_usd=hard * 0.2, hard_kill_usd=hard)
```

`float("0")` and `float("-1")` are both valid. A cap of `0.0` means `HardCapExceeded` is raised on the very first LLM call (cost > 0.0 > 0.0 is False, but cost = 0.001 > 0.0 is True). A negative cap means no call ever raises. `ValueError` from `float(raw)` (non-numeric string) is also unhandled and propagates as an uncaught exception during provider construction.

**Why this matters**

A typo in `AGENTSUITE_COST_CAP_USD` (e.g., `"$5"`, `"5usd"`) crashes the process at the point `CostCap.from_env()` is called, which is inside `CostTracker.__init__` inside `BaseAgent._drive`. The error message is a bare `ValueError: could not convert string to float` with no mention of which env var caused it. A zero or negative cap silently destroys cost-control semantics.

**Fix path**

Add validation in `from_env`:
```python
hard = float(raw)  # may raise ValueError — catch and re-raise with message
if hard <= 0:
    raise ValueError(f"AGENTSUITE_COST_CAP_USD must be > 0, got {hard}")
```
And wrap the `float(raw)` in a try/except that raises a clear `ValueError(f"AGENTSUITE_COST_CAP_USD={raw!r} is not a valid number")`.

---

### [ENG-008] — Minor — Architecture — `AgentRegistry.get_class` calls `enabled_names()` which re-reads the env var on every call

**Evidence**

File: `agentsuite/agents/registry.py`, lines 55–61:
```python
def get_class(self, name: str) -> Type[BaseAgent]:
    if name not in self.enabled_names():  # re-reads env var
        raise UnknownAgent(...)
    if name not in self._registered:      # redundant — enabled_names() already checks this
        raise UnknownAgent(...)
    return self._registered[name]
```

`enabled_names()` reads `os.environ.get("AGENTSUITE_ENABLED_AGENTS", ...)` and re-parses the comma-separated list every time `get_class` is called. In the MCP server, `build_server()` calls `enabled_names()` once explicitly, then `get_class(name)` for each enabled name — so `enabled_names()` is called `N+1` times where `N` is the number of enabled agents. The second guard `if name not in self._registered` is unreachable: if `enabled_names()` passes, the agent is by definition in `_registered`.

**Why this matters**

Performance impact is negligible for small N. The dead second guard is a code clarity issue. The repeated env-var read is a latent correctness issue: if `AGENTSUITE_ENABLED_AGENTS` is mutated between calls (unusual but possible in tests), `enabled_names()` and `get_class()` could disagree.

**Fix path**

Cache the result of `enabled_names()` or remove the double check in `get_class` (keep `enabled_names()` check, remove the `_registered` check since it is strictly subsumed). The cleanest fix: `return self._registered[name]` after confirming `name` is in `enabled_names()` — one check, no duplication.

---

### [ENG-009] — Minor — Hygiene — `httpx` is a direct dependency in `pyproject.toml` but not used in any production code

**Evidence**

`pyproject.toml` line 26: `"httpx>=0.27,<1"`. Grep of all `agentsuite/` Python files finds zero `import httpx` occurrences. The `_ollama_daemon_running()` function in `resolver.py` uses `urllib.request` (stdlib), not `httpx`.

**Why this matters**

Every declared dependency is a dependency users install. `httpx` pulls in `certifi`, `h11`, and `anyio` as transitive deps. This is ~4 additional packages installed for zero benefit. For a library project whose minimalism is a design goal, this is noise.

**Fix path**

Remove `httpx` from `dependencies` in `pyproject.toml`. If it was intended for future use (e.g., async LLM clients), add a comment to `pyproject.toml` or a GitHub issue tracking the plan, then add it when it is actually used.

---

### [ENG-010] — Minor — Hygiene — `_default_mock_for_cli` in `mock.py` has grown to 140 lines and imports all 7 agents' rubrics and spec-artifact lists at call time

**Evidence**

File: `agentsuite/llm/mock.py`, lines 118–301. The function imports 14 symbols from 7 agent modules, builds a response dict with ~40 keys, and has 5 for-loops that conditionally build per-agent responses. It is called by every CLI test via `monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")`.

**Why this matters**

This function is a maintenance liability: adding a new agent or changing a rubric dimension requires a coordinated update to this function or tests start failing with `NoMockResponseConfigured`. It also front-loads 14 imports into the mock module, breaking the lazy-import discipline that the rest of the codebase follows carefully (e.g., `_INPUTS_BY_AGENT` in `state_store.py`).

**Fix path**

Replace with a lazy-loading builder: each agent module provides a `build_mock_responses() -> dict[str, str]` function, and `_default_mock_for_cli` assembles them by iterating over a registry. This way, adding an 8th agent requires only adding that agent's `build_mock_responses` function — no change to `mock.py`.

---

### [ENG-011] — Minor — Hygiene — `agentsuite/agents/cio/mcp_tools.py` line 180: qa file path mismatch (`qa-scores.json` vs `qa_scores.json`)

**Evidence**

File: `agentsuite/agents/cio/mcp_tools.py`, line 180:
```python
qa_path = run_dir / "qa-scores.json"
```

All QA stages write the file as `qa_scores.json` (underscore), confirmed in `agentsuite/agents/cio/stages/qa.py` line 66:
```python
ctx.writer.write_json("qa_scores.json", report.model_dump(), kind="data", stage="qa")
```

`agentsuite_cio_get_qa_scores` therefore always returns `{"run_id": ..., "scores": None, "note": "QA scores not yet available..."}` even after QA is complete.

**Why this matters**

The `agentsuite_cio_get_qa_scores` MCP tool returns silently wrong data for all completed runs. An operator checking QA scores via MCP always sees "not yet available" regardless of run state.

**Fix path**

Change line 180 to `qa_path = run_dir / "qa_scores.json"`. Also add a test for this tool in `tests/unit/agents/cio/test_mcp_tools.py` that verifies the scores are returned when the file exists.

---

### [ENG-012] — Nit — Hygiene — `base_agent.py` imports `time` and `os` and `sys` inside the function body rather than at module top

**Evidence**

File: `agentsuite/kernel/base_agent.py`, lines 164 (`import time`), 29–30 (`import os`, `import sys` inside `_emit_stage_progress`).

**Fix path**

Move to module-level imports. The lazy imports in `base_agent.py` appear to be a defensive holdover; `os`, `sys`, and `time` are stdlib and always available. Module-level imports are faster and easier to audit.

---

### [ENG-013] — Nit — Hygiene — `AgentRegistry.DEFAULT_ENABLED` is a string but treated as a single-value default; multi-agent defaults are not supported by the field type

**Evidence**

File: `agentsuite/agents/registry.py`, line 17: `DEFAULT_ENABLED = "founder"`. The `enabled_names()` method splits on comma and would correctly handle `"founder,design"` as a default — but the class attribute is `str`, not `list[str]`, which is surprising. The README documents `AGENTSUITE_ENABLED_AGENTS=founder` as the default. This is not a bug; just a slight type/documentation mismatch.

**Fix path**

Either annotate `DEFAULT_ENABLED: str = "founder"` with a comment ("comma-separated list") or switch to `DEFAULT_ENABLED: list[str] = ["founder"]` and join it in `enabled_names`.

---

### [ENG-014] — Nit — Data provenance — `cost.py` `CostCap.from_env` comment says "schema frozen for v0.9.0" on `summary()` but `model` field was added post-v0.9

**Evidence**

File: `agentsuite/kernel/cost.py`, line 89: `"Schema (frozen for v0.9.0)"`. The `model` field in per-stage entries was added in v1.0.1 as part of the CR-102 cost provenance fix. The comment is outdated.

**Fix path**

Update comment to `"Schema (stable as of v1.0.1)"` or remove the version pin.

---

## Patterns and systemic observations

**Root cause 1 — Copy-paste scaling:** The 7-agent architecture was built by duplicating the founder agent's implementation. This was the correct bootstrapping choice (shipping 7 agents fast), but the project has now accumulated enough cross-cutting fixes (CR-101, CR-102, CR-104) that the duplication is starting to carry a real maintenance cost. The next sprint should establish a kernel-level helper for the QA stage pattern (ENG-003) and the source-file confinement check (ENG-004). These two changes eliminate the most dangerous copy-paste vectors.

**Root cause 2 — Input validation discipline at MCP boundaries:** `run_id` and `project_slug` are correctly validated at every callsite via `require_run_dir`/`require_kernel_dir`. `artifact_name` and `template_name` are not. The gap is not from carelessness — the ENG-001 pattern was added for exactly the right reasons in `identifiers.py` and `_common.py` — it was simply missed for the artifact/template parameters. Applying `validate_identifier` at these two callsites and adding a test closes the gap completely.

**What the stress suite gets right:** The recent 87-test stress suite addition is the single best quality investment in v1.0.5. It covers the exact failure modes that caused production crashes (CR-101, CR-102, CR-104), it uses parametrize extensively for exhaustive coverage, and it documents the LLM output shapes that must be handled. This pattern should be extended: every future cross-cutting defensive fix should ship with a corresponding stress test.

---

## Dependency snapshot

| Dependency | Version | Concern |
|---|---|---|
| pydantic | >=2.5,<3 | Clean. Current generation. |
| tenacity | >=8.2,<10 | Clean. No known CVEs. |
| typer | >=0.12,<1 | Clean. |
| httpx | >=0.27,<1 | **Unused in production code.** Should be removed. See ENG-009. |
| jinja2 | >=3.1,<4 | Clean. Prompt templates should be reviewed for user-input injection surface. |
| anthropic | >=0.40,<1 (optional) | Clean. Current SDK. |
| openai | >=1.50,<3 (optional) | Clean. Current SDK. |
| google-genai | >=1.0,<2 (optional) | Clean. Current SDK. |
| ollama | >=0.4,<1 (optional) | Clean. |
| mcp | >=1.0,<2 (optional) | Clean. |

---

## Appendix: artifacts reviewed

**Source files read:**
- `agentsuite/__init__.py`
- `agentsuite/__version__.py`
- `agentsuite/cli.py` (lines 1–80)
- `agentsuite/mcp_server.py`
- `agentsuite/mcp_models.py` (skimmed)
- `agentsuite/kernel/__init__.py` (skimmed)
- `agentsuite/kernel/base_agent.py`
- `agentsuite/kernel/schema.py`
- `agentsuite/kernel/cost.py`
- `agentsuite/kernel/qa.py`
- `agentsuite/kernel/state_store.py`
- `agentsuite/kernel/artifacts.py`
- `agentsuite/kernel/identifiers.py`
- `agentsuite/kernel/approval.py`
- `agentsuite/llm/base.py`
- `agentsuite/llm/anthropic.py`
- `agentsuite/llm/openai.py`
- `agentsuite/llm/ollama.py`
- `agentsuite/llm/gemini.py` (referenced; not fully read — pattern confirmed via provider protocol)
- `agentsuite/llm/mock.py`
- `agentsuite/llm/pricing.py`
- `agentsuite/llm/resolver.py`
- `agentsuite/llm/retry.py`
- `agentsuite/llm/json_extract.py`
- `agentsuite/agents/registry.py`
- `agentsuite/agents/_common.py`
- `agentsuite/agents/founder/agent.py`
- `agentsuite/agents/founder/input_schema.py`
- `agentsuite/agents/founder/rubric.py` (skimmed for structure)
- `agentsuite/agents/founder/mcp_tools.py`
- `agentsuite/agents/founder/stages/intake.py`
- `agentsuite/agents/founder/stages/extract.py`
- `agentsuite/agents/founder/stages/spec.py`
- `agentsuite/agents/founder/stages/execute.py`
- `agentsuite/agents/founder/stages/qa.py`
- `agentsuite/agents/cio/stages/qa.py`
- `agentsuite/agents/cio/mcp_tools.py` (lines 140–250)
- `agentsuite/agents/trust_risk/mcp_tools.py` (artifact/template sections)
- `agentsuite/agents/trust_risk/stages/qa.py` (confirmed identical pattern)
- `pyproject.toml`
- `CLAUDE.md` (project-level)

**Test files read:**
- `tests/stress/test_json_extraction_variants.py`
- `tests/stress/test_qa_rubric_variants.py`
- `tests/integration/test_founder_pipeline.py` (lines 1–30)
- `tests/unit/kernel/test_cost.py` (references)

**Grep passes run:**
- All `extract_json` and `json.loads` callsites in `agentsuite/agents/`
- All `revision_instructions` type guards across 7 qa stages
- All `artifact_name`/`template_name` path constructions in all `mcp_tools.py` files
- All `read_text` callsites outside `run_dir`-scoped paths
- All `pytest.skip` / `pytest.mark.skip` / `@xfail` occurrences in test suite
- All `AGENTSUITE_*` env var references
- All `soft_warn` / `cap_warn` references in kernel and CLI
- Dependency usage: `httpx` import grep across `agentsuite/`
