# Test Suite Deep-Dive — AgentSuite v1.0.5

**Audit date:** 2026-04-30
**Role:** Test Engineer
**Scope audited:** `tests/unit/`, `tests/integration/`, `tests/golden/`, `tests/stress/`, `tests/live/`, `tests/test_*.py` (top-level), `.github/workflows/test.yml`, `Makefile`, `pyproject.toml`
**Auditor posture:** Balanced

---

## TL;DR

AgentSuite has a well-structured, high-quality test suite with genuine depth in the unit and stress tiers. The pyramid is heavy on unit (626+ functions), has meaningful golden snapshots for all 7 agents, and a genuinely thoughtful stress suite covering real-LLM failure modes. The main systemic issue is that the stress suite — the most valuable new addition — is **excluded from CI** (it is not listed in the `pytest tests/unit tests/integration tests/golden` CI command), meaning its 87 tests never gate a PR. The second systemic issue is that `SequentialMockLLMProvider`, shipped in `agentsuite/llm/mock.py`, has zero test coverage anywhere in the codebase. Four of seven agents are also missing per-agent `mcp_tools` unit tests, leaving the per-agent MCP surface validated only through the coarser `test_mcp_server.py` tests.

---

## Severity roll-up (tests)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 3 |
| Minor | 3 |
| Nit | 2 |

---

## What's working

- **Stress suite quality** — The three stress test files (`test_json_extraction_variants.py`, `test_qa_rubric_variants.py`, `test_consistency_check_variants.py`) are genuinely well-crafted. They were written in direct response to live-test failures (CR-101, CR-102, CR-104) and test exactly the malformed-LLM-output scenarios that burned the project in production. This is the best example of "test-with-fix" culture in the codebase. `test_qa_rubric_variants.py` in particular covers 35+ parametrized and named cases: missing dimensions, null scores, string-typed scores, `revision_instructions` as dict/string/null. This is professionally paranoid testing.

- **Zero skipped tests in the default suite** — The hard project rule (no `pytest.mark.skip`, no `xit`) is holding. The `@pytest.mark.skipif(RECORD_CASSETTES == "1")` pattern in integration tests is the only skip usage, and it is correctly gated on an opt-in environment variable for a VCR re-recording workflow — a legitimate and narrowly scoped exception.

- **Live-test gating is principled** — The `live/conftest.py` gating approach (opt-in env var, cost-per-test cap, Ollama zero-cost tier) is clean. The capability gate logic (probing `localhost:11434` before skipping rather than unconditionally skipping) is the right model.

- **Kernel cost tracker coverage** — `test_cost.py` covers 18 cases including mutation-safety on hard-cap overflow, per-stage breakdown ordering, model field last-wins aggregation, and summary schema keys. This is well-designed.

- **Resume idempotency test** — `test_resume_idempotency.py` pins ADR-0007 with a crash-inject-and-resume mock that bills real costs per call. This is exactly the regression test that should exist for that behavior.

- **Doc-drift gates** — `test_mcp_tool_names_documented.py` and `test_readme_cli_invocations.py` are unusual and valuable: they parse live documentation and cross-check it against the registered tool names and CLI flags. Most projects do not test this at all; AgentSuite tests it with two dedicated files.

- **Golden snapshot infrastructure** — The split between `assert_artifact_exact` (byte-stable, no tolerance) and `assert_qa_within_tolerance` (numeric, 5% rtol) is well-designed and protects against contributors accidentally masking text drift with numeric tolerance. All 7 agents have committed golden snapshots.

- **Kernel base-agent contract test** — `test_base_agent.py` uses a minimal `_FakeAgent` subclass rather than mocking the real agents, which means the test exercises the real pipeline dispatch loop and the resume/approve contract without being coupled to any agent's specific behavior.

---

## What couldn't be assessed

