# Test Engineering Deep-Dive — AgentSuite

**Auditor:** Test Engineer  
**Date:** 2026-04-27  
**Scope:** Full test suite — unit, integration, golden, cleanroom, coverage gaps, quality, known failures

---

## Executive Summary

AgentSuite's test suite is **healthy and professionally structured**. 551 tests collect and all 551 pass in 14.85 seconds with zero failures. The suite has three distinct tiers (unit, integration, golden) backed by a dedicated cleanroom smoke test and a live tier gated to v0.X.0 releases. No `pytest.mark.skip` markers exist in the non-cleanroom suite. Foundational kernel tests (artifacts, cost, QA, state store, base agent) are thorough and test real behaviors with sharp assertions.

The main weaknesses are **assertion shallowness in golden tests** (most assert non-empty rather than content), **CLI coverage frozen at 2 of 7 agents** (founder + design only), **MCP tool dispatch never exercises actual tool calls** (only registration), **QA pass/fail boundary is untested at exact-threshold**, and **4 of 7 agents missing a consistency-check failure test** (only marketing has it). These are regression risks, not current failures.

**Overall verdict: Good foundation. Gaps are concentrated in contract-enforcement and integration-depth layers, not in the happy-path unit layer.**

---

## Test Inventory

**Total collected: 551 tests** (3 deselected — the `cleanroom` marker tests excluded by default)

| Directory | Count | Description |
|---|---|---|
| `tests/unit/agents/` | ~320 | Per-agent stage unit tests (7 agents × ~46 tests each) |
| `tests/unit/kernel/` | 37 | ArtifactWriter, CostTracker, QARubric, StateStore, BaseAgent, schema |
| `tests/unit/llm/` | ~60 | All 5 LLM providers + mock + pricing + resolver |
| `tests/unit/test_cli.py` | 7 | CLI subcommand tests (founder + design only) |
| `tests/unit/test_mcp_server.py` | 4 | MCP server tool registration |
| `tests/integration/` | 27 | Full pipeline runs per agent (mock LLM) |
| `tests/golden/` | 35 | Frozen fixture runs against snapshots |
| `tests/test_cleanroom_smoke.py` | 1 | Marker-gated (`-m cleanroom`), deselected by default |
| `tests/live/` | 2 | Fully gated (`RUN_LIVE_TESTS=1`), deselected by default |

**By agent (unit files):**

| Agent | Unit test files | Integration test | Golden test |
|---|---|---|---|
| founder | 12 files (agent, stages/×5, input_schema, rubric, mcp_tools, prompt_loader, template_loader) | yes | yes |
| design | 11 files | yes | yes |
| product | 10 files | yes | yes |
| engineering | 9 files | yes | yes |
| marketing | 10 files | yes | yes |
| trust_risk | 11 files | yes | yes |
| cio | 9 files | yes | yes |

---

## What's Working Well

1. **Zero test failures, zero skips.** The entire collectable suite is green. Hard Rule 4a (no skip markers) is respected — the one conditional `skipif` in the cleanroom test is a proper environment gate (bash availability), not a skip of the test logic.

2. **Kernel unit tests are thorough and sharp.** `test_cost.py` covers accumulation, soft-warn flag, hard-cap raise, no-mutation-on-overflow, and zero-cost (Ollama) paths. `test_artifacts.py` covers creation, SHA stability, overwrite idempotence, subdirectories, and promotion. `test_qa.py` tests pass/fail threshold, unknown dimension rejection, missing dimension rejection, and markdown rendering. `test_state_store.py` covers round-trip serialization, overwrite, and missing-file-returns-None. `test_base_agent.py` tests the full stage-dispatch loop, artifact writes, resume, and approve paths.

3. **MockLLMProvider is well-designed.** Keyword-based dispatch, call recording for assertion, name override, and a `_default_mock_for_cli()` factory that gives every agent realistic canned responses. The `test_mock.py` suite covers all provider behaviors including the `NoMockResponseConfigured` exception path.

4. **Integration tests run full pipelines end-to-end.** All 7 agents have a corresponding `test_{agent}_pipeline.py` that exercises intake → extract → spec → execute → qa → approval → kernel promotion with MockLLMProvider. Marketing additionally covers parse-error fallback and ConsistencyCheckFailed.

5. **LLM resolver and pricing tables are well-tested.** Resolver auto-detection, environment variable override, Ollama daemon-down error, unknown provider name, and all 4 providers (Anthropic, OpenAI, Gemini, Ollama) have dedicated coverage. Pricing table completeness is asserted for each provider.

