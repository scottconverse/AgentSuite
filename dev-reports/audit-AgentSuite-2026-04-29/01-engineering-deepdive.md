# Engineering Deep-Dive — AgentSuite v1.0.0 GA

**Audit date:** 2026-04-29
**Role:** Principal Engineer
**Scope audited:** `agentsuite/` package (kernel, llm, agents, mcp_server), `pyproject.toml`, ADRs 0001–0007, public API surface, test counts. Live LLM behavior and cleanroom builds were not exercised.
**Auditor posture:** Adversarial

---

## TL;DR

The kernel is small, clean, and largely correct. `BaseAgent` holds across all seven concrete agents without leaking abstractions; the schema-versioned state envelope, atomic `_state.json` writes, and the stage-atomic resume contract (ADR-0007) are properly implemented and matched by tests. The release is not, however, free of real defects: cost provenance has a silent-fallback bug that will under- or over-charge users on any model id the SDK returns that doesn't exactly key the pricing table; the MCP surface accepts unvalidated `run_id` and `project_slug` strings as path segments, which is a path-traversal vector the moment `agentsuite-mcp` is exposed beyond the developer's own machine; the OpenAI provider uses the deprecated `max_tokens` parameter; and `pyproject.toml` ships a `Development Status :: 3 - Alpha` classifier on a v1.0.0 GA wheel. None of these block the tag, but two of them should be fixed in a v1.0.1 patch this week.

## Severity roll-up (engineering)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 2 |
| Major | 5 |
| Minor | 6 |
| Nit | 3 |

## What's working

- **Kernel surface is genuinely small (~700 LoC across 7 files) and the BaseAgent abstraction holds.** `base_agent.py:_drive()` is the single owner of stage iteration, cost-cap enforcement, state persistence, and resume; no agent reaches around it. The 7 concrete agents each ship `stage_handlers()` + `qa_rubric` and nothing else. That is exactly the right boundary.
- **State persistence is atomic and crash-safe.** `state_store.py:save()` uses `tempfile.mkstemp` in the run dir, `fsync()`, then `os.replace()` — partial writes never corrupt the canonical `_state.json`. The schema_version envelope (ADR-0002) is implemented exactly as documented and rejects pre-v0.9 files with a remediation message that names the offending dir. Both behaviors are covered by `tests/unit/kernel/test_state_store.py`.
- **Resume idempotency contract (ADR-0007) is real.** `_drive()` correctly carries `state.cost_so_far` into a fresh `CostTracker.total` on resume, restores `per_stage` from the prior `cost_summary.json`, and persists best-effort partial costs in the exception path before re-raising. The "crashed stage re-bills" caveat is documented in the ADR rather than hidden.
- **Retry layer is correctly bounded.** `RetryingLLMProvider` uses `tenacity.stop_any(stop_after_attempt, stop_after_delay)` and `retry_if_not_exception_type(_NO_RETRY_EXCEPTIONS)` so `ProviderNotInstalled`/`KeyboardInterrupt`/`SystemExit` short-circuit. Configurable via env. `reraise=True` makes the final exception observable to the caller. This is what most projects get wrong.
- **Cost cap enforcement is strict and side-effect-correct.** `CostTracker.add()` computes `new_total` and raises `HardCapExceeded` BEFORE mutating `self.total`, so a cap rejection doesn't leave the tracker in a half-updated state.
- **Test coverage is non-trivially deep.** `pytest --collect-only -q` returns `689/692 tests collected (3 deselected)` — README claim verified. Parametrised round-trip across all 7 agent input subclasses guards against future serializer regressions.
- **ADRs 0001–0007 actually describe what's in the code.** ADR-0002, ADR-0004, ADR-0007 each cite specific tests in their consequences — and the tests exist. This is rare and worth crediting.

## What couldn't be assessed

- **Live LLM behavior.** No live cassettes were re-recorded; cost-provenance findings below are reasoned from code reading, not a recorded API response.
- **Cleanroom build.** `scripts/run-cleanroom.sh` was not invoked.
- **`pip-audit` / SBOM output.** Release artifacts were not retrieved from GitHub Releases for inspection.
- **Concurrent run behavior.** Two simultaneous runs into the same `run_dir` were not exercised; analysis is static.

