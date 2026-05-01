# Sprint 2 — Test Engineering Deep-Dive

**Audit date:** 2026-04-30
**Role:** Test Engineer
**Scope audited:** Sprint 2 new/modified test files (TEST-002, TEST-003, TEST-004, ENG-004) plus coverage gap assessment against Sprint 2 code changes (ENG-002, ENG-003, ENG-004, ENG-005, QA-003, QA-004, QA-005, UX-004, UX-006)
**Auditor posture:** Balanced

---

## TL;DR

The Sprint 2 test additions are solid: 25 SequentialMockLLMProvider unit tests cover the core behavioral contract thoroughly, 4 MCP tool test files consistently exercise the UX-006 slug filter and RevisionRequired structured-error contract, and 7 revision cycle integration tests prove the two-leg flow from first-failing QA through approval. The primary weaknesses are two uncovered code paths: (1) no test verifies that an agent-level `spec_stage` or `qa_stage` thin wrapper actually delegates to the kernel — a delegation bug would silently ship; (2) path confinement tests omit symlinks, which is the most realistic real-world traversal vector. All five directly-targeted Sprint 2 code behaviors (QA-003, QA-004, ENG-002, UX-004/UX-006 status, ENG-005 cost warning) are covered in existing or new tests. No skipped tests found in Sprint 2 files.

---

## Severity roll-up (Sprint 2 tests)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 0 |
| Major | 2 |
| Minor | 3 |
| Nit | 2 |

---

## What's working

- **SequentialMockLLMProvider contract tested comprehensively** — TEST-002 (tests/unit/llm/test_mock.py lines 62–251) covers: ordering, repeat-last, single-item repeat, unmatched-raises, error-message keyword content, caller-list immutability, re-instantiation reset, longest-match-first with 2 and 3 candidate keys, system-field matching, empty-sequences case, call recording, response shape (model, usd, output_tokens), class name, and custom name override. Functionally complete for the behavioral contract.

- **Revision cycle integration tests drive a real two-leg pipeline** — TEST-004 (tests/unit/test_revision_cycle.py) exercises FounderAgent end-to-end with real stage wiring: no mocked stages, only the LLM is stubbed. This is a genuine integration test, not "integration in name only." Cost accumulation, file promotion, qa_report.md presence, and qa_scores.json content are all asserted at the correct points.

- **UX-006 slug filter tested consistently across all 4 MCP agents** — Each of engineering, marketing, trust_risk, and cio test files includes a three-slug scenario (slug-a, slug-b, no-slug) with assertions on exact count and run_id match. Pattern is correct and not copy-paste that diverged.

- **ENG-002 production guard is tested** — tests/unit/test_cli.py lines 426–441 test both the guard-fires case (no PYTEST_CURRENT_TEST) and the normal-test case (PYTEST_CURRENT_TEST set). The security-critical RCE guard has real coverage.

- **QA-003 from_env error handling is tested** — tests/unit/kernel/test_cost.py lines 192–217 cover non-numeric, empty-string, and valid-numeric inputs with assertion on the actionable error message. This was the bug the fix addressed.

- **QA-004 model_version fallback is tested** — tests/unit/llm/test_gemini.py lines 63–101 cover three distinct cases: model_version present, model_version absent from response object (spec=[]), and model_version=None. Full coverage.

- **ENG-005 cost warning and suppression are tested** — tests/unit/kernel/test_base_agent.py lines 163–241 test the zero-cost omission, non-zero cost format, and the warning-emitted-once contract through a concrete agent execution.

- **No skipped tests in Sprint 2 files** — Grep across all audited test files confirms zero `pytest.mark.skip`, `pytest.mark.xfail`, `xit`, or `.skip(` patterns in the new/modified Sprint 2 files.

- **Parametrized traversal attack variants for trust_risk and cio** — tests/unit/agents/trust_risk/test_mcp_tools.py and cio/test_mcp_tools.py use `@pytest.mark.parametrize` over 7 malicious artifact_name variants (raw `..`, URL-encoded, double-encoded, null-byte, absolute path). This is adversarial testing done right.

---

## What couldn't be assessed

- **CI run history / flakiness history** — CI log history is not accessible from this environment. Cannot confirm whether the new revision cycle tests are flaky under load. The tests depend on exact SequentialMockLLMProvider ordering; they appear deterministic but have not been observed across multiple CI runs.
- **Actual pytest run output for Sprint 2 tests** — Tests were not executed in this audit pass. Coverage numbers and pass/fail assertions are inferred from reading test bodies.

---

## Test landscape

