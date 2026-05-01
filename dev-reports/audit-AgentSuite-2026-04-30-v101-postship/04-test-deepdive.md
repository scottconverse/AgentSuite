# Test Suite Deep-Dive — AgentSuite v1.0.1

**Audit date:** 2026-04-30
**Role:** Test Engineer
**Scope audited:** `tests/unit/` (94 files), `tests/integration/` (10 files), `tests/golden/` (7 files), `tests/live/` (2 files), `tests/test_*.py` (5 root-level), `tests/integration/cassettes/` (0 files), `tests/golden/snapshots/` (7 agents × 3–4 fixtures each). CI: `.github/workflows/test.yml`, `.github/workflows/lint.yml`, `.github/workflows/provider-drift.yml`. Configuration: `pyproject.toml`, `CONTRIBUTING.md`, `docs/test-coverage.md`.
**Auditor posture:** Balanced

---

## TL;DR

AgentSuite has a well-structured, heavily unit-weighted test pyramid (94 unit files, 10 integration, 7 golden, 2 live) with disciplined tooling: no unconditional skips, a purpose-built mock LLM with longest-match semantics (fixed this sprint per TEST-003), and a three-tier gating system (mock / live-cassette-planned / actual-live) that is honest about what it covers. The main structural issue is that the "integration" tier is a mock-LLM unit test in disguise — no real HTTP traffic has ever been recorded against the cassette infrastructure the conftest.py and 11 `skipif` decorators are scaffolded for. The live tier (gated behind `RUN_LIVE_TESTS=1`) is the only place real LLM behavior is tested, and it covers only one agent (Founder). The class of bug most likely to slip through: behavioral regression in how the real LLM response shapes propagate through the extraction pipeline — because every integration test substitutes a keyword-matched stub for the real LLM response, and the golden tests only assert mock output against mock-captured snapshots.

---

## Severity roll-up (tests)

| Severity | Count |
|---|---|
| Blocker  | 0 |
| Critical | 1 |
| Major    | 4 |
| Minor    | 3 |
| Nit      | 2 |

---

## What's working

- **No unconditional skips — zero.** The repo enforces Hard Rule 4a at the documentation level (`CONTRIBUTING.md` line 32, `docs/test-coverage.md`) and backs it up in code. `grep -rn "@pytest.mark.skip\b"` returns nothing. The three deselected marker-gated tests (cleanroom, live, live_ollama) are collected but excluded by pyproject `addopts`; they are not skips. This is the correct pattern.

- **MockLLMProvider longest-match fix is pinned with a regression test.** `tests/unit/llm/test_mock_matcher.py` was added this sprint (TEST-003) to enforce the longest-keyword-wins semantics. The fix and the test arrived in the same commit. This is exactly the regression-test-after-bug-fix culture the test suite should have. The docstring names the audit finding that prompted the fix.

- **Resume idempotency is tested end-to-end with a custom crash-and-recover mock.** `tests/integration/test_resume_idempotency.py` uses `_BillableThenCrashThenSucceed` to simulate a transient failure mid-pipeline, then resumes and asserts that prior-stage costs are not double-billed. This is the most sophisticated test in the suite and directly pins ADR-0007.

- **Golden snapshot tier covers all seven agents.** Every agent has a committed primary-artifact snapshot (`brand-system.md`, `it-strategy.md`, etc.) and a QA-scores snapshot that is checked both byte-for-byte (markdown) and within tolerance (numeric averages). The `assert_artifact_exact` / `assert_qa_within_tolerance` helper split — tolerating floats but not text — is thoughtful and prevents test-helper misuse.

- **Drift traps gate on doc content, not just code.** `test_mcp_tool_names_documented.py` and `test_readme_cli_invocations.py` parse the live Typer CLI and live MCP server registration, then assert that every tool name or `--flag` documented in prose also exists in the live implementation. These are the right class of test to catch CR-04-style regressions before users hit them.

- **Downstream consumer type-check is an integration test, not a manual step.** `test_downstream_consumer.py` synthesizes a real consumer package, runs mypy against it with `--strict`, and fails CI if the public surface stops type-checking cleanly. This is an uncommon and valuable gate.

- **CI matrix covers Python 3.11 and 3.12.** The `test.yml` matrix runs both versions. Version-specific float ordering changes are covered by `rtol=0.05` in `assert_qa_within_tolerance`, which the audit notes as explicitly justified.

