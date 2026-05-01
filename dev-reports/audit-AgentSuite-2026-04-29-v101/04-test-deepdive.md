# Test Suite Deep-Dive — AgentSuite v1.0.1 closure audit

**Audit date:** 2026-04-29
**Role:** Test Engineer
**Scope audited:** v1.0.1 candidate at HEAD `de2a7a3`. Per-ID closure verification of TEST-003, TEST-004 (CR-04), TEST-006 from the v1.0.0 audit, plus deferral honesty for TEST-001 / TEST-002, plus a fresh full-suite run.
**Auditor posture:** Balanced

---

## TL;DR

Three of the five v1.0.0 test findings closed cleanly: TEST-003 (mock matcher) is fixed in `agentsuite/llm/mock.py` and pinned by 6 well-written tests, TEST-006 (wheel-install mypy) has a structurally correct windows-smoke step in `release.yml`, and TEST-004 / CR-04 (doc-CLI / doc-MCP drift) is the highest-leverage trap in the audit — both gates pass on HEAD and the regex extractors are tight enough that I could not construct a plausible false-positive in a 10-minute attempt. TEST-001 and TEST-002 are honestly deferred to W-01 / W-02 in `next-sprint-watchlist.md`. **However, the full suite does NOT match the CHANGELOG claim**: pytest reports `1 failed, 781 passed, 3 deselected` rather than the claimed `777 passed, 8 deselected`. The failure (`tests/integration/test_downstream_consumer.py::test_downstream_consumer_typechecks_clean`) is environmental on this machine — agentsuite is installed without the `[ollama]` extra so mypy walks into `agentsuite/llm/ollama.py` and trips on the missing `ollama` import — but the test is not gated on `ollama` being importable, which is itself a finding. Test count math (689 → 777, +88) does not reconcile with the actual collected count of 785 (781 + 1 failed + 3 deselected); CHANGELOG numbers need an honest pass.

## Severity roll-up (tests)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 0 |
| Major | 2 |
| Minor | 2 |
| Nit | 1 |

## Per-ID closure verdicts

| ID | v1.0.0 severity | v1.0.1 verdict | Evidence |
|---|---|---|---|
| TEST-001 (cassettes) | Critical | **Honestly deferred** to W-01 | `next-sprint-watchlist.md:12-15`. Decision rationale documented (multi-day spike, $30-50 budget). |
| TEST-002 (live tier) | Critical | **Honestly deferred** to W-02 | `next-sprint-watchlist.md:18-20`. Paired with W-01. |
| TEST-003 (mock matcher) | Major | **CLOSED** | `agentsuite/llm/mock.py:41-58` sorts by `-len(kv[0])`. `tests/unit/llm/test_mock_matcher.py` has 6 passing tests. Local run: `6 passed in 1.24s`. |
| TEST-004 / CR-04 (doc drift trap) | Major | **CLOSED** | `tests/test_readme_cli_invocations.py` (3 tests) + `tests/test_mcp_tool_names_documented.py` (2 tests) all pass. Trap covers fenced-code blocks, inline backtick spans across 3 doc files, AND rich-rendered SVG terminal screenshots. |
| TEST-006 (wheel-install mypy) | Major | **CLOSED structurally** | `.github/workflows/release.yml:120-148` — well-formed YAML, valid inline Python, correct mypy invocation. Cannot run locally (Windows GHA runner step), but reads correctly. |

## What's working

- **CR-04 trap design.** `_extract_subcommand_path()` returns `[]` if no subcommand follows `agentsuite`, so prose mentions like `` `agentsuite` `` (no args) are silently skipped — the gate only fires on real invocations. Clean separation.
- **MCP tool-name strict mode.** `test_mcp_tool_names_documented.py` validates byte-for-byte against the registered name rather than accepting a canonicalized form. Matches user behavior (paste-into-config) exactly.
- **TEST-003 fix is principled.** Length-descending sort with stable insertion-order ties is the right answer; the test for "empty keyword does not silently swallow everything" is the kind of adversarial coverage I'd want from a senior IC.
- **Watchdog on deferred work is honest.** W-01 / W-02 entries name the cost ($30-50, $10 cap) and the decisions needed. Not vapor.

## What couldn't be assessed

- The release.yml `windows-smoke` job — Windows-only GHA runner. YAML and inline Python read correctly, but a CI run on a tag is required to confirm the wheel install actually ships `py.typed` + the import paths the consumer uses. Worth grepping the next CI release log for the step output.

---

## Test landscape (delta vs v1.0.0)

| Dimension | v1.0.0 | v1.0.1 candidate |
|---|---|---|
| Default-run tests | 689 (3 deselected) | **collected 785: 781 passed + 1 failed + 3 deselected** |
| CHANGELOG claim | 689 baseline | "+88 tests vs v1.0.0 (689 → 777 passing)" — does not match observed 781 |
| Failures | 0 | 1 (environmental, see TEST-101 below) |
| Skipped tests | 0 (Hard Rule 4a clean) | 0 (still clean) |

---

## Findings