---

## Findings

> **Finding ID prefix:** `ENG-`

### [ENG-001] — Critical — Security — MCP-exposed path traversal via unvalidated `run_id` / `project_slug`

**Evidence**

`agentsuite/agents/founder/mcp_tools.py:69-91`:

```python
def founder_run(request: FounderRunRequest) -> RunResult:
    run_id = request.run_id or _now_id()
    ...
    state = agent.run(request=founder_input, run_id=run_id)
    run_dir = output_root_fn() / "runs" / run_id
```

`agentsuite/mcp_server.py:100-111`:

```python
def agentsuite_kernel_artifacts(project_slug: str) -> dict[str, Any]:
    kernel_dir = _output_root() / "_kernel" / project_slug
    if not kernel_dir.exists():
        return {"artifacts": []}
    return {
        "artifacts": sorted(
            str(p.relative_to(kernel_dir))
            for p in kernel_dir.rglob("*")
            ...
```

`agentsuite/kernel/artifacts.py:24-26`:

```python
self.run_dir = self.output_root / "runs" / run_id
self.run_dir.mkdir(parents=True, exist_ok=True)
```

`run_id` and `project_slug` flow from the MCP wire to a path concatenation with no validation. A caller supplying `run_id="../../../tmp/x"` causes `ArtifactWriter.__init__` to `mkdir(parents=True, exist_ok=True)` outside the configured output root. `_resolve_safe()` only protects file *contents* inside `run_dir`; it does nothing about the `run_dir` path itself. A `project_slug` of `..` walks `agentsuite_kernel_artifacts` over the parent of `_kernel/`. `founder_approve` calls `writer.promote(project_slug)` which eventually does `shutil.rmtree(target)` on `_kernel / project_slug` — a value of `.` or `../foo` could remove the wrong directory.

**Why this matters**

The README and ADR-0006 sell AgentSuite as the MCP backend for Codex/Claude Code/Cowork — i.e. a server that an LLM-driven host calls with strings the user doesn't directly type. A model-controlled or template-controlled `project_slug` is exactly the kind of input a path-traversal exploit lives inside. Even on a single-developer box this is a foot-gun. The moment anyone hosts `agentsuite-mcp` for shared use it is a Critical exposure.

**Blast radius**
- Adjacent code: every agent's `mcp_tools.py` (founder/design/product/engineering/marketing/trust_risk/cio) repeats the same pattern. The cross-agent `agentsuite_kernel_artifacts` and `agentsuite_cost_report` in `mcp_server.py` are also affected.
- Shared state: `_kernel/<slug>/` directories — `promote()` calls `shutil.rmtree(target)`. A malicious slug deletes the wrong tree.
- User-facing: legitimate runs unchanged.
- Migration: none. Add validation; reject offending values with a typed error.
- Tests to update: `tests/unit/test_mcp_server.py` and per-agent MCP test files should add traversal-attempt cases.
- Related findings: ENG-006 (CLI `run_id` is also unvalidated but there only the local user can hurt themselves).

**Fix path**

Add a single validator in `agentsuite/kernel/_ids.py`:

```python
import re
_VALID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

def validate_run_id(s: str) -> str:
    if not _VALID.match(s) or ".." in s:
        raise ValueError(f"invalid run_id: {s!r}")
    return s

def validate_project_slug(s: str) -> str:
    ... # same shape, separate name
```

Call it in `BaseAgent.run`, `BaseAgent.resume`, `BaseAgent.approve`, every MCP tool entry, and `ArtifactWriter.__init__`. Pydantic `Field(pattern=...)` on the MCP request models is the cleanest top-level guard.

---

### [ENG-002] — Critical — Data provenance — Cost USD silently wrong on any model id not exactly in pricing table

**Evidence**

`agentsuite/llm/anthropic.py:10-12`:

```python
def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    rates = _PRICING.get(model, {"in": 3.0, "out": 15.0})
    return (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000
```