- **CI flakiness history** — No access to GitHub Actions run history. Cannot assess whether any tests have a flaky pattern over time. The test design is deterministic (mock LLM, `tmp_path` isolation), so flakiness is unlikely, but it cannot be confirmed.
- **Coverage numbers** — The CI command uses `--cov=agentsuite --cov-report=term-missing` but outputs are not available. Reported coverage cannot be verified against actual behavior coverage.
- **VCR cassettes** — Zero cassettes exist (`tests/integration/cassettes/` is empty). The integration conftest scaffolds the vcr.py infrastructure, but all integration tests currently use `MockLLMProvider` directly. This means the `cassette` fixture is dead infrastructure that is never exercised.

---

## Test landscape

| Dimension | Observation |
|---|---|
| Framework | pytest 8, pytest-cov 5, vcrpy 6 (scaffolded, not in use) |
| Test pyramid shape | Heavy unit (626 functions), moderate golden (54), thin integration (32), stress tier not in CI (46 functions + 41 parametrized cases), 2 live tests |
| Coverage tool | `--cov=agentsuite --cov-report=term-missing` in CI, but only over `tests/unit tests/integration tests/golden` — stress is excluded |
| Reported coverage | Not directly available; structural analysis performed |
| Flakiness posture | Clean design — all tests use deterministic mocks, isolated `tmp_path`, no wall-clock dependencies |
| CI blocking? | Yes for unit/integration/golden. **No for stress tier.** |

---

## Findings

> **Finding ID prefix:** `TEST-`
> **Categories:** Coverage / Shortcut / Flakiness / Quality / Ergonomics / Mocking / Regression / CI

---

### TEST-001 — Critical — CI — Stress suite excluded from CI

**Evidence**

`.github/workflows/test.yml` line 25:
```
run: pytest tests/unit tests/integration tests/golden -v --cov=agentsuite --cov-report=term-missing
```

The `tests/stress/` directory is not listed. The `Makefile` `test` target also omits it:
```makefile
test: test-unit test-integration test-golden
```
`pyproject.toml` `testpaths = ["tests"]` means running `pytest` locally would include stress, but CI does not. The 87 stress tests — covering the JSON-fence bugs (CR-101), null-score bugs (CR-102), and missing-dimension bugs (CR-104) that burned in live testing — can regress silently on any PR.

**Why this matters**

The stress suite was written precisely to prevent the class of bugs that reached production. If a prompt refactor silently breaks `extract_json()` fence handling or `qa_stage()` null-score handling, CI will go green while the regressions are live. The stress suite catches exactly these bugs but cannot fulfill that purpose if it never runs in CI.

**Blast radius**
- Adjacent code: all 7 agents share the same `extract_json`, `spec_stage` consistency check path, and `qa_stage` scoring path. A regression in any of these affects every agent.
- User-facing: `extract_json` failures produce silent wrong results or crashes mid-run. QA score null-handling failures produce wrong `requires_revision` decisions. These are the highest-impact failure modes in the entire product.
- Tests to update: none needed — the tests exist; the CI config needs one line added.
- Related findings: none — this is a standalone CI configuration gap.

**Fix path**

Update `.github/workflows/test.yml` line 25 to:
```
run: pytest tests/unit tests/integration tests/golden tests/stress -v --cov=agentsuite --cov-report=term-missing
```
Update the `Makefile` `test` target to include `tests/stress`. Takes 2 minutes.

---

### TEST-002 — Major — Coverage — `SequentialMockLLMProvider` has zero test coverage

**Evidence**

`agentsuite/llm/mock.py` ships `SequentialMockLLMProvider` (lines 61–115). Codebase-wide grep:
```
grep -rn "SequentialMock" tests/ --include="*.py"
(no output)
```
The class is defined and documented but never imported or exercised in any test file. `tests/unit/llm/test_mock.py` covers `MockLLMProvider` with 7 tests but has zero imports of `SequentialMockLLMProvider`.

**Why this matters**