- **Error paths covered with real fixture manipulation.** ConsistencyCheckFailed is triggered across every agent's integration test by patching `MockLLMProvider.responses` to insert a critical-severity mismatch JSON. `HardCapExceeded` is propagated through the full pipeline in a separate test. These test error behavior that traverses real code paths, not test-only escape hatches.

---

## What couldn't be assessed

- **CI run history and flakiness.** I cannot query GitHub Actions run history to see whether any tests have failed intermittently. Flakiness patterns (tests that pass 95% of the time) are invisible from source alone.

- **Actual code coverage percentage.** The CI command (`pytest ... --cov=agentsuite --cov-report=term-missing`) generates coverage but does not enforce a minimum threshold. No `.coveragerc` exists. I cannot run the suite locally to see the actual number.

- **Mock response completeness vs. actual LLM behavior.** The `_default_mock_for_cli()` function keys on keywords found in stage system prompts. I cannot verify that the keywords faithfully simulate the full range of LLM responses the real pipeline would receive, because that would require comparing against actual Anthropic / OpenAI / Gemini response shapes.

---

## Test landscape

| Dimension | Observation |
|---|---|
| Framework(s) | pytest 8+, pytest-cov 5+, vcrpy 6+ (installed but cassettes dir empty) |
| Test pyramid shape | Heavy unit (94 files, ~600 functions), thin integration (10 files, all mock), thin golden (7 files), micro live (2 files, 1 agent) |
| Coverage tool | pytest-cov installed; no minimum gate; no `.coveragerc` |
| Reported coverage | Not enforced — `--cov-report=term-missing` output not checked against a floor |
| Flakiness posture | Appears clean — no retry config, no `sleep()` calls, no time.time() in assertions |
| CI blocking? | Yes — PRs block on `unit-integration-golden`, `cleanroom`, and `wheel-smoke` jobs |

---

## Findings

### TEST-001 — Critical — Coverage — vcr cassette infrastructure is permanently scaffolded but never populated

**Evidence**

- `tests/integration/cassettes/` is empty: `ls cassettes/ | wc -l` returns 0.
- `tests/integration/conftest.py` (lines 1–26) imports `vcrpy`, defines a `cassette` fixture that resolves to a per-test `.yaml` in the empty cassettes directory, and sets `record_mode="new_episodes"` when `RECORD_CASSETTES=1`.
- Zero test functions in any integration test file accept the `cassette` fixture as a parameter. The fixture is defined, never consumed.
- Eleven `@pytest.mark.skipif(os.environ.get("RECORD_CASSETTES") == "1", reason="Skip when re-recording cassettes")` decorators appear across integration tests (`test_cio_pipeline.py:18,42,78`, `test_design_pipeline.py:17`, `test_engineering_pipeline.py:17`, `test_founder_pipeline.py:16`, `test_marketing_pipeline.py:17`, `test_product_pipeline.py:17`, `test_trust_risk_pipeline.py:18,42,78`).
- These `skipif` decorators guard the mock-LLM tests against `RECORD_CASSETTES=1`, implying a recording path is planned. But no test function exists that uses the cassette fixture, so `RECORD_CASSETTES=1` would simply deselect 11 tests and run no others.
- The `CONTRIBUTING.md` (line 34) says: "vcr.py cassettes are checked in and re-recorded only via `make rerecord-cassettes`." The cassettes have never been recorded.

**Why this matters**

The integration tests are structurally labeled as integration tests but are behaviorally unit tests. They substitute `MockLLMProvider` for the real provider — which is honest and useful — but the intent comment in `test_founder_pipeline.py:21` says "vcr cassettes are reserved for the future real-provider integration path." That future has not arrived. The 11 `skipif` decorators are dead code: they protect against a recording path that doesn't exist, while the cassette fixture is dead infrastructure.

The practical risk is not that these tests lie — they don't, they correctly test mock-LLM behavior — but that the vcr scaffolding creates the impression that a real-HTTP replay tier exists. If a maintainer adds a new integration test expecting cassette replay to work, they will get an `OSError: [Errno 2] No such file` when vcr tries to load a cassette that was never recorded, with no guidance on how to record it. The vcr `record_mode="none"` (the default when `RECORD_CASSETTES=0`) blocks network traffic and throws `CannotSendRequest` if a test does hit HTTP — this is actually a useful guard, but only if the cassette file exists first.