| Dimension | Observation |
|---|---|
| Framework(s) | pytest 8.x; pytest-cov; no test retries configured |
| Test pyramid shape | Heavy unit, moderate integration (mock-LLM), thin live (gated to v0.X.0 releases) |
| Coverage tool | pytest-cov (configured in pyproject.toml) |
| Reported coverage (if any) | Not run in this audit; prior sprint reported ~87% line coverage |
| Flakiness posture | Appears clean — no retry config, no sleep-based waiting in Sprint 2 tests |
| CI blocking? | Yes — integration tests in `tests/integration/` gate on env var `RUN_INTEGRATION_TESTS` |

---

## Findings

> **Finding ID prefix:** `TEST-`
> **Categories:** Coverage / Shortcut / Flakiness / Quality / Ergonomics / Mocking / Regression

---

### [TEST-S2-001] — Major — Coverage — No test verifies thin-wrapper delegation to kernel stages

**Evidence**

ENG-003 extracted shared orchestration into `agentsuite/kernel/stages/spec.py` (`kernel_spec_stage`) and `agentsuite/kernel/stages/qa.py` (`kernel_qa_stage`). Every agent now has a thin wrapper file, e.g.:

- `agentsuite/agents/founder/stages/spec.py` line 89–98: `spec_stage()` builds `_SPEC_CONFIG` and calls `kernel_spec_stage(_SPEC_CONFIG, state, ctx)` — one line.
- `agentsuite/agents/founder/stages/qa.py` line 34–44: same pattern with `kernel_qa_stage`.

Glob confirmed 14 such thin-wrapper files across 7 agents × 2 kernel stages (spec + qa). There is no test in `tests/unit/kernel/` or any agent test file that calls a thin wrapper and asserts it correctly invokes the kernel stage. The new `tests/unit/kernel/test_stages_spec.py` (ENG-004) tests `check_path_confinement` in isolation but does not test `kernel_spec_stage` execution at all.

A grep for `kernel_spec_stage` and `kernel_qa_stage` across `tests/` returns zero results.

**Why this matters**

A developer could refactor the config dict keys (e.g. rename `consistency_system_msg`) in the wrapper's `SpecStageConfig` without touching `kernel_spec_stage`. The kernel would silently receive an invalid config and produce wrong output or raise an unhelpful error. Since the 14 wrappers all follow the same "build config, call kernel" pattern, a single bug in how any agent builds its config would ship undetected as long as the kernel's own unit tests pass.