`SequentialMockLLMProvider` is designed for testing pipelines where "the same prompt pattern fires N times but you want to inject a bad response on a specific call." This is exactly the pattern needed to test retry logic, multi-call spec stages, and revision cycles. Its absence from tests means:
1. Bugs in `SequentialMockLLMProvider` itself won't be caught.
2. Future contributors who try to use it won't know whether it actually works.
3. The regression-test scenarios it was designed to enable (per the docstring) are not being written because the tool is untested.

**Blast radius**
- Adjacent code: `agentsuite/llm/mock.py` — `MockLLMProvider` and `SequentialMockLLMProvider` live in the same module. A refactor that touches the `complete()` dispatch logic affects both.
- Shared state: the `sequences` dict mutation in `SequentialMockLLMProvider.complete()` (pop-from-list) is stateful in a way `MockLLMProvider` is not. That statefulness is untested.
- Related findings: TEST-005 (revision-cycle behavior untested) — `SequentialMockLLMProvider` is the natural tool for testing what happens when `requires_revision=True` triggers a second QA pass.

**Fix path**

Add `tests/unit/llm/test_mock_sequential.py` (or extend `test_mock.py`) with tests covering:
- Returns first item, then second item, then repeats last item indefinitely
- Longest-match-first rule applies to sequential providers
- `NoMockResponseConfigured` raised when no key matches
- `calls` list accumulates correctly
- Sequential provider correctly handles single-item lists (repeats the one item)

---

### TEST-003 — Major — Coverage — Four of seven agents missing per-agent `mcp_tools` unit tests

**Evidence**

Per-agent `test_mcp_tools.py` inventory:
```
founder:     tests/unit/agents/founder/test_mcp_tools.py  — EXISTS
design:      tests/unit/agents/design/test_mcp_tools.py   — EXISTS
product:     tests/unit/agents/product/test_mcp_tools.py  — EXISTS
engineering: tests/unit/agents/engineering/               — MISSING
marketing:   tests/unit/agents/marketing/                 — MISSING
trust_risk:  tests/unit/agents/trust_risk/                — MISSING
cio:         tests/unit/agents/cio/                       — MISSING
```

The `test_mcp_server.py` file exercises the MCP layer only for `founder` as the representative agent (it sets `AGENTSUITE_ENABLED_AGENTS=founder` in every test). The missing agents' MCP tools are only validated at the integration level (which also focuses on the pipeline, not the MCP surface).

**Why this matters**

Each agent has its own `mcp_tools.py` module with `register_tools()`, a `RunRequest` schema, and agent-specific handler implementations. The per-agent MCP surface — `run`, `resume`, `approve`, `get_status`, `list_runs` — is what MCP clients (Codex, Claude Code, Cowork) call directly. A bug in `trust_risk.mcp_tools.register_tools()` or `engineering.mcp_tools.EngineeringRunRequest` defaults would not be caught by the current suite.

**Blast radius**
- Adjacent code: `agentsuite/agents/engineering/mcp_tools.py`, `agentsuite/agents/marketing/mcp_tools.py`, `agentsuite/agents/trust_risk/mcp_tools.py`, `agentsuite/agents/cio/mcp_tools.py` — all unexercised at the unit level.
- User-facing: MCP is the primary integration surface for the product. Silent bugs in tool registration, default arguments, or error handling in the missing agents would surface as MCP client errors.
- Migration: none.
- Tests to update: none to update — four test files need to be created.
- Related findings: TEST-001 (stress suite CI gap is the higher-severity CI gap; this is the coverage gap).

**Fix path**

Create `tests/unit/agents/{engineering,marketing,trust_risk,cio}/test_mcp_tools.py` mirroring the pattern in `tests/unit/agents/product/test_mcp_tools.py`. Minimum coverage: tool registration, `RunRequest` schema defaults, and one `get_status` round-trip with a mock run. The existing `test_mcp_server.py` already tests the multi-agent registration dispatch — these per-agent tests should focus on the per-agent handler behavior.

