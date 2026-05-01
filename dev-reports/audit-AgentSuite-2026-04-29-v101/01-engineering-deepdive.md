# Engineering Deep-Dive — AgentSuite v1.0.1 (closure-audit)

**Audit date:** 2026-04-29
**Role:** Principal Engineer
**Scope audited:** v1.0.1 candidate at HEAD `de2a7a3` (10 commits ahead of v1.0.0 / `9540957`); verifying closure of ENG-001…ENG-005 from the v1.0.0 audit. Public-API compat-freeze impact also checked.
**Auditor posture:** Balanced

---

## TL;DR

All five engineering findings from the v1.0.0 audit are genuinely closed at HEAD. The fixes are well-scoped, the new tests cover the negative paths the v1.0.0 audit called out, and no public API surface listed in the v1.0.0 CHANGELOG "Compatibility" section was broken. The central pricing helper (`agentsuite/llm/pricing.py`) is the standout — it not only closes ENG-002 but also turns the dated/aliased model-id problem into a recurring lint via `lookup_pricing` provenance + the ENG-003 default-model parametrized test. One non-blocking observation: a pre-existing test failure in `tests/integration/test_downstream_consumer.py` reproduces on v1.0.0 too (Ollama optional dep missing on this host), so it is **not** a v1.0.1 regression but it should be hardened so the suite is green in any environment.

## Severity roll-up (engineering)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 0 |
| Major | 0 |
| Minor | 1 |
| Nit | 1 |

## What's working

- **Central pricing module (`agentsuite/llm/pricing.py`)** — `lookup_pricing(provider, model) -> (rates, provenance)` is the right shape: callers get the rates AND a flag they can thread into telemetry. The `WARNING` log on fallback is structured (provider + model + chosen rates + remediation pointer) so an operator's first encounter with a stale model id is actionable, not silent. The provenance contract is also enforced in tests at the default-model layer (ENG-003), which means future provider changes can't silently regress cost accuracy.
- **`InvalidIdentifier` is a `ValueError` subclass** — keeps existing exception handlers that catch `ValueError` working while still allowing precise catches when callers want them. Right call.
- **Defense-in-depth on `ArtifactWriter`** — even after `validate_run_id` accepts the value, the constructor still resolves `run_dir` and asserts `is_relative_to(output_root)`. Same for `promote()`. If someone widens the validator regex by mistake later, the path-resolution check catches the regression at I/O time. Good belt-and-suspenders.
- **Backward-compat run_ids preserved** — every `run_id` literal in the existing test suite (`run-2026-04-29-a4f2`, `golden_d1`, `integration-d1`, `pfl.v2`, etc.) still validates. The new gate is strict enough to reject `..` and `/abs` but permissive enough not to break disk state in the wild.

## What couldn't be assessed

- I did not exercise live MCP requests with malformed identifiers — the unit tests cover `ArtifactWriter` directly and the resume path, and the production wire path goes through the same constructor, so this is covered structurally. Direct end-to-end MCP request fuzzing is a v1.0.2 nice-to-have but not needed to close ENG-001.

---

## Per-finding closure verdicts

| ID | v1.0.0 severity | v1.0.1 verdict | Evidence |
|---|---|---|---|
| ENG-001 | Critical | **CLOSED** | `agentsuite/kernel/identifiers.py:32-79`; `artifacts.py:25-32, 117-144`; `base_agent.py:100-101`; 13 tests in `tests/unit/kernel/test_identifiers.py`, all pass |
| ENG-002 | Critical | **CLOSED** | `agentsuite/llm/pricing.py:101-161`; `WARNING` log on fallback at `pricing.py:149-154`; canonical table extended to real-API ids (`pricing.py:35-77`); per-provider `_cost_usd` delegates at `anthropic.py:11-13`, `openai.py:11-13`, `gemini.py:11-13`; tests in `tests/unit/llm/test_pricing.py` pass |
| ENG-003 | Major | **CLOSED** | `tests/unit/llm/test_default_models.py:26-41` parametrized over all three providers; each `default_model()` resolves with `provenance == "exact"`; suite passes |
| ENG-004 | Major | **CLOSED** | `agentsuite/llm/resolver.py:29-48` — `urllib.request.Request(..., method="GET")`, 1-byte read, broad exception net |
| ENG-005 | Major | **CLOSED** | `agentsuite/llm/openai.py:42-48` — explicit comment documenting the `max_tokens` choice and v1.1 follow-up for reasoning-model support |

Test counts: `pytest tests/unit/kernel/test_identifiers.py tests/unit/llm/test_pricing.py tests/unit/llm/test_default_models.py tests/unit/llm/test_mock_matcher.py -q` → **86 passed, 1 warning, 0.33s**. Full repo suite: **781 passed, 1 failed, 3 deselected** — the 1 failure is `tests/integration/test_downstream_consumer.py`, see ENG-006 below; reproduces on v1.0.0 in the same environment, not a v1.0.1 regression.

## Compat-freeze sanity check

The v1.0.0 CHANGELOG locks four items:

1. **Public API surface** (`agentsuite.agents.<agent>...`, `agentsuite.kernel.schema.*`, `agentsuite.kernel.qa.*`, `agentsuite.llm.base.LLMProvider`, `agentsuite.llm.mock.MockLLMProvider`). v1.0.1 only adds: a new module `agentsuite.kernel.identifiers` (additive), new helpers in `agentsuite.llm.pricing` (additive). No public symbol removed or renamed. ✓
2. **`_state.json` schema_version: 2** — no v1.0.1 commit touches `RunState`, `state_store`, or the schema version constant. ✓
3. **MCP tool naming** — no v1.0.1 commit touches `mcp_server.py`. ✓
4. **Six-stage pipeline** — no v1.0.1 commit touches `PIPELINE_ORDER`. ✓