**Blast radius:**
- Adjacent code: `tests/integration/conftest.py`, all 11 `skipif` decorators across 7 integration test files. The `Makefile` `rerecord-cassettes` target (line 8–13) would run against the mock and produce no cassette files.
- Shared state: `vcrpy>=6.0` is a dev dependency (`pyproject.toml` line 41). It's not dead weight — it's used by the conftest — but the dependency cost is real for zero runtime value.
- User-facing: No user-facing impact from the empty cassettes. The risk is to developer-facing confidence in the integration tier label.
- Migration: Two options: (a) record cassettes against real providers at v1.0.X and commit them, converting the integration tests to true replay tests; (b) remove the cassette fixture, remove the `skipif` decorators, and rename the tests to `test_founder_pipeline_mock.py` to be honest about scope. Option (b) is cheaper and equally honest.
- Tests to update: All 11 decorated test functions; `conftest.py`.
- Related findings: TEST-002 (live coverage is single-agent only).

**Fix path**

Either commit cassettes (requires live provider access at recording time) or remove the dead scaffolding. The `skipif` decorators should be removed in the same commit as whichever choice is made. Until then, add a comment to `conftest.py` that says "cassette fixture provided for future use; no cassettes exist yet" so the next maintainer doesn't spend time debugging why replays fail.

---

### TEST-002 — Major — Coverage — Live tier covers only Founder agent; six agents have no real-LLM test

**Evidence**

- `tests/live/` contains two files: `test_founder_live.py` and `test_ollama_live.py`.
- `test_founder_live.py` runs `FounderAgent` against the live provider. Zero other agents (Design, Product, Engineering, Marketing, TrustRisk, CIO) have a live test.
- `test_ollama_live.py` (not inspected in full) runs Ollama tests — also agent-specific.
- The six remaining agents have integration coverage only via `MockLLMProvider`.

**Why this matters**

Each agent has its own prompt templates, extraction logic, and QA rubric. The real LLM's response shape for a Design brief may differ from a CIO strategy document in ways the mock never exercises. For example: if a real Gemini response for the Engineering agent's `architecture-decision-record` stage omits a field the extraction stage expects, the extraction would silently produce an empty artifact. The mock always returns the canned keyword-matched response, so this class of failure is invisible without a live test.

This is especially important post-v1.0 GA, where users of all seven agents are expected.