---

### TEST-004 — Major — Coverage — Revision cycle behavior (requires_revision=True → re-run) not tested end-to-end

**Evidence**

`tests/stress/test_qa_rubric_variants.py` tests that `qa_stage()` sets `requires_revision=True` when scores are below threshold. `tests/stress/test_consistency_check_variants.py` tests that `spec_stage()` sets `requires_revision=True` on critical mismatches. But no test in any tier exercises the full pipeline behavior when `requires_revision=True`: does the agent loop back? How many times? What does the operator see?

Grep across all non-live tests:
```
grep -rn "requires_revision.*True" tests/ --include="*.py" | grep -v stress/
```
Returns only state-assertion lines in unit tests — never an end-to-end pipeline invocation that produces a revision cycle.

The integration tests (e.g. `test_founder_full_pipeline_with_mock_provider`) all use `_default_mock_for_cli()` which returns scores of 8.0 — always passing. No integration test injects a failing QA score to observe the revision path.

**Why this matters**

The revision cycle is a first-class product feature — it is the mechanism by which the agent improves its output before presenting it to the operator. If the cycle has a bug (infinite loop, wrong stage restart, cost double-billing on the revision leg), it would not be caught. A user who hits `requires_revision=True` has a materially different run experience than the happy path. That experience is currently untested.

**Blast radius**
- Adjacent code: `agentsuite/kernel/base_agent.py` pipeline dispatch, `agentsuite/kernel/state_store.py` (state persistence across revision), `agentsuite/kernel/cost.py` (cost accumulation across revision legs).
- Shared state: `RunState.requires_revision` and `RunState.cost_so_far` both affect revision behavior.
- User-facing: any run that scores below 7.0 on any dimension. In production, this is a real scenario.
- Related findings: TEST-002 (`SequentialMockLLMProvider` is the tool to write this test; its absence removes the natural test-writing path).

**Fix path**

Write one integration test that:
1. Constructs a `MockLLMProvider` that returns failing QA scores on first call, passing on second.
2. Runs the pipeline through a full agent (Founder is the representative specimen).
3. Asserts the final state reaches `approval` and `requires_revision=False`.
4. Asserts cost accounting reflects both the initial run and the revision leg.

`SequentialMockLLMProvider` is the right tool for step 1 once TEST-002 is addressed.

---

### TEST-005 — Minor — Coverage — VCR cassette infrastructure is dead code

**Evidence**

`tests/integration/conftest.py` scaffolds `vcrpy` cassette fixtures. `pyproject.toml` lists `vcrpy>=6.0` as a dev dependency. `tests/integration/cassettes/` directory exists but contains zero files:
```
ls tests/integration/cassettes/ | wc -l
0
```
The `cassette` fixture is never imported by any test in `tests/integration/`. All integration tests use `MockLLMProvider` directly. The `rerecord-cassettes` Makefile target and `RECORD_CASSETTES=1` guard in integration tests are infrastructure for a real-provider integration path that does not yet exist.

**Why this matters**

Dead infrastructure has carrying cost: the `cassette` fixture adds to developer confusion ("when do I use this?"), `vcrpy` is a dev dependency that adds install time and a supply chain surface, and the `RECORD_CASSETTES` skipif guards in integration tests add noise to test files. More importantly, the intent — real-provider integration tests with VCR cassettes — is a good idea that is currently not delivered. The infrastructure exists but the promise is not fulfilled.

**Fix path**

Two options:
1. (Preferred) Record one cassette per agent against a real provider and commit it. This delivers the original intent and tests a path that MockLLMProvider cannot: actual HTTP request/response serialization.
2. Remove the cassette infrastructure, the `vcrpy` dependency, and the `RECORD_CASSETTES` guards from integration tests if the VCR path is not planned for the current sprint. Clean up the dead code.

---

### TEST-006 — Minor — Coverage — Live tier has only 2 tests covering only `founder` agent

