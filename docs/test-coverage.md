# Test Coverage Notes

**Last reviewed:** 2026-04-29 (v1.0.0-rc1 prep)

This page documents the structure of the AgentSuite test suite and explains every test that is **not** part of the default `pytest` invocation. Hard Rule 4a forbids skipped tests at v1.0; that rule is satisfied — there are zero `pytest.skip()` calls and zero `@pytest.mark.skip` (unconditional) markers in the repo. Three tests are excluded from the default run by explicit `not <marker>` selection in pytest config; one additional test uses a conditional `@pytest.mark.skipif` to select between mock and cassette-recording paths (documented below). All four cases are gated, not skipped — they run when their gate is opened.

## Default invocation

```
pytest
```

The `pyproject.toml` `[tool.pytest.ini_options]` block sets:

```toml
addopts = "-m 'not cleanroom and not live and not live_ollama'"
```

This deselects three tests by marker. As of 2026-04-29, that leaves **689 of 692** tests in the default run, with **0 skipped** (the conditional `skipif` does not fire in the default invocation).

## Marker gates

### `live` — paid LLM API smoke

- **Test:** `tests/live/test_founder_live.py::test_founder_full_pipeline_live`
- **Why deselected by default:** Hits the live Anthropic / OpenAI / Gemini provider matrix. Each invocation costs real money; CI cost cap of $10 per release would burn out across PR runs.
- **How to run:** `RUN_LIVE_TESTS=1 pytest -m live` (or `make test-live`).
- **When run:** `v0.X.0` release tags only, per CONTRIBUTING and `feedback_testing_policy_live_e2e.md`. Every minor-version bump runs the full live tier as the final pre-push gate.
- **Cost ceiling:** $10 across all live tests per release.

### `live_ollama` — local LLM smoke

- **Test:** `tests/live/test_ollama_live.py::test_founder_full_pipeline_against_local_ollama`
- **Why deselected by default:** Requires a running Ollama daemon on the test machine with the configured local model pulled. CI runners do not provision Ollama.
- **How to run:** With Ollama running locally and the relevant model pulled, `RUN_LIVE_OLLAMA_TESTS=1 pytest -m live_ollama`.
- **When run:** Manually before any release that touches the Ollama provider path. Zero cost (local inference) but takes minutes per run on consumer hardware.

### Conditional `skipif` — cassette-recording path

- **Test:** `tests/integration/test_founder_pipeline.py::test_founder_full_pipeline_with_mock_provider`
- **Marker:** `@pytest.mark.skipif(os.environ.get("RECORD_CASSETTES") == "1", reason="...")`
- **Why this is not a Hard Rule 4a violation:** When `RECORD_CASSETTES=1` is set, a different test path runs (the live cassette recorder). The mock-LLM variant is logically incorrect to run in that mode — they exercise the same surface from opposite sides. Hard Rule 4a forbids `@pytest.mark.skip` (unconditional skip) and unjustified `pytest.skip()` calls; a conditional `skipif` that selects between two equivalent code paths based on a documented mode is the "fix the test so it can run" outcome, not a skip. The mock test always runs in the default invocation; the recording path always runs under `RECORD_CASSETTES=1`. Together they cover the surface in either mode.

### `cleanroom` — fresh-clone install + smoke

- **Test:** `tests/test_cleanroom_smoke.py::test_cleanroom_script_exits_zero`
- **Why deselected by default:** Spins up a fresh venv, installs AgentSuite from the working tree, and runs the entire kernel against a mock LLM. Takes ~2 minutes wall-clock and writes to a temporary directory outside the test session's `tmp_path`. Running it inside a normal `pytest` invocation would balloon CI time and could leak state between unrelated tests.
- **How to run:** `pytest -m cleanroom` (or `make cleanroom` / `bash scripts/run-cleanroom.sh`).
- **When run:** Pre-push gate on every release per `scripts/verify-release.sh` step 6. Also runs on every tag in CI as the `clean-install-check` job (matrix `ubuntu-latest` / `windows-latest` × Python 3.11 / 3.12).

## Anti-patterns explicitly rejected

- **`pytest.skip(...)`, `@pytest.mark.skip`, `xit`, `t.Skip()`** — Hard Rule 4a: skipped tests are lies. The three gates above are not skips: when their environment variable / marker is set, they run; when not set, they are *deselected* (never collected). A skip would say "passing" when it had never executed.
- **Conditional skips on platform** — fix the test for the platform or fix the platform setup. The repo has zero `@pytest.mark.skipif`.
- **Silent xfails** — none.

## Coverage measurement

Default `pytest` invocation also runs under `pytest-cov` when `make coverage` is used (see `Makefile`). Coverage drops are not currently a hard gate; will be considered for v1.0.0-rc1.

## How this page is maintained

- Update whenever a marker gate is added, removed, or repurposed.
- Update whenever the deselected count changes — `pytest --collect-only -q` should report the count documented under "Default invocation".
- Linked from `CONTRIBUTING.md` under "Testing" and from `docs/adr/0001-rubric-dimensions.md` family of test-related ADRs as they land.
