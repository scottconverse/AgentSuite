# Test Suite Deep-Dive — AgentSuite v1.0.0 GA (commit 9540957)

**Audit date:** 2026-04-29
**Role:** Test Engineer
**Scope audited:** tests/ tree (unit, integration, golden, live, cleanroom), .github/workflows/{test,release,lint,provider-drift}.yml, scripts/run-cleanroom.sh, scripts/check_install_block_drift.py, agentsuite/llm/mock.py
**Auditor posture:** Adversarial

---

## TL;DR

This is a serious test suite by community-Python standards: 689 default tests across a deliberate unit / integration / golden / cleanroom / live tier separation, Hard-Rule-4a-clean (no `pytest.skip` outside two well-justified capability gates), atomic-write + schema-version coverage, and a real cassette-recording escape hatch via `RECORD_CASSETTES=1`. Tests-to-code ratio is ~1.43:1 (11.7K test LOC vs. 8.2K source LOC). The team takes testing seriously and it shows.

The blind spots are concentrated in three places: (1) the integration tier is **mock-only** despite naming itself "integration" — `tests/integration/cassettes/` contains only `.gitkeep`, so v1.0 ships with zero recorded cassettes and the "vcr" infrastructure is scaffold theater; (2) the live tier is two thin happy-path tests asserting "stage == approval" + heading count, which is fig-leaf coverage for the v0.X.0 / GA release boundary; (3) **no test enforces parity between the README's documented CLI invocations / MCP tool names and the actually-registered Typer commands and tool registry** — the install-block drift check covers the install command but not the run commands. The UX role's screenshot-drift finding has the same root cause.

The single most likely class of bug to slip through: a real-provider regression (Anthropic/OpenAI/Gemini SDK shape change, retry behavior, cost accounting) that the mock provider's keyword-substring matcher cannot model, hitting users on first paid run.

## Severity roll-up (tests)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 2 |
| Major | 4 |
| Minor | 3 |
| Nit | 1 |

## What's working

- **Hard Rule 4a discipline is real.** A repo-wide grep finds zero `pytest.skip` decorators in test bodies; the only `skipif` markers are in `tests/integration/test_*_pipeline.py` (capability gate for cassette-record mode), `tests/test_cleanroom_smoke.py` (bash availability), `tests/unit/kernel/test_artifacts.py:142` (Windows-only path test), and `tests/live/conftest.py` (live-tier cost gate). All four are documented capability gates, not "make it pass" skips. This is rare.
- **Schema-version coverage is honest.** `tests/unit/kernel/test_state_store.py:118-166` pins `SCHEMA_VERSION=2`, asserts the field is written, asserts pre-v0.9 state files raise `RunStateSchemaVersionError`, and asserts older versions are rejected. The rc1 compat-freeze claim is backed by tests for this dimension.
- **Deterministic golden snapshots split exact-match from numeric tolerance.** `tests/golden/_helpers.py` separates `assert_artifact_exact` (bytes-stable text) from `assert_qa_within_tolerance(rtol=0.05)` (float ordering). The split is type-enforced — a contributor cannot accidentally apply tolerance to text. 7 agents × 2 shapes = ~14 snapshot dirs, all populated.
- **Resume idempotency is contract-tested with a billing mock.** `tests/integration/test_resume_idempotency.py` subclasses `MockLLMProvider` to bill non-zero USD and crash at the Nth call exactly once, then verifies cost carry-forward and stage skip on resume. This is the kind of test that catches real bugs.
- **Wheel install + console-script smoke runs in CI.** `.github/workflows/test.yml` `wheel-smoke` job builds, installs into a fresh venv, imports all 7 agent prompt loaders, runs `agentsuite --help` and `agentsuite-mcp --help`. This catches packaging regressions that pure-source tests miss.
- **Install-block drift is enforced both pre-push and on-tag.** `scripts/check_install_block_drift.py` + `release.yml` step "Verify README install block has not drifted from fixture" diff README's `<!-- install:start -->` block against `tests/fixtures/install-block.md`.
- **Per-stage cost cap + aggregate cap** are exercised in `tests/unit/kernel/test_cost.py` (16 tests) including the `_per_stage_skipped_when_current_stage_none` boundary.