**Evidence**

`tests/live/` contains exactly 2 test functions:
- `test_founder_full_pipeline_live` — cloud provider, Founder agent only
- `test_founder_full_pipeline_against_local_ollama` — Ollama provider, Founder agent only

Six of seven agents (design, product, engineering, marketing, trust_risk, cio) have no live coverage. The live tier's purpose is to validate real LLM output quality, not just pipeline mechanics. An agent whose prompts silently degrade (from a model version bump, a prompt refactor, or a rubric change) will not be caught by the live tier.

**Why this matters**

Per the project's own CLAUDE.md standards: "Live tests run only at v0.X.0 releases with `RUN_LIVE_TESTS=1` and a $10 total cap." This is explicitly scoped to major releases. At those release boundaries, having only founder coverage means six agents are promoted to a release without live validation. The golden tier provides mock-LLM stability checks, but it cannot catch prompt quality regressions that only manifest with real models.

**Fix path**

Add one live test per remaining agent before the next v0.X.0 release. Each test mirrors `test_founder_full_pipeline_live`: run the full pipeline, assert `stage == "approval"`, assert the primary artifact exists and contains real markdown headings, assert `cost_so_far.usd <= PER_TEST_CAP_USD`. The total cap is $10 — 7 agents × ~$0.50 per run is well within budget.

---

### TEST-007 — Minor — Quality — Golden snapshot quality check is non-empty only for mock-LLM output

**Evidence**

`tests/golden/test_founder_patentforgelocal.py` line 51–55:
```python
def test_golden_brand_system_non_empty(tmp_path):
    """Under mock LLM, bodies are scaffold strings — assert non-emptiness only.
    Real heading checks live in the live tier (Task 30)."""
    _, run_dir = _run_founder(tmp_path)
    body = (run_dir / "brand-system.md").read_text(encoding="utf-8")
    assert len(body) > 0
```

The `assert_artifact_exact` test does pin the byte-exact content of `brand-system.md` against the committed snapshot. However, the snapshot itself was captured from `MockLLMProvider` output, which returns scaffold strings like `# brand-system\nMocked content.`. This means the golden snapshot verifies determinism of the mock — not quality or structure of the output. A bug that produced a one-character file would be caught, but a bug that produced structurally wrong output (no headings, wrong section order) would pass as long as the mock output matches.

This is acknowledged in the test comments ("Real heading checks live in the live tier"), so it is Minor — the design choice is intentional and documented.

**Why this matters**

The golden tier's bite is in detecting prompt drift and template drift, not in asserting content quality. That is appropriate given the mock LLM constraint. The risk is that contributors may interpret "golden tests pass" as "output quality is fine" — they are different claims. The comments help, but the separation could be made more explicit in CONTRIBUTING.md.

**Fix path**

Add a comment at the top of `tests/golden/_helpers.py` making the scope explicit: "These tests verify mock-LLM output stability. They detect prompt and template drift. They do not validate real-LLM output quality, which is the live tier's job." No test changes needed.

---

### TEST-008 — Nit — Ergonomics — `Makefile` `test` target omits `tests/stress/`

**Evidence**

```makefile
test: test-unit test-integration test-golden
```
There is no `test-stress` target and no inclusion in the default `make test`. A developer running `make test` locally would silently skip all 87 stress tests. Running `pytest` directly from the repo root would include them (since `testpaths = ["tests"]` covers all subdirs), creating a discrepancy between `make test` and direct `pytest`.

**Fix path**

Add `test-stress: pytest tests/stress -v` and include it in the `test` target. This is the same fix as TEST-001 at the Makefile level.

---

### TEST-009 — Nit — Quality — `test_mock.py` does not test the longest-match-first fix referenced in its own code comments

**Evidence**