6. **vcr.py cassette infrastructure is scaffolded.** The `conftest.py` in `tests/integration/` is ready for real-provider cassette recording via `RECORD_CASSETTES=1`, even though cassettes aren't yet recorded.

---

## Findings

### Blockers (active failures)

**None.** All 551 collectable tests pass.

---

### Critical (missing critical coverage)

**C-1: MCP tool dispatch is untested — only registration is verified.**  
`tests/unit/test_mcp_server.py` asserts that `build_server()` registers the correct tool names and respects `AGENTSUITE_EXPOSE_STAGES`. It never calls any tool handler (e.g., `founder_run`, `founder_approve`, `agentsuite_cost_report`). If a tool handler raises an unhandled exception, crashes on bad input, or returns a wrong schema, no test catches it.  
**Risk:** MCP is the primary integration surface for Codex/Claude Code consumers. A broken tool handler would silently fail in production.

**C-2: CLI coverage frozen at 2 of 7 agents.**  
`test_cli.py` covers `founder run`, `founder approve`, `design run`, `design approve`, and `list-runs`. The 5 remaining agents (product, engineering, marketing, trust_risk, cio) have no CLI test at all. If any of their CLI subcommands fail to register, crash on required flags, or emit wrong output, no test catches it.  
**Risk:** A CLI regression on any of the 5 uncovered agents goes undetected until a user hits it.

**C-3: QA pass/fail exact-boundary untested.**  
`test_qa.py` tests scores clearly above threshold (7.75 > 7.0) and clearly below (5.5 < 7.0) but never at the exact threshold (7.0 == 7.0). The boundary condition (`>=` vs `>`) in `QARubric.score()` is unverified. A 7.0-average run may pass or fail depending on the comparison operator, and no test would catch a flip.  
**Risk:** Silent mis-classification at the boundary could cause runs to stall in revision loops or skip required QA retries.

---

### Major (regression risk)

**M-1: ConsistencyCheckFailed path tested only for marketing.**  
5 of 7 agents with a consistency check stage (founder, design, product, engineering, trust_risk) have no test that forces a critical consistency finding and asserts `ConsistencyCheckFailed` is raised. Only `test_marketing_pipeline.py` has `test_marketing_consistency_check_failure_raises`. If the exception path is broken in any other agent, the pipeline would silently swallow the critical finding and continue to approval.

**M-2: Golden tests assert existence and non-emptiness, not content.**  
The golden tier was designed to catch regressions against frozen fixtures. In practice, most golden tests assert only that files exist and `len(body) > 0`. The comment in `test_golden_critical_phrase_blocklist_in_brief_templates` explicitly defers real content validation to the live tier. Since the live tier only runs at v0.X.0 releases, regressions to artifact *content structure* (section headings, required keys in JSON outputs) can slip through the entire non-live test pyramid undetected.

**M-3: RunState serialization round-trip is shallow.**  
`test_state_store.py` asserts `loaded.run_id` and `loaded.stage` after a round-trip, but does not assert that nested fields (`inputs`, `cost_so_far`, `artifacts`) survive deserialization correctly. If Pydantic serialization of `AgentRequest` subclasses drops subclass-specific fields (e.g., `organization_name` for CIOAgentInput), the test would pass while a real resume would fail.

**M-4: `_wrap()` dict branch tested only for CIO and design/founder.**  
The resume path where `state.inputs` is a base `AgentRequest` and `edits["inputs"]` is a dict is critical for all 7 agents. Based on the file list, CIO has an explicit `test_wrap_with_dict_input` and `test_wrap_with_schema_input`. Whether the 6 remaining agents have equivalent coverage is unclear from file names alone. If any agent's `_wrap()` silently passes through a base `AgentRequest` instead of the typed subclass, resume operations will drop agent-specific fields.

**M-5: ArtifactWriter `promote()` does not test subdirectory preservation.**  
`test_artifacts.py::test_promote_copies_to_kernel_dir` only checks that `brand-system.md` ends up in `_kernel/patentforgelocal/`. It does not verify that the `brief-template-library/` subdirectory structure is preserved during promotion. The integration and agent-level tests cover this indirectly, but the unit test for `ArtifactWriter` leaves this behavioral guarantee unverified at the unit level.