## What couldn't be assessed

- CI run history / flakiness rate — no access to GitHub Actions logs in this audit.
- Mutation-testing score — the project does not run `mutmut` or equivalent, so I cannot quantify the gap between line coverage and behavior coverage.
- Real-provider compatibility — by design, live tests are gated to GA tags and would have run during the v1.0.0 release, but I cannot inspect that run from here.

---

## Test landscape

| Dimension | Observation |
|---|---|
| Framework(s) | pytest 8.x, vcr.py (scaffolded but unused), pytest-cov |
| Test pyramid shape | Heavy unit (~600), thin integration (mock-only), 7 golden agents, 2 live happy-path, 1 cleanroom |
| Coverage tool | coverage.py via `pytest --cov=agentsuite --cov-report=term-missing` in CI |
| Reported coverage | Not pinned in pyproject; CI prints term-missing but no minimum threshold enforced |
| Flakiness posture | No `--retry`, no `flaky` decorators — clean. Cannot verify CI history. |
| CI blocking? | Yes for unit/integration/golden/cleanroom/wheel-smoke on PR + push to main |

---

## Findings

### [TEST-001] — Critical — Coverage / Mocking — Integration tier is "integration" in name only; cassette dir is empty

**Evidence**

```
$ ls tests/integration/cassettes/
.gitkeep
```

`tests/integration/conftest.py:1` declares "Integration test fixtures — vcr.py cassette mode (scaffold for v0.2)." Every `tests/integration/test_*_pipeline.py` runs against `MockLLMProvider` / `_default_mock_for_cli()`, e.g. `test_founder_pipeline.py:23`. The `@pytest.mark.skipif(os.environ.get("RECORD_CASSETTES") == "1")` gate means these tests are *skipped* in the only mode that would actually hit a real provider. There are no `.yaml` cassettes anywhere in the repo. The "Re-record via `make rerecord-cassettes`" workflow described in the project context has nothing to re-record against.

**Why this matters**

What the team calls "integration tests" are end-to-end tests of the kernel + agent pipeline against a deterministic stub. They're valuable — they catch wiring errors, state-store regressions, and stage-ordering bugs — but they cannot catch:

- Anthropic / OpenAI / Gemini SDK signature changes (and their dep-bumps don't fail the suite)
- Retry / backoff behavior under real 429 / 5xx
- Cost-accounting drift when a provider changes its tokenization or pricing
- Streaming, tool-use, or system-prompt encoding differences
- Network timeout handling

This is the class of bug that hits a user on first paid run, after `pip install agentsuite[anthropic]`. The v1.0 GA tag promises a stable surface; that promise is unverified against any real provider in CI, and there is no recorded fixture to fall back on.

**Blast radius**
- Adjacent code: All 9 `tests/integration/test_*_pipeline.py` files. The MockLLMProvider keyword-matcher has accumulated provider-specific prompts (mock.py:88-204) that drift further from real prompts every release.
- Shared state: `agentsuite/llm/{anthropic,openai,gemini,ollama}.py` — none of the four cloud providers' real call paths are exercised in CI. `RetryingLLMProvider` (mentioned in 2026-04-28 sprint2 handoff) is only exercised against fake errors.
- User-facing: First real provider run is the customer's UAT. Bug class shifts from "we caught it" to "user filed an issue."
- Migration: None — additive.
- Tests to update: Land at least one recorded `vcr` cassette per provider per agent at GA boundaries. The infrastructure already exists (`tests/integration/conftest.py:13` defines `cassette_for`). It just has nothing in it.
- Related findings: TEST-002 (live tier is thin), TEST-003 (mock prompts drift silently).

**Fix path**

Two options, in priority order:

1. **Land cassettes for one provider × all 7 agents** as a v1.0.1 patch. This is the lowest-cost lift: run the live tier with `RECORD_CASSETTES=1` once, check in the YAML, run the suite without env var to play back. The README claim of "integration tests" then matches reality.
2. **Rename + restructure if cassettes won't ship.** If the team decides cassette playback is wrong for this project, then `tests/integration/` should be renamed `tests/pipeline/` or `tests/agent_e2e_mock/` and the conftest's "scaffold for v0.2" comment removed. Naming honesty is a small cost; mismatched naming masks the gap from future maintainers.

---

### [TEST-002] — Critical — Coverage — Live tier is two happy-path smoke tests, not a real release gate

**Evidence**

`tests/live/test_founder_live.py` (49 lines, one test) and `tests/live/test_ollama_live.py` (49 lines, one test) are the entire `live` and `live_ollama` tiers. The Founder live test asserts:

- `state.stage == "approval"` (shape, not behavior)
- 9 spec artifact filenames exist (presence, not content)
- `brand-system.md` has `>=3` `\n#` headings or starts with `# ` (heading shape)
- `state.cost_so_far.usd <= 3.0` (cost cap held)

There are no live tests for the other 6 agents (design, product, engineering, marketing, trust_risk, cio). The project context states "Live tier: gated by `RUN_LIVE_TESTS=1`; runs only at v0.X.0 / GA tags with $10 cap" — at $3/test that's room for ~3 tests, but only 2 exist.

**Why this matters**

The live tier is the team's stated mechanism for catching real-provider regressions. At v1.0 GA, six of seven agents have zero real-LLM coverage at any time, ever. The Founder agent gets one real call covering "headings exist," which would not catch:

- A provider returning prose without markdown structure (still passes the `or body.startswith("# ")` clause)
- Costs accumulating to $2.99 (under the per-test cap, way over the per-stage budget the kernel would normally enforce)
- Output that is fluent garbage — the test never reads the content of any artifact other than `brand-system.md`'s heading count
- QA rubric scores that are wildly off — the test doesn't read `qa_scores.json`

This is the test the GA boundary depends on, and it is fig-leaf depth.

**Blast radius**
- Adjacent code: All 6 non-Founder agents at GA boundaries.
- User-facing: A real-provider regression in design / product / engineering / marketing / trust_risk / cio reaches users without ever being seen by the suite.
- Migration: None.
- Tests to update: Add 6 more `tests/live/test_<agent>_live.py` files. Each can stay $1-cap with mock-equivalent assertions that read at least one full artifact.
- Related findings: TEST-001 (no integration cassettes), TEST-003 (mock drift).

**Fix path**

For v1.0.1 or the next minor release: replicate the Founder live test for all 6 remaining agents with $1 cap each (total $7 vs. current cap of $10). Tighten Founder's assertion to read `brand-system.md` content for at least one expected substring (project name, persona reference, or audience term that any working pipeline would surface). The point is to fail loudly when a provider response is structurally valid but semantically empty.

---

### [TEST-003] — Major — Mocking — MockLLMProvider keyword-substring matcher silently masks prompt drift

**Evidence**

`agentsuite/llm/mock.py:31-45`:

```python
def complete(self, request: LLMRequest) -> LLMResponse:
    self.calls.append(request)
    for keyword, text in self.responses.items():
        if keyword in request.prompt or keyword in request.system:
            return LLMResponse(...)
    raise NoMockResponseConfigured(...)
```

The match is `if keyword in request.prompt`. The keys (mock.py:88-204) are long human-readable prompt fragments like `"You are extracting structured marketing context from brand and competitor documents. Return ONLY valid JSON."`. If a maintainer rewrites a prompt template — even a minor copy edit — the substring may still match, producing a confidently-wrong canned response that was authored against an older prompt. There is no negative test that fails when prompt and canned-response drift.

**Why this matters**

This is the most common shape of "mocks lie" failure. The deterministic mock that gives the team confidence in 689 passing tests can quietly diverge from the prompts the kernel actually sends. Symptoms: integration suite green, real run produces output that no longer matches the prompt's intent because the prompt evolved while the mock didn't.

**Blast radius**
- Adjacent code: All 7 agents. Every prompt template is keyed against a substring in mock.py.
- Shared state: `agentsuite/agents/<agent>/stages/*.py` — the stage code is the source of truth for prompts; mock.py is the brittle mirror.
- User-facing: Indirect — surfaces only if a real run produces content the mock pretends works.
- Tests to update: Add a `test_mock_keys_match_real_prompts` that imports each stage's prompt-rendering function with deterministic inputs and asserts every prompt's prefix is present *as a unique key* in the mock.
- Related findings: TEST-001, TEST-002.

**Fix path**

Add a single meta-test that, for each agent, renders each stage's prompt with a deterministic minimum input and asserts at least one mock key is a substring AND that key is the longest matching prefix. Even better: switch keys from substring to exact-prefix match (first 60 chars of rendered prompt) so a copy edit in the template breaks the suite loudly.

---

### [TEST-004] — Major — Coverage — No test catches drift between README/USER-MANUAL CLI invocations and registered Typer commands

**Evidence**

`README.md:45,75` and `USER-MANUAL.md:292,301,307,368,378,435,445` document concrete invocations:

```
agentsuite founder run --business-goal "..." --project-slug "..." --inputs-dir "..." --run-id "..."
agentsuite design run --target-audience "..." --campaign-goal "..." --channel "..."
agentsuite product run --product-name "..." --target-users "..." --core-problem "..."
```

No test parses these invocations and asserts the documented commands and flags exist on the registered Typer app. `tests/unit/test_cli.py` checks `--help` exits 0 and tests one mocked run per agent, but does not pin documented flag *names* against the README. A copy edit to README replacing `--target-users` with `--users` would silently ship.

There IS a drift-check for the install block (`scripts/check_install_block_drift.py`) — exactly the right pattern, but applied only to the `pip install` lines, not to the agent-run commands.

**Why this matters**

This is the gap the UX role flagged for screenshots and the same root cause: documented user-visible CLI surface is not pinned by tests. The blast radius is wider than screenshots — every time the CLI evolves (new flag, renamed flag, removed flag) the README/USER-MANUAL claim can silently diverge. New users follow the docs first; a wrong flag is a Day-1 friction event.

The same gap applies to MCP tool names. `docs/adr/0004-mcp-tool-naming.md:28` and `docs/community/launch-posts.md:94` document `agentsuite_<name>_run` as a stable surface. `tests/unit/agents/founder/test_mcp_tools.py:64` checks that `agentsuite_founder_run` is registered, but there is no test that enumerates *all* expected tool names from a fixture and asserts the registry returns exactly that set. A renamed tool would pass the existing per-agent assertion (which is hard-coded per file) and silently break docs.

**Blast radius**
- Adjacent code: `agentsuite/cli.py`, all 7 `agentsuite/agents/<agent>/cli.py` Typer command files, all 7 `agentsuite/agents/<agent>/mcp_tools.py` registration functions.
- Shared state: README.md, USER-MANUAL.md, docs/community/launch-posts.md, ADR-0004.
- User-facing: First-time users following the README/USER-MANUAL hit "Error: no such option" and lose trust.
- Migration: None.
- Tests to update: Add `tests/unit/test_cli_doc_drift.py` that extracts code-fenced `agentsuite ... run ...` invocations from README+USER-MANUAL via regex, parses each into argv, and runs `runner.invoke(app, argv + ["--help"])` asserting exit 0. Add `tests/unit/test_mcp_tool_names_pinned.py` that reads an expected-tool-names fixture (committed to the repo) and asserts the v1.0 compat-freeze surface.
- Related findings: UX role's screenshot-drift Critical (same root cause); TEST-005.

**Fix path**

Pattern is already in the repo — extend `scripts/check_install_block_drift.py` style to:
1. New regex: extract every fenced bash block in README.md and USER-MANUAL.md that begins with `agentsuite `.
2. For each, run a "would this parse" check via `runner.invoke(app, args, ["--help"])`.
3. Fail with the offending block on any non-zero exit.

For MCP: commit `tests/fixtures/mcp_tool_names_v1.txt` listing the 14+ expected tool names, then a unit test compares against `build_server().tool_names()`.

---

### [TEST-005] — Major — Coverage — No concurrency test for the run-directory contract

**Evidence**

`agentsuite/kernel/state_store.py` does atomic writes via tempfile + rename. The only multi-process safety test is the resume-after-crash idempotency test (`tests/integration/test_resume_idempotency.py`) which is sequential. No test exercises:

- Two concurrent `agentsuite founder run` invocations against the same `--run-id` (`--force` flag exists per `tests/unit/test_cli.py:test_force_flag_blocks_existing_run`, but the test mocks the existence check, not the race)
- A read of `_state.json` mid-write
- The `.tmp` file cleanup contract (`test_state_store_save_leaves_no_tmp_files` exists but only on success path; no test on partial writer crash)

**Why this matters**

The atomic-write code exists because race conditions were anticipated. Tests prove the happy path doesn't leave `.tmp` files. They don't prove the two-writer or write-during-read cases. On Windows in particular (where the user runs), atomic-rename semantics differ from POSIX and pytest's `tmp_path` won't expose Windows-specific race conditions unless deliberately exercised.

**Blast radius**
- Adjacent code: `state_store.py`, `artifacts.py` (similar atomic write pattern).
- Shared state: `runs/<run-id>/_state.json`, `runs/<run-id>/<artifact>.md`.
- User-facing: A user re-running the same run-id from two terminals (common on developer laptops) could see corrupted state. Currently neither caught nor pinned.
- Tests to update: `tests/unit/kernel/test_state_store.py` add two-thread/two-process write race; add Windows-marked variant.
- Related findings: None directly — but pairs with the "first paid run" risk class from TEST-001.

**Fix path**

Add `test_state_store_concurrent_writes_serialize` using `concurrent.futures.ThreadPoolExecutor` to fire 5 saves at the same store; assert the load is one of the 5 valid states (not corrupted, not the `.tmp` file). For Windows-specific behavior, mark `@pytest.mark.skipif(sys.platform != "win32")` (consistent with existing pattern in `test_artifacts.py:142`).

---

### [TEST-006] — Major — Coverage — Wheel-install mypy claim is not actually tested

**Evidence**

`tests/integration/test_downstream_consumer.py:74-107` synthesizes a downstream consumer and runs `mypy --strict`. The docstring acknowledges:

> "Editable installs (`pip install -e .`) hide the source tree behind a `.pth` file that mypy does not follow. We point mypy at the repo via `MYPYPATH` so the consumer resolves AgentSuite's typed source — exactly what a downstream consumer with a non-editable install would see via the package's `py.typed` marker."

The MYPYPATH workaround is correct in spirit but tests source-tree resolution, not wheel-install resolution. The project context claims "Real wheel-install case is verified by clean-install-check job in release.yml" — verify that claim. Reading `release.yml`:

- `wheel-smoke` in `test.yml` installs the wheel and runs `--help` (import + console-script smoke).
- `release.yml` `Smoke check — agentsuite CLI runs from clean install` runs `agentsuite --help` and `agentsuite-mcp --help`.

Neither runs `mypy` against the installed wheel. The claim that wheel-install mypy is verified is not supported by the workflows.

**Why this matters**

`py.typed` is a contract with downstream type-checkers. The MYPYPATH test proves source-tree typing works; it does not prove the wheel ships with the right `py.typed` marker, the right files, and resolves under stub_uses_source flow. A user installing `pip install agentsuite[anthropic]` and running mypy on their own code could hit a mypy resolution failure on AgentSuite imports that the suite never sees.

**Blast radius**
- Adjacent code: `pyproject.toml` (`include-package-data` / `py.typed` shipping), `MANIFEST.in`.
- User-facing: Type-checking downstream consumers see ImportError-from-mypy or "Cannot find implementation or library stub" failures.
- Tests to update: Extend `release.yml` smoke step (after wheel install) to: write a 5-line consumer, install mypy, run `mypy --strict consumer.py` against the *installed* package (no MYPYPATH).
- Related findings: TEST-004 (similar pattern — claim made, not pinned).

**Fix path**

In `release.yml` after the existing `Smoke check`, add:

```yaml
- name: Wheel-install mypy check (real py.typed resolution)
  run: |
    .audit-venv/bin/pip install mypy
    cat > /tmp/consumer.py <<'EOF'
    from agentsuite.kernel.schema import Constraints
    from agentsuite.llm.mock import MockLLMProvider
    c: Constraints = Constraints()
    p: MockLLMProvider = MockLLMProvider({})
    EOF
    .audit-venv/bin/mypy --strict /tmp/consumer.py
```

That's the test the claim describes.

---

### [TEST-007] — Minor — Quality — Many unit tests assert state-shape rather than artifact content

**Evidence**

Sampling integration tests:

- `tests/integration/test_design_pipeline.py:38` asserts presence of files: `["_state.json", "inputs_manifest.json", "extracted_context.json", ...]`. No test reads `extracted_context.json` and asserts the extracted persona / brand voice fields are populated.
- `tests/integration/test_founder_pipeline.py:40` (and similar across all 7 agents) checks `state.stage == "approval"`.
- The Founder live test at `tests/live/test_founder_live.py:46` asserts `body.count("\n#") >= 3 or body.startswith("# ")` — heading shape, not content.

The golden tests do exact byte-match against snapshots, which is content-aware. But the integration tier and live tier lean shape-heavy.

**Why this matters**

Shape assertions catch wiring regressions (file didn't exist, state didn't reach approval) but not semantic regressions (file exists with wrong content, approval reached with empty rubric). The golden snapshots backfill some content coverage at the mock level, but in the real-provider path, only the snapshots wouldn't apply (different output every run).

**Blast radius**
- Adjacent code: All 9 integration pipeline tests + 2 live tests.
- User-facing: A bug that produces empty / placeholder / wrong-language artifacts could pass shape tests.
- Tests to update: For each integration test, add `assert <expected substring> in <one artifact>.read_text()` for at least one substring deterministic from the input.

**Fix path**

Per integration test, add one content assertion: e.g. for `test_founder_pipeline`, the input includes `business_goal="Launch PatentForgeLocal v1"` — assert `"PatentForgeLocal" in (run_dir / "brand-system.md").read_text()`. Cheap, content-aware, and would catch mock-drift bugs that shape tests miss.

---

### [TEST-008] — Minor — Ergonomics — No coverage threshold enforced in CI

**Evidence**

`.github/workflows/test.yml:25` runs `pytest --cov=agentsuite --cov-report=term-missing` but does not pass `--cov-fail-under=N`. Coverage is reported in CI logs, not blocked on regression.

**Why this matters**

A test deletion or untested-feature add can silently drop coverage. The team's discipline is high (1.43:1 LOC ratio) so this is currently fine, but the gate isn't mechanical.

**Fix path**

Add `--cov-fail-under=85` (or whatever the current floor is) to the pytest invocation in `test.yml`. Set the threshold to the current measured coverage minus 1pp so day-1 doesn't fail.

---

### [TEST-009] — Minor — Coverage — Provider-specific error path coverage is uneven

**Evidence**

`tests/unit/llm/test_*.py` covers each provider's happy path and basic error mapping. There is no systematic coverage of:

- Anthropic 429 → retry → eventual 200
- OpenAI tool-use response shape divergence between models
- Gemini quota exhaustion
- Ollama daemon connection refused (covered partially by live_ollama gate)

The mocked `RetryingLLMProvider` tests (per the 2026-04-28 sprint2 handoff) exercise retry against fake errors but not provider-specific status codes.

**Fix path**

For each provider, add a `test_<provider>_retry_on_429`, `test_<provider>_raises_on_4xx_other_than_429`, and `test_<provider>_streams_correctly` set. Use `responses` or `httpx_mock` to inject specific HTTP status codes.

---

### [TEST-010] — Nit — Quality — Comment "scaffold for v0.2" in `tests/integration/conftest.py:1` is now stale at v1.0

**Evidence**

`tests/integration/conftest.py:1`: `"""Integration test fixtures — vcr.py cassette mode (scaffold for v0.2)."""`

The repo is at v1.0.0. Either the cassettes shipped (they didn't) or the comment is stale.

**Fix path**

Update the comment to reflect the current state and the decision: either "Cassettes deferred to v1.x — see TEST-001" or "Cassette mode active as of v1.0.1 — see CONTRIBUTING.md."

---

## Shortcut census

| Shortcut pattern | Count |
|---|---|
| `pytest.skip` / `xit` | 0 in test bodies (Hard Rule 4a clean) |
| `@pytest.mark.skipif` (capability gates only) | 11 (cassette record mode in 9 integration files + cleanroom bash + Windows-only artifacts test) |
| `@pytest.mark.skip` | 0 |
| `xfail` | 0 |
| `.only` left in | 0 (n/a — pytest doesn't have `.only`) |
| `TODO: add test` / `FIXME: test` | 0 in tests/ |
| Empty assertion / placeholder | 0 found in sampling |
| `--retry` / retries normalized | None — clean |

This is genuinely better than 95% of community Python projects.

---

## Blind spots by class

- **Real-provider regression** (TEST-001, TEST-002, TEST-003): the entire cloud-provider path is untested at any tier in CI.
- **Doc drift in user-facing CLI / MCP surface** (TEST-004): same root cause as the UX role's screenshot finding.
- **Concurrency / race conditions** (TEST-005): atomic-write code exists, two-writer race is not pinned.
- **Wheel-install type-checking** (TEST-006): claim and evidence don't match.
- **Content vs. shape** (TEST-007): integration + live tiers lean on presence/exit-code rather than artifact content.
- **Provider-specific HTTP error paths** (TEST-009): generic retry covered, provider-specific not.

---

## Patterns and systemic observations

**Pattern: "scaffolded for later" infrastructure that didn't ship.** TEST-001 (empty cassette dir) and TEST-010 (stale conftest comment) point to the same shape: vcr was wired in v0.2 with the intention of recording cassettes, and that work never closed. At v1.0 GA, the integration tier is mock-only and is not honestly named. Recommend either landing one cassette run as a v1.0.1 patch or renaming the tier and removing the scaffold.

**Pattern: "claim made, evidence missing."** TEST-004 (CLI commands documented but not tested for parity) and TEST-006 (wheel-install mypy claim, but no wheel-install mypy test) share a root cause: the team writes precise claims in docs/handoffs, and the tests sometimes lag the precision. Fix: every public claim ("compat freeze," "py.typed," "stable MCP names") should have one pinning test that names the claim in its docstring. The install-block drift script is the gold-standard pattern; replicate it.

**Pattern: shape-over-content in the higher tiers.** TEST-007 + TEST-002. The unit tier is content-rich (per-agent extract / qa / prompt_loader tests dig into structure). The integration / live tiers thin out to "stage == approval" + filename presence. Push at least one content assertion into each integration and live test.

---

## Appendix: test artifacts reviewed

- `tests/test_cleanroom_smoke.py` (full read)
- `tests/live/test_founder_live.py`, `tests/live/test_ollama_live.py`, `tests/live/conftest.py` (full read)
- `tests/integration/conftest.py`, `tests/integration/test_founder_pipeline.py`, `tests/integration/test_resume_idempotency.py`, `tests/integration/test_downstream_consumer.py` (full + sampled)
- `tests/golden/_helpers.py`, `tests/golden/test_founder_patentforgelocal.py` (full read)
- `tests/unit/test_cli.py`, `tests/unit/test_mcp_server.py`, `tests/unit/test_public_api.py`, `tests/unit/test_registry.py` (sampled)
- `tests/unit/kernel/test_state_store.py` (full read)
- `agentsuite/llm/mock.py` (full read)
- `agentsuite/kernel/state_store.py` (skim)
- `.github/workflows/test.yml`, `release.yml` (full read)
- `scripts/run-cleanroom.sh`, `scripts/check_install_block_drift.py` (read)
- `pytest --collect-only -q` confirmed 689 / 692 (3 deselected — `cleanroom`, `live`, `live_ollama`)