`agentsuite/llm/mock.py` line 41–45:
```python
"""TEST-003 (audit): match by *longest* matching keyword rather than
dict-insertion order. With insertion-order matching, ``responses =
{"brand": ..., "brand-system": ...}`` would return the ``brand``
response for a ``brand-system`` prompt -- a silent prompt-drift
masking pattern. With length-descending matching, the most-specific
keyword wins.
```

The code references a past audit finding (TEST-003) and documents the fix. `tests/unit/llm/test_mock.py` does not include a test for this specific behavior: a prompt that matches both `"brand"` and `"brand-system"` should return the `brand-system` response. The existing `test_mock_falls_through_keywords_in_order` tests the basic keyword ordering but does not test the longest-match-first rule.

**Fix path**

Add to `test_mock.py`:
```python
def test_mock_longest_match_wins():
    """Longer key must win even when shorter key appears first in dict."""
    p = MockLLMProvider(responses={"brand": "short", "brand-system": "long"})
    resp = p.complete(LLMRequest(prompt="writing brand-system.md", system=""))
    assert resp.text == "long", "Shortest key must not mask longer matching key"
```

---

## Shortcut census

| Shortcut pattern | Count |
|---|---|
| `pytest.mark.skip` (hard skips) | 0 |
| `@pytest.mark.skipif` — legitimate cost/capability gates | 10 (all correct) |
| `.only` (left in) | 0 |
| `TODO: add test` / similar | 0 |
| Empty assertion / placeholder | 0 |
| `--retry` / retries normalized | No |
| `assert True` placeholders | 0 |

The shortcut census is clean. The 10 `skipif` uses are all narrowly gated on `RECORD_CASSETTES == "1"` (integration tests) or `RUN_LIVE_TESTS != "1"` / `RUN_LIVE_OLLAMA_TESTS != "1"` (live conftest). No unconditional skips exist.

---

## Blind spots by class

1. **Revision cycles** — No test exercises the full `requires_revision=True → re-run` pipeline behavior. This is the second major feature branch (after the happy path) and is entirely unverified at the pipeline level. (TEST-004)

2. **Multi-agent MCP surface** — Four of seven agents' MCP tool registration and handler behavior is unverified at the unit level. Cross-agent tool dispatch tests exist but are coarse. (TEST-003)

3. **Sequential mock behavior** — `SequentialMockLLMProvider` is untested; scenarios requiring per-call response injection (nth-call fault injection, revision-cycle mock, retry-exhaustion mock) cannot be written reliably until TEST-002 is addressed.

4. **Concurrent or overlapping run isolation** — No test verifies that two simultaneous runs with different `run_id` values do not share state. The design appears isolating (each run gets its own `tmp_path` directory), but this is not explicitly pinned.

5. **Cost cap interaction with revision cycles** — A revision cycle that approaches the cost cap mid-way through the second attempt is not tested. Does the cap accumulate across revision legs? The resume idempotency test covers crash-then-resume, but not score-fails-then-re-QA.

6. **MCP server startup failure modes** — `test_mcp_server.py` tests `build_server()` construction, but no test covers `main()` behavior: `--help` output, `--version` output, or the stdio loop startup.

7. **Input validation edge cases** — Empty string inputs (`user_request=""`, `business_goal=""`), very long inputs (>10,000 characters), and inputs with special characters (HTML tags, null bytes, Unicode edge cases) are not tested at the `input_schema` level across most agents.

8. **File system failure modes** — No test injects file system errors (disk full, permission denied, path-too-long on Windows). The `ArtifactWriter` atomic-save path (`_state.tmp`) is tested for no leftover `.tmp` files on success, but not on failure.

---

## Patterns and systemic observations

**Pattern 1: Founder-as-representative-specimen is reasonable but creates blind spots.**
The stress tests explicitly note "Uses the Founder agent as a representative specimen; the defensive code path is identical across all 7 agents." This is a valid tradeoff — testing all 7 agents for every stress variant would be 7x the test count for little additional value if the code is truly shared. The risk is that agent-specific overrides or subtle divergences in how each agent calls `qa_stage()` or `spec_stage()` are not caught. The "identical across all 7 agents" claim is asserted by comment, not by test.