**M-6: HardCapExceeded during a pipeline run is untested.**  
`test_cost.py` verifies that `CostTracker.add()` raises `HardCapExceeded`. But no integration or agent unit test verifies that this exception propagates cleanly through the pipeline's stage loop (i.e., that it's not silently caught, that it produces a meaningful error, and that the run state is left in a recoverable condition). A poorly placed `except Exception` anywhere in the stage dispatch loop could swallow it.

---

### Minor

**m-1: Integration tests for CIO and trust_risk check QA scores above threshold but don't assert specific score values.**  
`test_cio_qa_scores_above_threshold` and `test_trust_risk_qa_scores_above_threshold` verify `score >= 7.0` for all dimensions. This is correct, but it also passes if all scores are 8.0 (the mock default). The tests would not catch a regression where a score falls to 6.9 under certain mock configurations.

**m-2: `test_marketing_extract_parse_error_fallback` uses a prompt-substring key that could silently stop matching.**  
The test patches `responses` using a hardcoded prompt substring: `"You are extracting structured marketing context..."`. If the extract prompt changes wording, `MockLLMProvider`'s keyword dispatch will fall through to the generic `"extracting"` key (which was explicitly removed in the patch), causing `NoMockResponseConfigured` — but the test would fail with a confusing error rather than a clear signal that the prompt key drifted.

**m-3: `test_cleanroom_smoke.py` has a `skipif` on bash availability.**  
On Windows without Git Bash or WSL, this test is silently deselected (the `skipif` condition). Since AgentSuite's primary dev platform is Windows (per the working directory), the cleanroom test may never actually run in the main dev loop. The CLAUDE.md says to use `pytest -m cleanroom` explicitly, but CI configuration was not reviewed.

**m-4: `test_founder_agent_resume_from_qa` uses an empty `edits={}` dict.**  
The resume test passes `edits={}` which means the `_wrap()` dict branch is not exercised here. The test only proves the stage-dispatch loop runs; it does not prove that a real resume (with `edits["inputs"]` from a serialized state) reconstructs the typed input correctly.

**m-5: StateStore does not test load of a corrupted/malformed JSON file.**  
If `_state.json` is written partially (e.g., crash mid-write), `StateStore.load()` would raise a JSON decode error. No test covers this. A partial write is a real-world failure mode when a process is killed during a long pipeline run.

---

### Nits

**n-1: `tests/integration/conftest.py` cassette fixture is unused.**  
The `cassette` fixture is defined but no integration test uses it. All integration tests use `_default_mock_for_cli()` directly. The fixture is dead code until real-provider cassettes are recorded.

**n-2: Test helper `_all_responses()` in `test_agent.py` (founder) is not shared across agent test files.**  
Each agent's `test_agent.py` defines its own local mock response dict. Extracting this to a shared conftest fixture would reduce duplication and make it easier to keep mocks in sync when prompts change.

**n-3: Some integration test `run_id` strings are reused across tests in the same file without isolation.**  
Most tests use `tmp_path` (so isolation is guaranteed), but the pattern of hardcoded `run_id="integration-r1"` across multiple test functions within the same file could cause confusion when reading failure output.

**n-4: No `__init__.py` in `tests/unit/agents/trust_risk/` or `tests/unit/agents/engineering/` (verify).**  
The directory listing shows `__init__.py` at the `tests/unit/agents/` level but per-agent `__init__.py` files were not explicitly verified for all agents. Missing `__init__.py` files can cause import collisions in some pytest configurations.

---

## Coverage Matrix

| Agent | Unit tests | Integration test | _wrap tested | Registration tested | ConsistencyCheck failure tested | Gap |
|---|---|---|---|---|---|---|
| founder | Yes — 12 files | Yes | Indirect (resume test) | Yes | No | ConsistencyCheck failure |
| design | Yes — 11 files | Yes | Yes (mcp_tools) | Yes | No | ConsistencyCheck failure |
| product | Yes — 10 files | Yes | Indirect | Yes | No | ConsistencyCheck failure |
| engineering | Yes — 9 files | Yes | Indirect | Yes | No | ConsistencyCheck failure |
| marketing | Yes — 10 files | Yes | Yes (resume test) | Yes | **Yes** | None critical |
| trust_risk | Yes — 11 files | Yes | Indirect | Yes | No | ConsistencyCheck failure |
| cio | Yes — 9 files | Yes | **Yes — explicit** | Yes | No | ConsistencyCheck failure |