### [TEST-101] — Major — Quality / Coverage — Downstream-consumer typing test fails when `ollama` extra is not installed

**Evidence**

```
tests/integration/test_downstream_consumer.py::test_downstream_consumer_typechecks_clean FAILED
mypy --strict failed against synthetic downstream consumer.
  agentsuite\llm\ollama.py:17: error: Cannot find implementation or library stub
    for module named "ollama"  [import-not-found]
```

The test sets `MYPYPATH=<repo root>` (line 89-90) to make mypy resolve `agentsuite.*` from source. mypy then follows imports into every module under `agentsuite/`, including `agentsuite/llm/ollama.py`, which imports the optional `ollama` package. On any developer machine without `pip install -e .[ollama]` (or `[all]`), the test fails with an import error in code the synthetic consumer never touches.

**Why this matters**

This test is the rc1 "compat freeze" gate for downstream typing — it MUST run cleanly on a vanilla developer setup or the gate becomes "if you remembered to install all extras." The CHANGELOG count (777 passed) presumably came from a machine with all extras installed; on a typical contributor box the suite is RED, which contradicts Hard Rule 4a's spirit (a test that lies about its environment is no better than a skipped test). It also undermines TEST-006's win — the wheel-install mypy smoke depends on the same py.typed contract this test claims to pin.

**Blast radius**
- Adjacent code: `agentsuite/llm/openai.py`, `agentsuite/llm/anthropic.py`, `agentsuite/llm/gemini.py` likely have the same shape — any consumer-typing test that imports the `agentsuite.llm` package transitively is exposed.
- Tests to update: this one. Either narrow the `--strict` walk (`--follow-imports=silent` for files outside the consumer pkg, or `--exclude` ollama.py), or require `[all]` as a dev install precondition documented in CONTRIBUTING.md and conftest.
- Migration: none.
- Related findings: TEST-006 (the windows-smoke job uses a different consumer fixture that does NOT import founder.agent or the LLM provider modules — so the GHA job will probably stay green even when the local suite is red, hiding the gap).

**Fix path**
1. Pin mypy at the consumer package only: drop `--strict` reach into `agentsuite.llm.ollama` by adding `--follow-imports=silent` or `[mypy-ollama]\nignore_missing_imports = True` in a test-local config.
2. OR mark the test with `pytest.importorskip("ollama")` — but that creates a soft Hard-Rule-4a issue; better to fix the type-check scope.
3. Update CONTRIBUTING.md to require `pip install -e .[all]` for full-suite runs if option 1 is rejected.

---

### [TEST-102] — Major — Quality — CHANGELOG test-count claim does not reconcile with observed default-run output

**Evidence**

CHANGELOG.md:16-17 says "Net +88 tests vs v1.0.0 (689 → 777 passing in the default invocation)."

Observed local run on HEAD `de2a7a3` (Python 3.14.3, Windows, no `[ollama]` extra):
- `1 failed, 781 passed, 3 deselected, 2 warnings in 80.87s`
- Total collected: 785

781 + 1 failed = 782 passing-or-failing tests, vs the claimed 777. Even accounting for the failure, the count drifted by 4. The `8 deselected` claim in the audit prompt is also wrong — only 3 are deselected (`cleanroom`, `live`, `live_ollama` markers per `pyproject.toml:86`).

**Why this matters**

Test-count claims in a release CHANGELOG are a small honesty signal. If the repo is meant to be a public open-source project with semver discipline, drifting the claimed count by ~5 within the same release is a cheap fix that prevents a bigger trust loss later.

**Blast radius**
- Adjacent claims: any landing-page / press-kit / discussion-seed text that quotes "777 tests."
- Migration: none. Just a number update.

**Fix path**

Run `pytest --collect-only -q | tail -1` on a clean `[all]` install, capture the exact number, and update CHANGELOG + any other doc surface that quotes a count. The drift gate from CR-04 covers CLI/MCP names but does not yet cover prose numerical claims — out of scope for this finding but worth W-list consideration.

---

### [TEST-103] — Minor — Coverage — No public-API surface freeze test exists

**Evidence**

`grep -rn "compat.freeze\|public_api_surface\|public_surface" tests/` returns only one hit, and it's a docstring reference in `test_mcp_tool_names_documented.py:196`. The CHANGELOG and watchlist talk about "v1.0 compat freeze" as a contract, but there is no test that enumerates the public symbols (e.g. `agentsuite.agents.founder.agent.FounderAgent`, `agentsuite.kernel.qa.QARubric`, `agentsuite.llm.base.LLMProvider`) and pins them.

**Why this matters**

A compat freeze that isn't tested is just an aspiration. A user who pins `agentsuite==1.0.x` expects `from agentsuite.kernel.qa import QARubric` to keep working. A small `test_public_api_surface.py` that imports each documented public symbol and asserts on its callable / class shape would close this. The downstream-consumer test (TEST-101) is close in spirit but fails on environmental issues and is not really a surface enumeration.

**Fix path**

Add a `tests/test_public_api_surface.py` listing the v1.0 public imports as `from agentsuite... import X` plus `assert hasattr(X, ...)` for the methods documented in README. Worth flagging for v1.0.2.