**Pattern 2: Integration tests are effectively extended unit tests.**
All integration tests use `MockLLMProvider` directly. They exercise the real pipeline orchestration (stage dispatch, state persistence, artifact writing) with a mocked LLM. This is the right choice for CI speed and cost control, but it means the "integration" tier is more accurately described as "pipeline unit tests." The VCR cassette infrastructure was intended to deliver true integration testing but is not yet populated. The labeling is slightly misleading.

**Pattern 3: Test quality is higher than average for this codebase type.**
The audit comment in `mock.py` (`TEST-003 (audit): match by *longest* matching keyword...`) is an example of a good practice: documenting the reason for a code choice by referencing the test finding that prompted it. The `test_resume_idempotency.py` is another example — a complex contract is pinned by a test that both simulates the failure and verifies the recovery. This is above-average test culture.

**Pattern 4: The `_default_mock_for_cli()` fixture is large and growing.**
The `_default_mock_for_cli()` function in `mock.py` is ~160 lines of canned responses for all 7 agents. It is used across CLI tests, MCP tests, integration tests, and golden tests. As agents are added or prompts are changed, this fixture requires coordinated updates. If a prompt change is made that breaks a keyword match silently (because the new prompt no longer contains the old keyword), tests that rely on `_default_mock_for_cli()` will fail with `NoMockResponseConfigured` rather than a meaningful assertion failure. The longest-match-first fix helps, but the fixture's scope is a maintenance surface to watch.

---

## Appendix: test artifacts reviewed

**Test directories:**
- `tests/unit/` — 109 files, 626 test functions
- `tests/integration/` — 10 files, 32 test functions
- `tests/golden/` — 9 files (7 agent tests + `_helpers.py` + `__init__.py`), 54 test functions
- `tests/stress/` — 3 files, 46 named test functions + 41 parametrized cases (87 total per audit prompt)
- `tests/live/` — 2 files, 2 test functions (gated)
- `tests/*.py` — 5 top-level test files, 13 test functions

**Sample test files read in full:**
- `tests/stress/test_json_extraction_variants.py`
- `tests/stress/test_qa_rubric_variants.py`
- `tests/stress/test_consistency_check_variants.py`
- `tests/unit/test_mcp_server.py`
- `tests/unit/test_cli.py`
- `tests/unit/kernel/test_cost.py`
- `tests/unit/kernel/test_base_agent.py` (partial)
- `tests/unit/kernel/test_state_store.py` (partial)
- `tests/unit/llm/test_mock.py`
- `tests/unit/llm/test_retry.py`
- `tests/unit/agents/engineering/test_stages_spec.py`
- `tests/unit/agents/engineering/test_stages_execute.py`
- `tests/unit/agents/cio/test_qa.py` (partial)
- `tests/unit/agents/trust_risk/test_agent.py` (partial)
- `tests/golden/_helpers.py`
- `tests/golden/test_founder_patentforgelocal.py`
- `tests/golden/test_cio_acme_cio.py` (partial)
- `tests/integration/test_resume_idempotency.py`
- `tests/integration/test_founder_pipeline.py` (partial)
- `tests/integration/test_cio_pipeline.py` (partial)
- `tests/integration/test_sdk_usage.py`
- `tests/integration/test_downstream_consumer.py` (partial)
- `tests/live/conftest.py`
- `tests/live/test_founder_live.py`
- `tests/live/test_ollama_live.py`

**CI configuration reviewed:**
- `.github/workflows/test.yml`
- `Makefile`
- `pyproject.toml` (`[tool.pytest.ini_options]`)
- `scripts/run-cleanroom.sh` (partial)

**Source files reviewed:**
- `agentsuite/llm/mock.py` (full)
- `agentsuite/mcp_server.py` (full)