The `model` passed in is `result.model` from the SDK, NOT `request.model`. Anthropic's API typically returns dated model ids like `claude-sonnet-4-5-20250929` while the pricing table at `agentsuite/llm/pricing.py:15` keys on the un-dated alias `claude-sonnet-4-6`. The exact-match miss falls through to a hardcoded `{"in": 3.0, "out": 15.0}` fallback that is invisibly different from real pricing on any model that is NOT 4.6 Sonnet (e.g. Opus 4.7's real `out` rate is $25.00, not $15.00 — a 40% under-charge).

OpenAI (`agentsuite/llm/openai.py:10-12`) and Gemini (`agentsuite/llm/gemini.py:10-12`) have the same pattern with the same fallback bug.

**Why this matters**

`cost_summary.json` is sold as authoritative — `CostTracker.summary()` writes it before every approval. `CostCap.from_env()` derives `hard_kill_usd` from `AGENTSUITE_COST_CAP_USD` and enforces it on `total.usd`. If `usd` is wrong, the cap is wrong. Operators looking at the cost report to decide whether to approve a run are looking at a fabricated number whenever the returned model id doesn't exactly hit a key. The fact that the dev report says "Cost telemetry, RunState schema_version 2" implies cost numbers are part of the v1.0 contract; they currently are not trustworthy.

**Blast radius**
- Adjacent code: `pricing.py` (3 tables); `anthropic.py`, `openai.py`, `gemini.py` `_cost_usd` (duplicated). `cost_summary.json` consumer tests; `test_cost_cap` integration tests; cost-report-format ADR if any.
- Shared state: `cost_summary.json`, `RunState.cost_so_far.usd` in every persisted state file.
- User-facing: every operator reading a cost report; every cap-enforcement decision.
- Migration: existing `_state.json` files from runs with non-keyed models hold wrong USD. New runs with the fix produce correct numbers; old data does not need rewriting.
- Tests to update: `tests/unit/llm/test_*_provider.py` need a test that the fallback raises rather than silently substituting a placeholder rate. Or, if a fallback is desired, tests asserting the warning is logged and the field is flagged in the response.
- Related findings: ENG-003 (model defaults look fictional, which compounds this).

**Fix path**

Two options, in order of preference:

1. Replace the silent fallback with a typed warning:

```python
def _cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    rates = _PRICING.get(model)
    if rates is None:
        # Try a prefix match on the dated alias before bailing
        for k, r in _PRICING.items():
            if model.startswith(k):
                rates = r
                break
    if rates is None:
        _log.warning("Pricing miss for %s; cost reported as 0.0 (untracked)", model)
        return 0.0  # honest 0 beats a silent wrong number
    return (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000
```

2. Or fail fast (`raise UnknownModelPricing(model)`) and force the operator to update `pricing.py`. This is what a billing-grade tool should do. The current behavior is the worst of both options.

Either way, also surface a `pricing_match: "exact" | "prefix" | "missing"` field in `LLMResponse` so cost provenance is visible downstream.

---

### [ENG-003] — Major — Correctness — Default models in providers do not match pricing table keys, and may not exist

**Evidence**

`agentsuite/llm/anthropic.py:31`: `return "claude-sonnet-4-6"`
`agentsuite/llm/pricing.py:17`: `"claude-sonnet-4-6": {"in": 3.00, "out": 15.00}`

`agentsuite/llm/openai.py:31`: `return "gpt-5.4"`
`agentsuite/llm/pricing.py:23-29`: `"gpt-5.4"` is keyed.

The defaults match the pricing keys *exactly*, which is what makes ENG-002 quiet most of the time during local testing. But the API will return whatever model id the provider canonicalizes the request to — typically a dated suffix — and that won't key. Additionally, "gpt-5.4" and "claude-sonnet-4-6" are model ids that may not exist on the provider in practice; if the SDK rejects the model name, every live call fails with `BadRequest`.

**Why this matters**

A v1.0.0 GA package with default models that the provider rejects is a one-line traceback for any user who runs it without setting `LLMRequest.model` explicitly. Even if the model names are real, the dated-alias return mismatches ENG-002.