**Blast radius:**
- Adjacent code: `tests/live/` — adding six more live test files, one per agent.
- User-facing: A behavioral regression in any non-Founder agent's prompt parsing would not be caught until a user reports it.
- Migration: None — additive test files only.
- Related findings: TEST-001 (cassette tier that could provide replay coverage doesn't exist).

**Fix path**

Add one live test per remaining agent, following the pattern of `test_founder_live.py`. Each test needs: a per-test cost cap via `AGENTSUITE_COST_CAP_USD`, a minimal input fixture, assertion that `state.stage == "approval"`, and at least one artifact content assertion (e.g., the primary `.md` contains a markdown heading). The `$10` total-cost live cap in `CONTRIBUTING.md` should be updated to reflect seven agents running live.

---

### TEST-003 — Major — Coverage — No coverage gate on reported test count in docs

**Evidence**

- `docs/test-coverage.md` line 19: "As of 2026-04-29, that leaves **689 of 692** tests in the default run."
- `CONTRIBUTING.md` line 78: "The default `pytest` invocation runs **688 of 691** tests."
- The audit context supplied by the caller states: "AgentSuite has 782 tests passing (3 deselected by marker: cleanroom, live, live_ollama)."
- Three distinct numbers appear across three documents for the same claim, all claiming to be current as of the same date range (late April 2026).

**Why this matters**

The test-count discrepancies (688 vs 689 vs 782) show that the count documented in `docs/test-coverage.md` and `CONTRIBUTING.md` is not mechanically enforced. A reader following the CONTRIBUTING guide to set up tests would expect 691 collected, not the actual 785. More importantly, there is no CI step that compares the collected count to the documented count. When test count changes (as it did by ~90 tests between releases), the docs silently drift.

The immediate risk is low — the count itself doesn't affect correctness — but it erodes trust in the documentation's accuracy and could mislead a new contributor about the test pyramid shape.

**Blast radius:**
- Adjacent code: `docs/test-coverage.md`, `CONTRIBUTING.md`.
- Migration: None.
- Tests to update: Add a CI step that runs `pytest --collect-only -q` and checks the count against a documented floor; or scrape the count from the CI output and write it back to a generated file.

**Fix path**

Add a `make check-test-count` target or CI step: `pytest --collect-only -q 2>&1 | grep "tests collected"` and compare to the expected floor. Update `docs/test-coverage.md` and `CONTRIBUTING.md` to the correct current count (782 active + 3 deselected = 785 total collected). Consider replacing hardcoded counts with a CI-generated badge.

---

### TEST-004 — Major — Coverage — No coverage minimum gate; coverage floor is unknown and unenforced

**Evidence**

- `pyproject.toml` [tool.pytest.ini_options] has no `--cov-fail-under` directive.
- No `.coveragerc` file exists (verified: `cat .coveragerc` returns "No .coveragerc").
- `docs/test-coverage.md` line 122: "Coverage drops are not currently a hard gate; will be considered for v1.0.0-rc1."
- The v1.0.1 release ships without a coverage gate, despite the "will be considered" note landing before GA.

**Why this matters**

The test suite has 702 test functions across 118 test files. Without a coverage floor, a refactor can silently drop coverage of a kernel subsystem. The kernel's `ArtifactWriter`, `StateStore`, `CostTracker`, and `BaseAgent._drive()` are used by all seven agents; a regression introduced by removing a test of one of these would be invisible until an agent produces a wrong artifact.

This is particularly relevant for the `tests/unit/kernel/` subsystem, which covers the shared pipeline engine. Any change to these files that removes tests without a coverage gate goes undetected.

**Blast radius:**
- Adjacent code: All code in `agentsuite/kernel/`. The `agentsuite/llm/` layer is also at risk — the retry, pricing, and resolver modules are heavily abstracted.
- Shared state: Coverage data is generated per-CI run; without a floor, regressions accumulate invisibly.
- Tests to update: None existing. Add `--cov-fail-under=85` (or appropriate floor after measuring the current actual number) to pyproject `addopts` or the CI command.
- Related findings: TEST-003 (general gap between documented and actual test infrastructure state).

**Fix path**

(1) Run `pytest tests/unit tests/integration tests/golden --cov=agentsuite --cov-report=term-missing` once to see the actual current floor. (2) Set `--cov-fail-under=<floor>` in the CI command or pyproject `[tool.pytest.ini_options] addopts`. (3) Update `docs/test-coverage.md` to close the "will be considered for v1.0.0-rc1" note with the decision made. The floor should be 80% at minimum for a v1.0 library.

---

### TEST-005 — Major — Quality — SVG terminal-screenshot extractor in `test_readme_cli_invocations.py` is rich-specific and has no unit tests

**Evidence**

- `tests/test_readme_cli_invocations.py` lines 52–122: `_iter_svg_invocations()` reconstructs terminal lines from rich's `Console.save_svg()` format by matching `clip-path="url(#[^"]*?-line-(\d+))"` on `<text>` nodes.
- This is a parser written against a specific SVG internal format that rich's `save_svg()` currently emits. Rich does not guarantee this format across minor versions.
- Five SVG files exist in `docs/screenshots/`: `brand-system-rendered.svg`, `cli-founder-run.svg`, `kernel-tree.svg`, `qa-report-rendered.svg`, `runs-tree.svg`.
- Zero unit tests exist for `_iter_svg_invocations()` or its helpers (`_decode_svg_entities`, `_SVG_LINE_GROUP_RE`). The function is exercised only end-to-end, making failures hard to diagnose.
- The audit context notes TEST-104 (SVG extractor clip-path regex is rich-specific) as a known open issue.

**Why this matters**

Rich releases minor updates frequently. If rich changes the clip-path ID format from `terminal-<uuid>-line-<N>` to another scheme, `_SVG_LINE_GROUP_RE` will match nothing. The result is `_iter_svg_invocations()` silently returning an empty list, which means SVG content is not validated, which means documented CLI commands in SVGs can drift. The test `test_at_least_one_invocation_documented` would still pass (because prose blocks cover the minimum), but the SVG-specific guard would be silently dead.

The existing test includes no assertion like "SVG files must contribute at least N invocations" — the sanity check only requires the total invocation count across all sources to be > 0.

**Blast radius:**
- Adjacent code: `_iter_svg_invocations()`, `_SVG_LINE_GROUP_RE`, `_decode_svg_entities` all in `tests/test_readme_cli_invocations.py` lines 52–122. The `docs/screenshots/*.svg` files are the data sources.
- Shared state: Rich version is pinned transitively through typer; a typer upgrade could bring a rich minor bump.
- User-facing: If SVG validation silently goes dark, a renamed CLI flag in an SVG screenshot would pass CI while misleading users.
- Migration: None.
- Tests to update: Add a parametrized unit test of `_iter_svg_invocations()` with a minimal synthetic rich SVG fixture to assert the line reconstruction works correctly. Add an assertion that SVG files contribute at least 1 invocation when they exist.
- Related findings: None.

**Fix path**

(1) Add `tests/unit/scripts/test_svg_extractor.py` with a synthetic SVG string that mimics rich's `save_svg()` format and asserts `_iter_svg_invocations()` correctly extracts a known invocation. (2) Add an assertion in `test_at_least_one_invocation_documented` that `_iter_svg_invocations()` specifically returned > 0 results when `SVG_FILES` is non-empty. This pins the extractor's behavior against the currently-committed SVGs, so a rich format change fails loudly rather than silently passing.

---

### TEST-006 — Minor — Coverage — No test exercises `AGENTSUITE_OUTPUT_DIR` environment variable override

**Evidence**

- `CLAUDE.md` (AgentSuite project): "Agent output goes to `.agentsuite/` in the calling project's CWD (configurable via `AGENTSUITE_OUTPUT_DIR`)."
- `tests/unit/test_mcp_server.py` uses `AGENTSUITE_OUTPUT_DIR` for MCP server tests, but only as a monkeypatched input to `build_server()`, not as an end-to-end output-path test.
- No test verifies that when `AGENTSUITE_OUTPUT_DIR=/custom/path` is set and an agent runs, artifacts land at that path rather than the CWD default.

**Why this matters**

The output directory override is a documented user-facing configuration option. A bug in how `resolve_provider()` or `FounderAgent` resolves the output root from the environment variable would cause all output to go to the wrong location — silently, with no CI signal.

**Fix path**

Add a test in `tests/integration/test_founder_pipeline.py` (or a new `test_output_dir_override.py`) that: (1) sets `AGENTSUITE_OUTPUT_DIR` via monkeypatch, (2) runs a minimal Founder pipeline, and (3) asserts that `(Path(os.environ["AGENTSUITE_OUTPUT_DIR"]) / "runs" / run_id / "_state.json").exists()` and that the default CWD path does not receive artifacts.

---

### TEST-007 — Minor — Coverage — Input validation edge cases not tested for five of seven agents

**Evidence**

- `tests/unit/agents/founder/test_input_schema.py` covers: missing required fields (`ValidationError`), slug truncation to 40 chars, slug alphanumeric normalization, slug derivation from business_goal.
- Sampling `tests/unit/agents/cio/test_input_schema.py`, `tests/unit/agents/trust_risk/test_input_schema.py`: cover required fields and basic happy path, but not boundary conditions (empty string values, very long strings, special characters in organization names or risk domains).
- No agent's input schema tests cover: Unicode in user_request, shell-special characters in project_slug, or `None` values for optional fields that later get passed to Jinja2 templates.

**Why this matters**

A user providing a project name containing `{{ }}` (Jinja2 template syntax), a forward-slash, or a null byte could trigger a Jinja2 `TemplateError` in the execute stage — after the spec stage has already billed LLM cost. This is not a security issue (templates are not user-controlled in the attack sense) but it is an error path that produces a confusing crash rather than a clean validation error.

**Fix path**

Extend the input schema tests for each of the six non-Founder agents to include at least: (1) test with empty string for a required field, (2) test with a string containing Jinja2 metacharacters `{%`, and (3) test with a very long string (>500 chars) in the primary free-text field. The test should assert either clean `ValidationError` rejection or graceful handling downstream.

---

### TEST-008 — Minor — Coverage — `test_cleanroom_smoke.py` has a conditional `skipif` on bash availability that silently passes on Windows without testing anything

**Evidence**

- `tests/test_cleanroom_smoke.py` lines 15–19:
  ```python
  @pytest.mark.skipif(
      shutil.which("bash") is None,
      reason="bash not available; cleanroom requires bash (Git for Windows or WSL)",
  )
  def test_cleanroom_script_exits_zero():
  ```
- On Windows systems without Git for Windows or WSL, `shutil.which("bash")` returns `None`.
- The test is collected (because it has `pytestmark = pytest.mark.cleanroom`, so it's only collected when `-m cleanroom` is passed) but the inner `skipif` would skip it silently on a Windows CI runner without bash.
- The CI `cleanroom` job runs on `ubuntu-latest` only, so bash is always available in CI. The issue is local developer experience on Windows.

**Why this matters**

This is a Minor because CI is unaffected (ubuntu-latest always has bash). The risk is that a developer on Windows running `pytest -m cleanroom` locally sees a "1 skipped" result and believes the cleanroom passed, when it silently did nothing. The `reason` string is informative, but a developer who doesn't notice the skip output won't know.

**Fix path**

Add a print or warning-level log when the skip fires: e.g., wrap the `skipif` in a `pytest.fail()` alternative that prints "CLEANROOM SKIPPED — bash not available. Install Git for Windows or WSL to run cleanroom locally." This makes the skip visible. Alternatively, restructure the cleanroom to use `subprocess.run(["python", "scripts/run-cleanroom-py.py"])` so it works cross-platform.

---

### TEST-009 — Nit — Quality — vcr.py is a dev dependency that adds install cost for zero current runtime benefit

**Evidence**

- `pyproject.toml` line 41: `"vcrpy>=6.0"` in `[project.optional-dependencies].dev`.
- Cassettes dir is empty; the cassette fixture is unused.
- `vcrpy` pulls in `PyYAML`, `wrapt`, and `httpretty` as transitive dependencies. On a clean install `pip install -e .[dev]` downloads and installs all of them.

**Fix path**

If the team commits to removing the cassette scaffolding (see TEST-001 fix path option b), remove `vcrpy>=6.0` from dev dependencies in the same commit. If the team commits to using cassettes, keep it. The decision should be made explicit rather than left in limbo.

---

### TEST-010 — Nit — Ergonomics — `CONTRIBUTING.md` says 688/691 tests; `docs/test-coverage.md` says 689/692; actual is 782/785

**Evidence**

- `CONTRIBUTING.md` line 78: "688 of 691"
- `docs/test-coverage.md` line 19: "689 of 692"
- Audit context: "782 tests passing (3 deselected)"
- Both documents claim to reflect the state as of "2026-04-29" but disagree with each other and with reality.

**Fix path**

Mechanically enforce via CI as described in TEST-003. Update both docs to the correct current count as a quick patch while the mechanical gate is being built.

---

## Shortcut census

| Shortcut pattern | Count | Notes |
|---|---|---|
| `@pytest.mark.skip` (unconditional) | 0 | None found. Hard Rule 4a satisfied. |
| `pytest.skip()` calls | 0 | None found. |
| `.only` left in | 0 | N/A (pytest, not Jest) |
| `TODO: add test` / similar | 0 | None found in test files |
| Empty assertion / `assert True` | 0 | None found |
| `@pytest.mark.xfail` | 0 | None found |
| `--retry` / retries normalized | No | No retry config found |
| `@pytest.mark.skipif` (conditional) | 12 | 11x RECORD_CASSETTES (integration), 1x bash availability (cleanroom); both documented and justified |
| `pytest.importorskip` | 1 | `test_mcp_tool_names_documented.py:103` — skips MCP drift gate if `mcp` extra not installed. Legitimate. |

The shortcut culture is clean. The 11 RECORD_CASSETTES `skipif` decorators are the only pattern worth watching — they aren't wrong, but they're scaffolding for a cassette tier that doesn't yet exist (see TEST-001).

---

## Blind spots by class

**Real-LLM behavioral drift (highest risk class)**
The mock LLM returns canned responses keyed on substrings. If a real LLM returns a response that is structurally different (e.g., additional keys in the JSON, different field ordering, wrapped in markdown fences), the extraction stage could silently produce an empty or malformed artifact. This class of bug is only catchable in the live tier, which covers one agent.

**Concurrent run collisions**
No test exercises two simultaneous runs with the same `run_id` in the same `output_root`. The `StateStore.save()` uses an atomic write pattern (verified: `test_state_store_save_leaves_no_tmp_files`), but there's no test for what happens when two processes race to save to the same path. For a library that can be invoked from multiple MCP clients, this is a realistic scenario.

**`AGENTSUITE_OUTPUT_DIR` end-to-end path**
Covered in TEST-006. The env var is used but not tested end-to-end.

**Unicode and special characters in user inputs**
Covered in TEST-007. Jinja2 template rendering with user-supplied values containing metacharacters is untested.

**MCP tool error response shapes**
`test_mcp_server.py` tests that `get_status` raises `FileNotFoundError` for a missing run. It doesn't test what the MCP client sees when that error propagates through the FastMCP tool registration — whether it becomes a structured MCP error or an unhandled exception.

**Provider SDK version drift**
The `provider-drift.yml` CI workflow checks that model names still exist in the provider's `/models` endpoint weekly. It does not check that the provider SDK's API surface (e.g., `client.messages.create` kwargs) has not changed. A major SDK bump (anthropic>=1.0) could break all LLM calls without the pricing drift check catching it.

**Cost cap enforcement under concurrent agent calls**
`HardCapExceeded` propagation is tested in `test_pipeline_hard_cap_exceeded_propagates`. No test checks what happens if a cost cap is hit mid-stage while a second call is in flight (relevant if a future streaming implementation is added).

---

## Patterns and systemic observations

**Integration tier is unit in disguise.** The label "integration" implies real integration points. Every integration test uses `MockLLMProvider`. The cassette scaffolding (conftest.py, 11 skipifs, `rerecord-cassettes` Makefile target, CONTRIBUTING reference) implies a real-LLM replay tier exists or is coming. It doesn't exist yet. This is not a test quality failure — the mock integration tests are valuable — but the labeling creates a false confidence that the suite exercises real HTTP behavior. The team should make a deliberate architectural decision: either build the cassette tier or remove the scaffolding and be honest that "integration" means "full mock pipeline."

**Golden snapshots are deterministic only under the mock.** The golden snapshots pin mock output, not real LLM output. This is correct and honest (the golden tests say so explicitly in their docstrings). The risk is that the golden tier provides coverage of "the mock produces stable output" but not "the real LLM produces useful output." The live tier is meant to cover the latter, but it covers only Founder.

**Regression-test-after-bug culture is present but nascent.** The `test_mock_matcher.py` file (added this sprint per TEST-003) is a good example of the culture working. The file's docstring names the audit finding that prompted the fix. If this becomes the norm — every bug fix gets a named regression test — the suite will drift toward higher quality naturally. It's worth explicitly documenting this expectation in CONTRIBUTING.md.

**No test isolation issue with tmp_path.** All tests that write files use pytest's `tmp_path` fixture, which guarantees isolation per test function. No shared filesystem state was found. This is a consistent pattern across all 118 test files.

**Coverage measurement is passive.** `--cov-report=term-missing` prints coverage to the CI log where no one reads it. The only person who would notice a coverage regression is someone who specifically goes to look. This is the design that produces slowly-eroding coverage over months.

---

## Appendix: test artifacts reviewed

**Test directories:**
- `tests/unit/` — 94 test files, sampled: `test_base_agent.py`, `test_state_store.py`, `test_retry.py`, `test_mock.py`, `test_mock_matcher.py`, `test_anthropic.py`, `test_mcp_server.py`, `test_public_api.py`, `test_cli.py`, `agents/founder/stages/test_qa.py`, `agents/founder/test_input_schema.py`
- `tests/integration/` — 10 files, all read: `conftest.py`, `test_founder_pipeline.py`, `test_design_pipeline.py`, `test_engineering_pipeline.py`, `test_cio_pipeline.py`, `test_trust_risk_pipeline.py`, `test_resume_idempotency.py`, `test_downstream_consumer.py`, `test_sdk_usage.py`
- `tests/golden/` — all 7 test files and all committed snapshots under `tests/golden/snapshots/`
- `tests/live/test_founder_live.py`
- Root-level: `test_cleanroom_smoke.py`, `test_cli_help_unicode.py`, `test_cli_progress.py`, `test_mcp_tool_names_documented.py`, `test_readme_cli_invocations.py`

**CI config:**
- `.github/workflows/test.yml` — unit+integration+golden matrix, cleanroom, wheel-smoke
- `.github/workflows/lint.yml` — ruff, mypy, doc artifact existence, version consistency
- `.github/workflows/provider-drift.yml` — weekly model name drift check

**Project config:**
- `pyproject.toml` — pytest options, dev dependencies, marker definitions
- `CONTRIBUTING.md` — test tier documentation, cassette recording instructions
- `docs/test-coverage.md` — gating rationale, marker gate catalog
- `Makefile` — test targets, `rerecord-cassettes`, `update-goldens`