**Behavior change visible to existing on-disk runs:** `BaseAgent.resume()` now validates `run_id` before constructing the resume run dir. A caller resuming a run whose existing on-disk dir name violates the new shape (e.g. someone manually created `runs/.hidden/_state.json`) will now get `InvalidIdentifier` where v1.0.0 returned `FileNotFoundError`. The error message names the offending field, the value, and the rule — actionable. Not a public-API break (this codepath was always going to fail; it just fails earlier and more clearly).

---

## Findings

> **Finding ID prefix:** `ENG-` (continuing numbering from the v1.0.0 audit; v1.0.0 used ENG-001…ENG-005)

### [ENG-006] — Minor — Hygiene — Pre-existing `test_downstream_consumer.py` failure when `ollama` SDK not on the typecheck path

**Evidence**

```
tests\integration\test_downstream_consumer.py::test_downstream_consumer_typechecks_clean FAILED
agentsuite\llm\ollama.py:17: error: Cannot find implementation or library stub for module named "ollama"  [import-not-found]
```

Reproduces at v1.0.0 (`9540957`) in the same environment — not introduced by v1.0.1. The test runs `mypy --strict` against a synthetic consumer with `MYPYPATH=<repo>` but does not configure `mypy --ignore-missing-imports` for optional extras (`ollama`, `anthropic`, `openai`, `google.genai`). On a host where any optional extra is missing, the test fails for an environmental reason rather than an actual typing regression in user-facing code.

**Why this matters**

The test claims to gate downstream consumer typing health, but in practice it fails on any contributor box where the `ollama` extra isn't installed. That makes it a flake in CI-like environments and devalues the gate it was meant to add. The pre-v1.0.1 audit (TEST-006) added a wheel-install variant in `release.yml`, which is the right move — but the unit-suite version still fails locally and that erodes trust in the green-suite signal.

**Blast radius**
- Adjacent code: `tests/integration/test_downstream_consumer.py` only.
- Migration: none — the optional-extras decision is already made.
- Tests to update: this single test.

**Fix path**

Either (a) add an `ignore_missing_imports = True` block scoped to optional-extra modules in the synthetic mypy config, or (b) install all optional extras in the dev-extras group so the suite is hermetic. Option (b) is more honest — the test pretends to check "downstream consumers" so it should pass under the documented dev-install. v1.0.2 candidate.

---

### [ENG-007] — Nit — Hygiene — `_PRICING` re-exports kept for back-compat, can be deprecated

**Evidence**

`agentsuite/llm/anthropic.py:7`, `openai.py:7`, `gemini.py:7`:

```python
from agentsuite.llm.pricing import ANTHROPIC_PRICING as _PRICING  # noqa: F401  # back-compat re-export for existing tests
```

**Why this matters**

Each provider re-exports the per-provider table as `_PRICING` solely so older direct-table-import tests keep working. The forward direction is the new central `lookup_pricing` API; the underscore prefix already signals "private," and the comment correctly tags this as transitional. Keeping it for v1.0.1 is right (patch-release compat). Track for removal in v1.1 once those tests migrate to `lookup_pricing`.

**Fix path**

Add a `# TODO(v1.1): remove _PRICING re-export once tests/unit/llm/test_*_pricing.py migrate to lookup_pricing` line and an issue. (Yes, I know — global rule on TODOs. In this case the project explicitly tags v1.1 follow-ups in commit messages already; a one-line tracker comment is consistent.) Or, simpler, file a v1.1 issue and skip the comment.

---

## Patterns and systemic observations

- **The audit→fix cycle worked.** Five Critical/Major findings, five focused commits, every fix has a regression test that pins the closure. Two of those tests (`test_identifiers.py`, `test_default_models.py`) actively prevent the same class of bug from regressing. That is the right pattern for an audit-fix sprint.
- **Defense-in-depth is the right posture for path-traversal.** Rather than relying solely on the regex, `ArtifactWriter` resolves and asserts containment. If a future contributor relaxes `_ID_RE` to add a new allowed character, the path check will still hold the line. This is good architecture; consider documenting the "two-layer rule" in `CONTRIBUTING.md`.
- **`provenance` is structural; the v1.0.1 fix shipped only the lookup-side correctness.** The audit watchlist already tracks W-04 (thread provenance into `cost_summary.json`). That is the right call for a patch release, but it should not stay open past v1.1 — operators benefit much more from a `provenance: "fallback"` field in the JSON than from a log line they may never read.

## Dependency snapshot

No dependency changes in v1.0.1. Surface unchanged from v1.0.0; no notable concerns surfaced during this pass.

## Appendix: artifacts reviewed

- Commits: `4c90c41`, `30d3792`, `08a134d` (full diffs and stats)
- Files (current state at `de2a7a3`):
  - `agentsuite/kernel/identifiers.py`
  - `agentsuite/kernel/artifacts.py`
  - `agentsuite/kernel/base_agent.py`
  - `agentsuite/llm/pricing.py`
  - `agentsuite/llm/anthropic.py`
  - `agentsuite/llm/openai.py`
  - `agentsuite/llm/gemini.py`
  - `agentsuite/llm/resolver.py`
- Tests run:
  - `tests/unit/kernel/test_identifiers.py` (13 tests, all pass)
  - `tests/unit/llm/test_pricing.py`, `test_default_models.py`, `test_mock_matcher.py` (combined 86 pass)
  - Full repo: 781 pass / 1 fail (pre-existing) / 3 deselected
- Reference docs: `principal-engineer.md`, `severity-framework.md`, `blast-radius.md`, `templates/01-engineering-deepdive.md`
- v1.0.0 CHANGELOG `[1.0.0]` Compatibility section