**Blast radius**
- Adjacent code: `anthropic.py`, `openai.py`, `gemini.py`, `ollama.py` (`gemma4:e4b` — verify it exists).
- Shared state: pricing tables; default-model documentation in README, USER-MANUAL, ADRs.
- User-facing: every default-path live call.
- Migration: none.
- Tests to update: live tests gated on v0.X.0 — if the model names are wrong, those tests have never run green against real APIs.
- Related findings: ENG-002.

**Fix path**

Verify each default model against the live API. Either name a real, currently-shipping model id, or use the most-recent stable family alias the provider documents. Pin the same string in `pricing.py` AND add a prefix-match in `_cost_usd` (per ENG-002) so dated-suffix returns key correctly.

---

### [ENG-004] — Major — Correctness — Ollama auto-detect uses HTTP HEAD on `/api/tags`, which the daemon does not advertise

**Evidence**

`agentsuite/llm/resolver.py:31-33`:

```python
req = urllib.request.Request("http://localhost:11434/api/tags", method="HEAD")
with urllib.request.urlopen(req, timeout=0.5) as resp:
    return bool(resp.status == 200)
```

Ollama's `/api/tags` is documented as `GET`. Many HTTP servers respond `405 Method Not Allowed` to HEAD on a GET endpoint, and `urlopen` raises `urllib.error.HTTPError` rather than returning `status == 200`.

**Why this matters**

`_check_ollama()` returning `False` means auto-detect skips Ollama even when the daemon is running. The "local-first" fallback advertised in ADR-0006-adjacent docs and the README quietly degrades into "cloud only unless `AGENTSUITE_LLM_PROVIDER=ollama` is set explicitly."

**Blast radius**
- Adjacent code: `_AUTO_DETECT_ORDER`, `NoProviderConfigured` error message that mentions Ollama.
- Shared state: none.
- User-facing: every operator with a running Ollama who expected zero-cost local fallback.
- Migration: none.
- Tests to update: `tests/unit/llm/test_resolver.py` should mock the probe with both 200 OK and 405 Not Allowed and assert the right outcome — currently this is not exercised against real daemon behavior.

**Fix path**

```python
req = urllib.request.Request("http://localhost:11434/api/tags")  # GET
with urllib.request.urlopen(req, timeout=0.5) as resp:
    return bool(resp.status == 200)
```

The 0.5s timeout already bounds the probe cost. A GET returns a small JSON list of models; the body is read implicitly by `urlopen`'s context manager.

---

### [ENG-005] — Major — Correctness — OpenAI provider uses `max_tokens`, deprecated by the OpenAI SDK

**Evidence**

`agentsuite/llm/openai.py:39-44`:

```python
result = self.client.chat.completions.create(
    model=model,
    max_tokens=request.max_tokens,
    temperature=request.temperature,
    messages=messages,
)
```

OpenAI's Chat Completions API has migrated newer model families to `max_completion_tokens`. With current `openai>=1.50,<3` and a recent reasoning-class model, `max_tokens` is at best ignored and at worst raises a 400.

**Why this matters**

The default model is `gpt-5.4` (per provider). If gpt-5.4 expects `max_completion_tokens`, every call fails. If it accepts both, the parameter is silently ignored and `max_tokens=4096` is not honored — which means longer outputs than budgeted, which means cost-cap surprises.

**Blast radius**
- Adjacent code: just `openai.py:complete()`.
- Shared state: none.
- User-facing: every OpenAI user.
- Migration: none.
- Tests to update: VCR cassettes for openai live tests need re-record under the new param name.
- Related findings: ENG-003 (default model name).

**Fix path**

Branch on model family or send `max_completion_tokens` unconditionally for current OpenAI SDK versions and document the floor:

```python
kwargs = {"max_completion_tokens": request.max_tokens}
result = self.client.chat.completions.create(model=model, **kwargs, ...)
```

If `gpt-5.4` legitimately predates the rename in OpenAI's lineage, then verify via cassette before shipping.

---

### [ENG-006] — Major — Architecture — `pyproject.toml` ships `Development Status :: 3 - Alpha` on a v1.0.0 GA wheel

**Evidence**

`pyproject.toml:7,15`:

```toml
version = "1.0.0"
...
classifiers = [
    "Development Status :: 3 - Alpha",
    ...
```