**Blast radius**
- Adjacent code: All 14 thin-wrapper files (`agentsuite/agents/*/stages/spec.py` and `agentsuite/agents/*/stages/qa.py`). A config-construction bug in any one of them has no test coverage.
- Shared state: `SpecStageConfig` and `QAStageConfig` dataclasses in `kernel/stages/spec.py` and `kernel/stages/qa.py`. If a field is renamed or a new required field added, all 7 agent configs are silently wrong until runtime.
- User-facing: Every agent run that reaches the spec or qa stage would fail or produce garbage output.
- Tests to update: None to update — the gap is that tests do not yet exist. The fix is to add at minimum one per-kernel smoke test that exercises the config path with a mock LLM and asserts on output (e.g., a `spec_stage` call that writes artifacts and verifies they're present, a `qa_stage` call that produces a passing QAReport).
- Related findings: None directly, but see also TEST-S2-004 (path confinement gap).

**Fix path**

Add `tests/unit/kernel/test_stages_spec_kernel.py` and `tests/unit/kernel/test_stages_qa_kernel.py`. Each should exercise `kernel_spec_stage` / `kernel_qa_stage` directly through a simple `SpecStageConfig` / `QAStageConfig` built inline, using `SequentialMockLLMProvider`. Assert on artifacts written to `tmp_path` and on the returned `RunState.stage`. Optionally, add a smoke test for one agent wrapper (e.g. `founder/stages/spec.py`) to verify the delegation chain.

---

### [TEST-S2-002] — Major — Coverage — Revision cycle tests use a fragile keyword key that couples to the LLM system message string

**Evidence**

`tests/unit/test_revision_cycle.py` lines 71–74 set the SequentialMockLLMProvider QA key as:

```python
"You are scoring 9 founder-agent artifacts. Return ONLY JSON.": [
    _FAILING_QA_RESPONSE,
    _PASSING_QA_RESPONSE,
],
```

This is the full `system_msg` string from `agentsuite/agents/founder/stages/qa.py` line 28. The test comment says: "Key must match system_msg fragment 'scoring 9 founder' (longest-match-first)." However, the key is the *entire* system message, not a fragment — it will only match if `SequentialMockLLMProvider` searches both prompt AND system fields, and only if that exact string still appears verbatim in `qa.py`.

The test passes because `SequentialMockLLMProvider.complete()` searches both `request.prompt` and `request.system` (verified at test_mock.py line 177–182), and the QA stage passes this string as `system=config.system_msg`. If a developer changes the `system_msg` string in `qa.py` (e.g. changing "9 founder-agent" to "9 founder") the revision cycle tests will fail with a non-obvious `NoMockResponseConfigured` error rather than a test failure that names the cause.

**Why this matters**

The revision cycle tests are the highest-value integration tests in the Sprint 2 additions. If they break on a routine prompt-text tweak, they'll be tagged as "fragile infrastructure" and ignored rather than fixed. A test that breaks on cosmetic changes to production prompts is a friction cost against iterating on those prompts.

**Blast radius**
- Adjacent code: `agentsuite/agents/founder/stages/qa.py` (the `system_msg` constant). Any future change to that string silently breaks 7 revision cycle tests.
- Tests to update: All 7 tests in `tests/unit/test_revision_cycle.py` share `_build_sequences()`, so the fix is in one place.
- Related findings: TEST-S2-003 (checking that test helpers are not too brittle overall).

**Fix path**

In `_build_sequences()`, import the `_QA_CONFIG.system_msg` constant directly from `agentsuite.agents.founder.stages.qa` rather than duplicating the string. The key then stays in sync automatically:

```python
from agentsuite.agents.founder.stages.qa import _QA_CONFIG as _FOUNDER_QA_CONFIG
sequences[_FOUNDER_QA_CONFIG.system_msg] = [_FAILING_QA_RESPONSE, _PASSING_QA_RESPONSE]
```

This also documents the coupling explicitly rather than burying it in a comment.

---

### [TEST-S2-003] — Minor — Coverage — Path confinement tests omit symlink traversal

**Evidence**

`tests/unit/kernel/test_stages_spec.py` covers 5 scenarios: path inside project (line 11–17), path at project root (line 20–25), path outside project (line 27–40), dotdot traversal (line 42–54), and error message content (line 57–69).

`check_path_confinement` in `kernel/stages/spec.py` lines 55–60 uses `path.resolve()` then `is_relative_to()`. `Path.resolve()` follows symlinks before resolving. A symlink inside the project directory pointing outside would be resolved to the real absolute path outside the project and should be caught. However, there is no test that creates a symlink inside the project dir that points to a file outside the project dir and verifies the check raises. This scenario is the most realistic real-world traversal attack (an attacker supplies a path to a symlink rather than a raw `..` sequence).

**Why this matters**

The code likely handles it correctly (`.resolve()` dereferences symlinks before the `is_relative_to` check), but "likely" is not the same as "tested." Without a symlink test, a platform-specific quirk (e.g. Windows Junction points, which `.resolve()` sometimes does not dereference in older Python versions) could go unnoticed.

**Blast radius**
- Adjacent code: `check_path_confinement` is called from any agent spec stage that reads `manifest["sources"]` or `inp.founder_voice_samples`. A bypass would let an attacker exfiltrate any file the AgentSuite process can read.
- Tests to update: `tests/unit/kernel/test_stages_spec.py` — add one test using `tmp_path.joinpath("link_to_outside").symlink_to(outside_file)`.

**Fix path**

Add a single test case to `test_stages_spec.py`:

```python
@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation requires admin on Windows")
def test_path_confinement_rejects_symlink_pointing_outside(tmp_path: Path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    outside = tmp_path / "secret.txt"
    outside.touch()
    symlink = project_dir / "link"
    symlink.symlink_to(outside)
    with pytest.raises(ValueError):
        check_path_confinement(symlink, project_dir)
```

---

### [TEST-S2-004] — Minor — Coverage — MCP tools for engineering and marketing lack parametrized traversal tests that trust_risk and cio have

**Evidence**

`tests/unit/agents/trust_risk/test_mcp_tools.py` lines 290–305 and `tests/unit/agents/cio/test_mcp_tools.py` lines 190–205 include `@pytest.mark.parametrize` over 7 malicious `artifact_name` variants.

`tests/unit/agents/engineering/test_mcp_tools.py` and `tests/unit/agents/marketing/test_mcp_tools.py` do not expose a `get_artifact` tool (engineering and marketing agents use a simpler tool surface that does not include artifact-by-name retrieval), so the traversal parametrize tests would not apply to these files.

However, the `engineering_approve` and `marketing_approve` tools accept `run_id` as a string parameter and construct paths from it (`_output_root() / "runs" / run_id`). There is no test for a traversal attempt via `run_id` (e.g. `run_id = "../../etc"`) in either file.

**Why this matters**

`run_id` path traversal is a different attack surface from `artifact_name` traversal. The `run_id` path is used to locate the state file, and a traversal could cause `StateStore` to read from outside the runs directory. This depends on whether `validate_run_id` or equivalent sanitization is in place upstream.

**Blast radius**
- Adjacent code: `agentsuite/kernel/identifiers.py` (if `validate_run_id` sanitizes run_ids — check this). `base_agent.py` `resume()` uses `validate_run_id`. CLI `_make_approve_fn` does not appear to validate run_id before constructing the path.
- Tests to update: `tests/unit/agents/engineering/test_mcp_tools.py` and `tests/unit/agents/marketing/test_mcp_tools.py`.
- Related findings: Tracked in the engineering deep-dive as ENG-001 coverage for run_id.

**Fix path**

Add one test to each of the engineering and marketing mcp_tools test files verifying that passing `run_id="../../etc"` to `approve` returns an error dict rather than attempting to read from an out-of-bounds path. If `validate_run_id` already rejects this, the test is a quick green confirmation. If it does not, this surfaces a real bug.

---

### [TEST-S2-005] — Minor — Coverage — No test for cost suppression (AGENTSUITE_QUIET) via the full pipeline driver path

**Evidence**

`tests/test_cli_progress.py` lines 75–79 test that `_emit_stage_progress()` produces no output when `AGENTSUITE_QUIET=1`. `tests/unit/kernel/test_base_agent.py` lines 163–177 also test `_emit_stage_progress()` directly.

However, there is no test that exercises the full `_drive()` loop in `base_agent.py` (lines 164–208) with `AGENTSUITE_QUIET=1` set and asserts that the pipeline completes without writing any stage-progress lines to stderr. The `_emit_stage_progress` path inside `_drive()` is invoked via line 194: `_emit_stage_progress(stage, time.monotonic() - stage_start, state.cost_so_far.usd)`. The unit tests for `_emit_stage_progress` test the function directly; they do not verify it is wired correctly into the pipeline driver.

This is a "static ≠ runtime" gap: the unit tests verify the function, but the integration path through `_drive()` is not tested.

**Why this matters**

If a developer moves the `_emit_stage_progress` call inside the `_drive()` loop to a different position (e.g., inside the `try` block before the state save), or accidentally removes it, the unit test passes but the UX regresses — operators see a silent pipeline again.

**Fix path**

Add one test to `tests/unit/kernel/test_base_agent.py` that runs `_CostlyAgent` (already defined at line 194) with `AGENTSUITE_QUIET` unset, captures stderr, and asserts that `[OK]` appears at least once in the output. Then run the same agent with `AGENTSUITE_QUIET=1` and assert no `[OK]` lines appear. This wires the quiet-suppression test to the actual pipeline driver, not just the standalone function.

---

### [TEST-S2-006] — Nit — Quality — SequentialMockLLMProvider test names use "sequential" prefix inconsistently

**Evidence**

`tests/unit/llm/test_mock.py` test names mix formats:
- `test_sequential_returns_responses_in_order` (line 62) — uses `test_sequential_*` prefix
- `test_sequential_last_item_repeated_indefinitely` (line 72) — same
- `test_sequential_class_default_name` (line 239) — same

But `test_sequential_single_item_sequence_always_repeats` (line 83) uses `_sequence_` as a mid-word noun rather than a subject qualifier, while others use `sequential` as a subject qualifier. This is minor and cosmetic, but in a 25-test file the naming convention is slightly inconsistent.

**Fix path**

Optional: normalize to `test_sequential_*` across all 25 tests. Not worth a standalone PR; address in a naming cleanup pass.

---

### [TEST-S2-007] — Nit — Quality — Revision cycle cost accumulation test uses a loose assertion

**Evidence**

`tests/unit/test_revision_cycle.py` lines 203–207 assert `two_leg_tokens > one_leg_tokens` with a failure message. This is correct but does not pin a *minimum* expected difference. If a regression causes only a few tokens to accumulate across the second leg (e.g. only one stage is re-run instead of all stages from qa onward), the test would still pass even though the accumulation is far less than expected.

**Why this matters**

This is a low-severity quality issue: the test proves some accumulation occurs but not that the right stages ran. However, for a regression-detection standpoint, a tighter assertion (e.g. asserting that `two_leg_tokens >= one_leg_tokens + min_expected`) would catch a partial-resume bug.

**Fix path**

Optional: compute the expected minimum token addition based on the mock provider's output_tokens-from-word-count formula applied to `_PASSING_QA_RESPONSE`, and add `assert two_leg_tokens >= one_leg_tokens + expected_min`. Alternatively, assert on the stage count directly if the state exposes it.

---

## Shortcut census

| Shortcut pattern | Count (Sprint 2 files only) |
|---|---|
| `.skip` / `xit` / `@pytest.mark.skip` | 0 |
| `.only` (left in) | 0 |
| `TODO: add test` / similar | 0 |
| Empty assertion / placeholder | 0 |
| `--retry` / retries normalized | No |

No shortcuts found in any Sprint 2 test file. The existing `skipif` patterns in integration tests are gated on `RUN_INTEGRATION_TESTS` and `SKIP_IF_MOCK`, which is consistent with the project's established pattern (not a shortcut).

---

## Blind spots by class

**Kernel stage delegation** — The 14 thin-wrapper spec/qa files have no test that verifies the delegation chain. A config-construction bug would be undetectable until runtime (see TEST-S2-001).

**Symlink traversal** — `check_path_confinement` is not tested against symlinks, the most realistic vector (see TEST-S2-003).

**run_id traversal via approve** — Engineering and marketing MCP tools accept `run_id` as a free-form string; no test exercises a traversal attempt through this field (see TEST-S2-004).

**QUIET flag integration** — The `AGENTSUITE_QUIET` suppression is tested at function level but not at pipeline-driver level (see TEST-S2-005).

**Revision cycle with 3+ legs** — The revision cycle tests cover exactly two legs (fail then pass). No test exercises 3+ revision cycles or a second failure after the first resume.

**Cost cap enforcement during revision cycle** — The revision cycle tests use `usd=0.0` mock responses. There is no test that verifies `HardCapExceeded` is raised correctly when accumulated cost across two legs would exceed the cap.

---

## Patterns and systemic observations

**SequentialMockLLMProvider is a quality addition** — The TEST-002 tests are methodical without being mechanical. They cover edge cases (empty dict, single-item, caller immutability) that most teams would skip. The provider will be reliable infrastructure for future integration tests.

**Integration tests are genuinely integrating** — The TEST-004 revision cycle tests exercise the full FounderAgent pipeline including file I/O, state persistence, and approval promotion. This is harder to write than it looks and represents real regression protection.

**Copy-paste discipline in MCP tool tests is good** — The 4 MCP test files (engineering, marketing, trust_risk, cio) follow an identical structure. This consistency means a pattern bug would appear in all 4 and be caught; it also means a fix can be applied uniformly.

**Coupling between test helpers and production prompt strings** — The `_build_sequences()` function in the revision cycle tests hard-codes the exact `system_msg` string from `agentsuite/agents/founder/stages/qa.py`. This is a "mock lies" risk: if the test helper is out of date with production, the mock matches the wrong thing. See TEST-S2-002.

---

## Appendix: test artifacts reviewed

**Sprint 2 test files read in full:**
- `tests/unit/llm/test_mock.py` — 251 lines, 31 tests (6 existing + 25 new)
- `tests/unit/agents/engineering/test_mcp_tools.py` — 258 lines
- `tests/unit/agents/marketing/test_mcp_tools.py` — 250 lines
- `tests/unit/agents/trust_risk/test_mcp_tools.py` — 322 lines
- `tests/unit/agents/cio/test_mcp_tools.py` — 321 lines
- `tests/unit/test_revision_cycle.py` — 240 lines, 7 tests
- `tests/unit/kernel/test_stages_spec.py` — 69 lines, 5 tests

**Sprint 2 code files read in full:**
- `agentsuite/kernel/stages/spec.py` — 168 lines
- `agentsuite/kernel/stages/qa.py` — 126 lines
- `agentsuite/kernel/cost.py` — 142 lines
- `agentsuite/kernel/base_agent.py` — 208 lines
- `agentsuite/cli.py` — 299 lines
- `agentsuite/llm/gemini.py` — 61 lines
- `agentsuite/agents/founder/agent.py` — 123 lines

**Cross-referenced test files (for existing coverage assessment):**
- `tests/unit/kernel/test_cost.py` (lines 190–217 for QA-003)
- `tests/unit/llm/test_gemini.py` (lines 63–101 for QA-004)
- `tests/unit/test_cli.py` (lines 422–461 for ENG-002 and QA-005)
- `tests/unit/kernel/test_base_agent.py` (lines 160–241 for ENG-005)
- `tests/test_cli_progress.py` (for AGENTSUITE_QUIET)
- `agentsuite/agents/founder/stages/spec.py` and `qa.py` (thin wrapper verification)