| Kernel component | Unit coverage | Gap |
|---|---|---|
| ArtifactWriter | Good | subdirectory promotion not unit-tested |
| CostTracker | Good | pipeline propagation of HardCapExceeded untested |
| QARubric | Good | exact-threshold boundary untested |
| StateStore | Good | corrupted JSON not tested |
| BaseAgent | Good | None |

| Surface | Coverage | Gap |
|---|---|---|
| CLI | 2 of 7 agents | product, engineering, marketing, trust_risk, cio |
| MCP tools | Registration only | Tool handler dispatch never exercised |
| MockLLMProvider | Comprehensive | None |
| LLM resolver | Comprehensive | None |
| Pricing tables | Comprehensive | None |
| Golden fixtures | All 7 agents | Content assertions deferred to live tier |
| Cleanroom | Exists | May not run on Windows without bash |

---

## Known Failures

**None.** All 551 collectable tests pass as of 2026-04-27.

```
551 passed, 3 deselected, 1 warning in 14.85s
```

The 1 warning is a `DeprecationWarning` in `google.genai.types` about `_UnionGenericAlias` being deprecated and slated for removal in Python 3.17. This is in the Gemini SDK, not AgentSuite code. Not a test failure, but a future compatibility risk.

---

## Blind Spots

These behaviors have **zero test coverage** in the collectable suite:

1. **MCP tool handler execution.** `founder_run`, `founder_approve`, `agentsuite_cost_report`, and all other registered tool handlers are never called from a test. The entire MCP dispatch layer — argument validation, error wrapping, output serialization — is untested.

2. **ConsistencyCheckFailed propagation in 6 of 7 agents.** Only marketing tests this exception path. If any other agent's consistency check stage silently catches or ignores a critical finding, no test would detect it.

3. **QA pass/fail boundary at exactly 7.0 average.** The exact-threshold comparison operator is unverified. A score of 7.0 == threshold could be a pass or fail depending on `>=` vs `>`, and no test pins this behavior.

4. **HardCapExceeded propagation through the stage loop.** The exception raises from `CostTracker.add()`, but nothing tests that the pipeline's stage dispatch loop lets it propagate rather than catching it.

5. **StateStore corrupted/partial JSON recovery.** Real-world crash-during-write scenarios are not tested.

6. **CLI subcommands for 5 agents** (product, engineering, marketing, trust_risk, cio). Required flags, help text, exit codes, and output format for these agents are entirely untested via CLI.

7. **Artifact content structure.** Golden tests assert non-emptiness; no test asserts that JSON artifacts (`qa_scores.json`, `consistency_report.json`, `extracted_context.json`) contain the expected top-level keys. A structural regression (e.g., key rename) would be invisible until a live run.

8. **Resume with actual serialized-then-deserialized state.** All resume tests pass the original typed input object through `edits`. No test exercises the realistic path where `state.inputs` is loaded from disk as a base `AgentRequest` JSON blob and `edits["inputs"]` is a plain dict from a real resume scenario.

9. **Multi-run cost accumulation across a full pipeline.** `test_cost.py` tests `CostTracker` in isolation. No test asserts the total cost accumulated across all LLM calls in a complete agent run matches the sum of individual stage costs.

10. **`agentsuite_kernel_artifacts` MCP tool output.** The tool is registered but its output (list of promoted artifact paths) is never verified against actual kernel directory contents.

---

## Recommendations (priority order)

1. **Add MCP tool handler dispatch tests** — call `founder_run`, `founder_approve`, `agentsuite_cost_report` via the server's tool interface and assert on return values. (Critical C-1)

2. **Add CLI tests for remaining 5 agents** — at minimum: `run --help` exits 0 and lists required flags; `run` with mock LLM exits 0 and emits `awaiting_approval`. (Critical C-2)

3. **Add exact-threshold QA boundary test** — `r.score({"a": 7.0}, [])` should assert `passed is True` (or False, pinning the actual behavior). (Critical C-3)

4. **Add ConsistencyCheckFailed tests to 6 remaining agents** — copy the marketing pattern into each agent's integration test. (Major M-1)

5. **Add golden content-structure assertions** — assert that `qa_scores.json` has a `scores` key, `extracted_context.json` has the expected top-level fields, etc. (Major M-2)

6. **Add HardCapExceeded pipeline propagation test** — integration test with a CostCap of $0.001 that forces HardCapExceeded mid-pipeline and asserts it surfaces cleanly. (Major M-6)