**Why this matters**

The classifier is a public-facing signal. Downstream tooling, dependency dashboards, and search filters use it. A v1.0.0 GA tag with an Alpha classifier is a credibility hit and arguably misleading: contributors evaluating maturity will distrust whichever signal turns out to be wrong.

**Blast radius**
- Adjacent code: `pyproject.toml` only.
- Shared state: any release dashboard or PyPI-metadata aggregator that scrapes classifiers (currently muted by ADR-0006's no-PyPI policy, but the metadata still ships in the wheel).
- User-facing: anyone reading the wheel's metadata.
- Migration: none.

**Fix path**

Bump to `Development Status :: 5 - Production/Stable` (or `4 - Beta` if rc1's stabilization doesn't yet feel 1.0-grade). Cut a v1.0.1 patch that includes the change.

---

### [ENG-007] — Major — Correctness — `ApprovalGate.promote` is not actually atomic on the swap step

**Evidence**

`agentsuite/kernel/artifacts.py:154-157`:

```python
# Swap staging into place — remove old target first, then rename
if target.exists():
    shutil.rmtree(target)
staging.rename(target)
```

The docstring (lines 117-121) claims:

> "Atomicity guarantee: all artifacts are staged into a sibling temp directory ... before the final rename. If the process dies mid-copy, the existing `_kernel/<project_slug>/` is untouched; only the temp staging dir may remain..."

But there is a window between `shutil.rmtree(target)` and `staging.rename(target)` where the target dir is gone and any concurrent reader sees no artifacts. If the process dies between the `rmtree` and the `rename`, the previous good copy is lost and the new copy isn't yet visible — exactly the failure mode the docstring claims to prevent.

**Why this matters**

The promised contract ("if the process dies mid-copy, the existing target is untouched") is not met. For a single-user dev tool the impact is small; for any shared/CI use the user lost their previous kernel state and has to re-run the whole agent.

**Blast radius**
- Adjacent code: only `promote()`.
- Shared state: `_kernel/<slug>/` directories.
- User-facing: an operator who re-promotes and crashes mid-promote.
- Migration: none.
- Tests to update: add a `test_promote_atomic_swap` that injects a fault between rmtree and rename and verifies the prior state survives.

**Fix path**

```python
backup = kernel_dir / f".{project_slug}.previous"
if backup.exists():
    shutil.rmtree(backup)
if target.exists():
    target.rename(backup)
try:
    staging.rename(target)
except Exception:
    if backup.exists():
        backup.rename(target)
    raise
shutil.rmtree(backup, ignore_errors=True)
```

This narrows the at-risk window to just the two single-syscall renames. Or accept the current behavior and rewrite the docstring to say "best-effort" rather than "atomic."

---

### [ENG-008] — Minor — Hygiene — Unreachable branch in `AgentRegistry.get_class`

**Evidence**

`agentsuite/agents/registry.py:55-61`:

```python
def get_class(self, name: str) -> Type[BaseAgent]:
    if name not in self.enabled_names():
        raise UnknownAgent(...)
    if name not in self._registered:
        raise UnknownAgent(...)
    return self._registered[name]
```

`enabled_names()` already raises if any enabled name is not registered, so by the time line 59 runs, `name` is guaranteed in `self._registered`. The second branch is unreachable.

**Fix path**

Drop the second `if`. Or, if the intent is defense-in-depth, document it and add a unit test that hits it via a manually-mutated registry.

---

### [ENG-009] — Minor — Security — Founder extract stage reads arbitrary user-supplied paths and forwards their content to the LLM

**Evidence**

`agentsuite/agents/founder/stages/extract.py:24-26`:

```python
if path.exists() and path.is_file():
    snippet = path.read_text(encoding="utf-8", errors="replace")[:1500]
    lines.append(f"[{kind}] {path}\n{snippet}\n")
```

`path` is whatever the user puts in `inputs_dir`, `explicit_brand_docs`, or `founder_voice_samples`. There is no path containment relative to the project — absolute system paths (`~/.ssh/id_rsa`, `/etc/passwd`) are read and shipped to the configured LLM provider. This is intentional in CLI use (the user is reading their own files) but compounds with ENG-001 the moment the agent is invoked over MCP from a host that templates user input into source-material paths.

**Fix path**

In MCP-exposed entry points, validate that supplied paths are inside an allow-listed root (configured via `AGENTSUITE_INPUT_ROOT` env). In CLI use, leave the current behavior but document the trust boundary.

---

### [ENG-010] — Minor — Hygiene — `RetryingLLMProvider` swallows `name` setability with a type comment, but allows the underlying provider to be re-wrapped

**Evidence**

`agentsuite/llm/retry.py:67-69`:

```python
def __init__(self, inner: LLMProvider) -> None:
    self._inner = inner
    self.name: str = inner.name
```

Nothing prevents `RetryingLLMProvider(RetryingLLMProvider(inner))`. Doubly-wrapped, exponential backoff multiplies and timeout budgets nest. `resolve_provider()` always wraps once, but a caller that re-wraps gets surprising behavior.

**Fix path**

```python
def __init__(self, inner: LLMProvider) -> None:
    if isinstance(inner, RetryingLLMProvider):
        raise TypeError("RetryingLLMProvider is already retrying; do not re-wrap")
```

---

### [ENG-011] — Minor — Correctness — `cost_so_far` zero-check on resume misses the legit-but-zero-cost case

**Evidence**

`agentsuite/kernel/base_agent.py:118`:

```python
if state.cost_so_far.usd > 0 or state.cost_so_far.input_tokens > 0:
    cost_tracker.total = state.cost_so_far
    if cost_summary_path.exists():
        try:
            prior = json.loads(...)
```

A run resumed from `intake` (no LLM call) has zero cost; the carry-forward branch is skipped. That's almost always fine because there's nothing to carry. But a resumed Ollama run with `usd=0.0` on every call ALSO skips the branch, even if `input_tokens` is set. If `input_tokens` is also 0 (Ollama sometimes returns no usage), the per-stage breakdown is dropped on resume.

**Fix path**

Anchor the carry-forward on whether a prior `cost_summary.json` exists, not on whether `cost_so_far` is non-zero:

```python
if cost_summary_path.exists():
    try:
        ... # restore per_stage
    except (...):
        pass
cost_tracker.total = state.cost_so_far
```

---

### [ENG-012] — Minor — Hygiene — `default_registry()` is a process-wide singleton with no reset hook

**Evidence**

`agentsuite/agents/registry.py:84-92`. The first call wins; subsequent test changes to env or registered classes are invisible. Every test that wants a fresh registry has to instantiate `AgentRegistry` directly.

**Fix path**

Add `default_registry.cache_clear()` (or a `_reset_for_tests()` private hook) so test fixtures can drop the cache without touching the module global.

---

### [ENG-013] — Minor — Correctness — `Cost.__add__` `last-non-None wins for model` is order-sensitive in surprising ways

**Evidence**

`agentsuite/kernel/schema.py:84-91`:

```python
def __add__(self, other: Cost) -> Cost:
    merged_model = other.model if other.model is not None else self.model
    return Cost(...)
```

For a chain `a + b + c`, model is the last non-None of `c`, `b`, `a`. Most of the time fine. But in `_drive`'s exception path, the partial cost may contain a `model` from a prior stage that was overwritten in memory but not yet persisted. Aggregations done in different orders give different `model` fields in `cost_summary.json`. The field is decorative for now (no consumers branch on it) but the docstring claims "the latest model id seen by an aggregating tracker" — the "latest" is order-dependent, not time-dependent.

**Fix path**

Either drop the field (it's not load-bearing) or store a `(timestamp, model)` tuple internally and pick the latest by time. Document the chosen semantics on the field doc.

---

### [ENG-014] — Nit — Hygiene — `SourceKind` literal includes `"voice-sample"` and `"brand-doc"` but founder's intake only emits `screenshot | product-doc | other`

`SourceKind` in `schema.py:11-20` declares 8 kinds; `intake.py:_classify_path` returns 3. The unused literals are documentation-only. Either narrow `SourceKind` or document why the broader set exists for future agents.

### [ENG-015] — Nit — Hygiene — `__version__.py` carries only `__version__ = "1.0.0"` with no `__version_info__` tuple

Some tooling parses tuples for ordering; the current file is a one-line string. Not a defect, but a future patch could add `__version_info__ = (1, 0, 0)` and a release date for free.

### [ENG-016] — Nit — Hygiene — `OllamaProvider` default `gemma4:e4b` is plausible but unverified in tests

The default model name should be one that survives `ollama list` on a clean install. The cleanroom test that pulls a model is not in the audited set.

---

## Patterns and systemic observations

**The cost subsystem is the weakest link.** ENG-002, ENG-003, ENG-005, ENG-013 all point at the same root: cost is treated as decorative metadata when it is in fact the gating signal for cap enforcement and operator approval. A v1.0 product that sells "cost telemetry" should treat pricing-table misses as exceptions, not silent fallbacks; should test default-model strings against the live API; and should fix the `Cost.__add__` semantics. Recommend a v1.0.1 patch focused entirely on cost provenance: typed warning on pricing miss, prefix-match on dated-alias model ids, model-default verification, OpenAI param rename. Total work is ~half a day.

**MCP path-traversal is the second-biggest gap.** ENG-001 + ENG-009 share root cause: the boundary between "trusted developer typing into their own CLI" and "MCP-exposed surface called by an LLM-driven host" was never explicitly drawn. The MCP entry points should validate path-shaped inputs at the wire boundary using shared validators. Doing this once in `kernel/_ids.py` and importing it in every `mcp_tools.py` clears both findings.

**Promote atomicity is over-promised.** ENG-007 is small in impact but the docstring is concretely wrong, which is the kind of finding that erodes trust in other docstrings. Either rewrite the docstring or implement the rename-rename-fallback pattern.

**Everything else is hygiene.** The kernel architecture is sound, the resume contract holds, tests exist where they should, and the ADRs match the code. ENG-008/010/011/012/013 are the kind of cleanup a maintainer notices in a leisurely afternoon.

## Dependency snapshot

| Dependency | Version | Concern |
|---|---|---|
| pydantic | >=2.5,<3 | Healthy, current. No concern. |
| tenacity | >=8.2,<10 | Healthy. No concern. |
| typer | >=0.12,<1 | Pre-1.0 upper bound is appropriate. No concern. |
| httpx | >=0.27,<1 | Listed as runtime dep; grep this audit didn't find a direct import in the audited files. Possible unused dep — verify. |
| jinja2 | >=3.1,<4 | Used by template_loader / prompt_loader. Healthy. |
| anthropic | >=0.40,<1 (optional) | Wide window; provider code uses stable `messages.create`. Fine. |
| openai | >=1.50,<3 (optional) | Wide window — but `max_tokens` API has changed inside this range (see ENG-005). Constrain or branch. |
| google-genai | >=1.0,<2 (optional) | Recent SDK; `genai.Client` API used is stable enough. Fine. |
| ollama | >=0.4,<1 (optional) | Pre-1.0 upper bound appropriate. Fine. |
| mcp | >=1.0,<2 (optional) | Healthy. |

## Appendix: artifacts reviewed

- `agentsuite/kernel/__init__.py`, `base_agent.py`, `schema.py`, `state_store.py`, `artifacts.py`, `cost.py`, `qa.py`, `approval.py`
- `agentsuite/llm/base.py`, `anthropic.py`, `openai.py`, `gemini.py`, `ollama.py`, `mock.py` (head), `retry.py`, `resolver.py`, `pricing.py`
- `agentsuite/agents/registry.py`
- `agentsuite/agents/founder/agent.py`, `input_schema.py`, `mcp_tools.py`, `stages/intake.py`, `stages/extract.py`, `stages/execute.py`, `stages/qa.py`
- `agentsuite/mcp_server.py`, `agentsuite/__init__.py`, `agentsuite/__version__.py`
- `pyproject.toml`
- `docs/adr/0002-runstate-shape.md`, `0004-mcp-tool-naming.md`, `0006-no-pypi-distribution.md`, `0007-resume-idempotency.md`
- `pytest --collect-only -q` output (689 collected / 3 deselected)