---

### [TEST-104] — Minor — Coverage — CR-04 SVG extractor has a silent false-negative path on renderer changes

**Evidence**

`tests/test_readme_cli_invocations.py:55-56` hardcodes rich's clip-path naming convention:

```python
_SVG_LINE_GROUP_RE = re.compile(r'clip-path="url\(#[^"]*?-line-(\d+)\)"')
```

If a future contributor switches the SVG renderer (e.g., from rich's `Console.save_svg()` to a different terminal-recording tool) or rich changes its clip-path naming, `_iter_svg_invocations()` returns 0 invocations from those SVGs and the test still passes (`test_at_least_one_invocation_documented` only requires non-empty across all sources combined — fenced-code blocks alone keep it green).

**Why this matters**

This is a contained risk: the SVG path is one of three extraction sources, and breaking only the SVG path leaves the prose / fenced-code paths still gating. But the test would silently lose coverage of every screenshot until someone notices.

**Fix path**

Add a sanity check that asserts at least one invocation is extracted *from SVGs specifically* (not just from all sources). One line:

```python
assert any(p.suffix == ".svg" for p, _, _ in documented_invocations), (
    "No invocations extracted from SVG screenshots. The rich clip-path "
    "regex may have drifted."
)
```

---

### [TEST-105] — Nit — Quality — `_TOOL_VERBS` and `_TOOL_AGENTS` lists in the MCP drift gate must hand-track agent registrations

**Evidence**

`tests/test_mcp_tool_names_documented.py:44-67` hardcodes the verb suffix list and agent name list:

```python
_TOOL_VERBS = ("run", "resume", "approve", "list_runs", ...)
_TOOL_AGENTS = ("founder", "design", ..., "trust_risk", "trust-risk", "cio")
```

If a new agent or new tool verb is added without updating these lists, the regex won't match the new tool's documented form and drift won't be caught.

**Why this matters**

Low-impact: the gate produces a false-negative only on freshly added tools. Any drift on an existing tool is still caught. But it's the kind of thing that erodes over 6-12 months.

**Fix path**

Build `_TOOL_VERBS` and `_TOOL_AGENTS` dynamically from the registered tool names instead of hardcoding (split on `agentsuite_<agent>_<verb>` and union). Two-line change.

---

## Shortcut census

| Shortcut pattern | Count | Notes |
|---|---|---|
| `.skip` / `xit` / `@skip` | 0 | Hard Rule 4a still clean. |
| `.only` (left in) | 0 | n/a |
| `TODO: add test` / similar | not surveyed | (out of v101 scope) |
| Empty assertion / placeholder | 0 observed | |
| `--retry` / retries normalized | no | |

## Blind spots by class (v1.0.1 delta)

- **Optional-extra mypy walks** — TEST-101. New surface introduced by the strict-typing test that wasn't there in v1.0.0.
- **Public API symbol freeze** — TEST-103. Claimed contract, no pinning test.
- **SVG-renderer drift** — TEST-104. Single-source coverage loss not detectable.

## Patterns and systemic observations

The v1.0.1 sprint has a clear pattern: "every public claim should have one pinning test." TEST-004 / CR-04 is the gold-standard execution of that pattern — three doc files, inline backticks, fenced blocks, and rendered SVGs are all under one regex-driven gate. TEST-006's windows-smoke step is the same pattern applied to wheel-install behavior.

The compat-freeze claim (TEST-103) is the next obvious application: the team has done the harder work of building the trap mechanism; finishing the surface-enumeration test is a half-day of work and would close the most valuable remaining v1.0.x posture gap.

The CHANGELOG count drift (TEST-102) and the local-suite redness (TEST-101) reinforce a smaller pattern: the team's test runs are now usually on machines with all extras installed, so the "runs cleanly on a fresh contributor checkout" promise is at risk. Worth a CONTRIBUTING.md note + a conftest startup check.

## Appendix: test artifacts reviewed

- `agentsuite/llm/mock.py` — full read.
- `tests/unit/llm/test_mock_matcher.py` — full read; 6 tests, all pass.
- `tests/test_readme_cli_invocations.py` — full read; 3 tests, all pass.
- `tests/test_mcp_tool_names_documented.py` — full read; 2 tests, all pass.
- `tests/integration/test_downstream_consumer.py` — full read; 1 failure (environmental).
- `.github/workflows/release.yml` — full read; YAML + inline Python valid; cannot run locally.
- `dev-reports/audit-AgentSuite-2026-04-29/04-test-deepdive.md` — referenced for v1.0.0 baseline.
- `dev-reports/audit-AgentSuite-2026-04-29/next-sprint-watchlist.md` — confirmed W-01 / W-02 deferral honesty.
- `pyproject.toml:86-89` — confirmed deselect markers (`cleanroom`, `live`, `live_ollama`) = 3, not 8 as the audit prompt suggested.
- Full suite run on HEAD `de2a7a3`: `1 failed, 781 passed, 3 deselected in 80.87s`.
