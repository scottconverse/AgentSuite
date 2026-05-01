# Runtime QA Deep-Dive — AgentSuite v1.0.5

**Audit date:** 2026-04-30
**Role:** QA Engineer
**Scope audited:** CLI entrypoints (`agentsuite`, `agentsuite-mcp`), MCP server, Python SDK kernel, all four provider adapters, install/setup experience, cross-platform concerns, error handling, edge cases, adversarial input
**Environment:** Python 3.14.0, Windows 11 Pro 10.0.26200, AgentSuite v1.0.5 (GitHub source install), Anthropic SDK available, no live API key used for destructive tests (fake key `sk-fake` used to test error flows)
**Auditor posture:** Balanced

---

## TL;DR

AgentSuite v1.0.5 is a structurally solid CLI/SDK. The core pipeline, path-traversal defenses, cost tracking, JSON fence stripping, and stdout/stderr discipline all work correctly. Three issues need attention before the next release: (1) authentication errors from all providers are silently retried up to 3 times before failing, burning ~3–4 seconds and emitting misleading retry warnings to stderr; (2) the README still says v1.0.3 while pyproject and CHANGELOG correctly say v1.0.5 — a first impression problem for every new user arriving via GitHub; and (3) `AGENTSUITE_COST_CAP_USD` accepts a non-float string and raises a raw `ValueError` with no actionable message. No Blockers. The retried-auth issue is the most friction-heavy finding for real users.

## Severity roll-up (QA)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 |
| Major | 4 |
| Minor | 4 |
| Nit | 2 |

## What's working

- **Path-traversal defense is comprehensive.** Tested `run_id = "../../../etc/passwd"`, absolute paths, null bytes, and embedded slashes. All rejected at `validate_run_id()` / `validate_project_slug()` before any I/O, with a human-readable error message that explains the rule. Exit code 1 cleanly. No data written.
- **stdout/stderr discipline is correct.** Verified via subprocess capture: JSON output goes to stdout, progress lines ("Skipping pre-v0.9 run dir …", retry warnings) go to stderr. `list-runs` JSON is pipe-safe.
- **MCP server `--help` / `--version` work correctly.** Prior audit finding QA-101 (FastMCP silently exiting 0) is fixed. `agentsuite-mcp --help` prints a complete, accurate help page including all env vars. `--version` returns `agentsuite-mcp 1.0.5`. Exit 0 in both cases.
- **Approval gate enforces all pre-conditions.** Tested: approve on a non-existent run → `FileNotFoundError` + exit 1; approve on wrong stage → `NotAtApprovalStage` + exit 1; provide neither `--run-id` nor `--latest` → actionable error + exit 1. Each error message tells the user exactly what to do.
- **JSON fence stripping handles the mainstream cases.** Tested: clean JSON, `` ```json … ``` `` fences, single `` ``` `` fences, and leading prose before a JSON object. All parsed correctly.
- **Cost cap enforcement works.** Zero cap rejects even sub-penny costs immediately with `HardCapExceeded`. Default cap ($1.00 soft / $5.00 hard) is sane for a single agent run.
- **Registry AGENTSUITE_ENABLED_AGENTS validation is immediate.** An unknown agent name in the env var is caught at registry lookup time with a message listing all registered agents — not silently ignored.
- **The `agents` command works and is helpful.** Returns separate `enabled` / `all_registered` lists, making it easy to see what the current env var configuration activates.
- **Atomic state writes prevent corruption.** `StateStore.save()` writes to a temp file, fsyncs, then `os.replace()` — a partial write never corrupts the existing state.

## What couldn't be assessed

- **Live provider completions** — No valid API keys were used for destructive tests. Authentication error behavior was observed (see QA-001) but the full LLM round-trip was not exercised in this session. The retry/timeout behavior in successful conditions was not measured.
- **Ollama provider under real daemon** — No Ollama daemon was running. The provider codepath was analyzed statically.
- **`agentsuite-mcp` under an actual MCP host (Codex, Claude Code, Cowork)** — Verified that the server starts, that tools register, and that `--help`/`--version` work. Full tool invocation through the MCP protocol was not tested in this session.
- **Windows console UTF-8 edge cases beyond what was tested** — `_force_utf8_io()` was confirmed present; the actual reconfigure call was not stress-tested across all Windows terminal emulators.
- **Gemini and OpenAI providers under real API responses** — Analyzed statically. The Gemini `model` provenance issue (QA-004) was confirmed by code inspection, not by live call.
- **Cleanroom E2E smoke test** — Not run in this audit session. The test suite was not executed; see the Test Engineer's report for that coverage.

---

## Product shape

AgentSuite is a CLI tool and Python SDK with a secondary MCP server interface. QA focused on: the install path (first-run experience from README), the full CLI user journey (run → review → approve), error handling for every failure mode reachable from the CLI, adversarial input testing (path traversal, invalid env vars, empty inputs, malformed cost caps), the MCP server startup surface, and cross-platform concerns (Windows codepage, stdout/stderr routing).

## Flows exercised

| Flow | Result | Findings |
|---|---|---|
| `agentsuite --help` | Pass | — |
| `agentsuite founder run --help` | Pass | — |
| `agentsuite founder approve --help` | Pass | — |
| `agentsuite agents` (default env) | Pass | — |
| `agentsuite agents` (bad AGENTSUITE_ENABLED_AGENTS) | Partial — unhandled exception surfaced but exit 1 is correct | QA-005 |
| `agentsuite list-runs` (no runs dir) | Pass — returns `[]` | — |
| `agentsuite list-runs` (with pre-v0.9 dirs) | Pass — warnings to stderr, JSON to stdout | — |
| `agentsuite founder approve --run-id nonexistent` | Pass — clean error, exit 1 | — |
| `agentsuite founder approve` (neither flag) | Pass — actionable error, exit 1 | — |
| `agentsuite founder run --business-goal "test"` (fake key) | Partial — retries 3x before failing; exit 1 | QA-001 |
| `agentsuite-mcp --help` | Pass | — |
| `agentsuite-mcp --version` | Pass | — |
| `agentsuite-mcp` (bad AGENTSUITE_ENABLED_AGENTS) | Partial — unhandled exception, exit 1 | QA-005 |
| Path-traversal run_id in approve | Pass — rejected pre-I/O | — |
| Path-traversal run_id in ArtifactWriter | Pass — rejected at construction | — |
| First-run README install flow | Partial — README version stale | QA-002 |
| AGENTSUITE_COST_CAP_USD = "not_a_float" | Fail — raw ValueError, no exit code | QA-003 |

## Adversarial scenarios exercised

| Scenario | Outcome | Findings |
|---|---|---|
| `run_id = "../../../etc/passwd"` | Rejected with clean error at `validate_run_id` | — |
| `run_id = "/etc/passwd"` (absolute path) | Rejected — first char `/` not in allowed set | — |
| `run_id` containing null byte | Rejected — regex rejects non-ASCII | — |
| `project_slug` with path traversal | Rejected by `validate_project_slug` | — |
| `AGENTSUITE_ENABLED_AGENTS = "unknown_agent"` | Exception raised with full registered list; exit 1 | QA-005 |
| `AGENTSUITE_COST_CAP_USD = "not_a_float"` | `ValueError: could not convert string to float` — no user-friendly message, no exit code | QA-003 |
| `AGENTSUITE_COST_CAP_USD = "0"` (zero cap) | Accepted; any cost immediately raises `HardCapExceeded` — correct behavior | — |
| `business_goal = ""` (empty string) | Accepted by Pydantic — no length validation | QA-006 |
| LLM response with mixed prose + JSON with braces in prose | `extract_json` fails: greedy `find('{')` + `rfind('}')` extracts `{key} is {value}. Now: {"a": 1}` which is not valid JSON | QA-007 |
| Fake API key (sk-fake) | Retried 3x before failing — auth error not in no-retry list | QA-001 |
| `agentsuite-mcp` with no MCP package | Clean `ImportError` with actionable install command | — |
| ArtifactWriter with escaping path component | Caught by `_resolve_safe` — second layer of defense | — |
| Approve a run at wrong stage | `NotAtApprovalStage` raised, caught, friendly error, exit 1 | — |
| Approve a run with `requires_revision=True` | `RevisionRequired` raised — see QA-008 for UX issue | QA-008 |

---

## Findings

> **Finding ID prefix:** `QA-`
> **Categories:** Flow / API / Security / Performance / Browser / Mobile / Console / Protocol / Install / Auth

---

### QA-001 — Critical — Auth — Authentication errors are silently retried before failing

**Evidence**

1. Install AgentSuite with `pip install "agentsuite[anthropic] @ git+…"`.
2. Export a bad key: `export ANTHROPIC_API_KEY=sk-fake`.
3. Run: `agentsuite founder run --business-goal "test"`.
4. Observe: the CLI prints `[OK] intake complete (0.0s, $0.0000)` to stderr (intake is a no-LLM stage, so it succeeds). Then, when extract stage calls the LLM, tenacity logs to stderr:
   ```
   Retrying <unknown> in 1 seconds as it raised AuthenticationError: Error code: 401…
   Retrying <unknown> in 2 seconds as it raised AuthenticationError: Error code: 401…
   ```
   After ~3 seconds, the full traceback is shown and the process exits 1.
5. Environment: Windows 11, Python 3.14, Anthropic SDK latest.

**Observed:** Auth errors (401) are retried 3 times (default `AGENTSUITE_LLM_MAX_ATTEMPTS=3`) with 1s + 2s backoff before the command finally fails. The "Retrying" messages appear to the user alongside the misleading message "Retrying … as it raised AuthenticationError."

**Expected:** A 401 authentication error is not transient. It should fail immediately with a human-readable message: "Authentication failed: ANTHROPIC_API_KEY is invalid or expired." No retry should occur.

**Why this matters**

This is the first error a new user is likely to hit after installing. A typo in the API key — or a key that's been rotated — produces a confusing 3-second wait with "Retrying" messages before failing. The user sees output that implies the system is attempting recovery, when in fact no recovery is possible. The same behavior applies to all three cloud providers (Anthropic `AuthenticationError`, OpenAI `AuthenticationError`, Gemini auth errors).

**Blast radius**
- Adjacent code: `agentsuite/llm/retry.py:_NO_RETRY_EXCEPTIONS` — add provider auth exception types here. Must import lazily or use a base-class check to avoid hard-wiring provider SDK imports in the retry module. `agentsuite/llm/anthropic.py`, `agentsuite/llm/openai.py`, `agentsuite/llm/gemini.py` are the call sites whose exception types must be excluded.
- User-facing: affects all three cloud providers on first run with an invalid key; affects every retry-triggered LLM failure path.
- Tests to update: `tests/unit/llm/test_retry.py` — add a test that `RetryingLLMProvider` does not retry when the inner provider raises an `AuthenticationError`-shaped exception. Currently this case is unexercised.
- Related findings: QA-003 (env var validation gaps — same "bad config fails loudly" theme).

**Fix path**

In `agentsuite/llm/retry.py`, extend `_NO_RETRY_EXCEPTIONS` to include the auth-error base classes from each provider SDK. Because provider SDKs are optional extras, import them lazily inside a helper that builds the tuple at `RetryingLLMProvider.__init__` time (or cache it at module level using a try/except import block). Alternatively, check the HTTP status code or exception message in a custom `retry_if` predicate that treats 401/403 as non-retriable.

---

### QA-002 — Major — Install — README version says v1.0.3 while package is v1.0.5

**Evidence**

1. Open the GitHub repository or run `cat README.md | head -5`.
2. First heading after the title: `**v1.0.3** — Specification Kernel + Founder · Design…`
3. `pyproject.toml` says `version = "1.0.5"`.
4. `agentsuite/__version__.py` says `__version__ = "1.0.5"`.
5. `CHANGELOG.md` correctly opens with `## [1.0.5]`.

**Observed:** The badge / version announcement in README.md was not updated when the version was bumped from 1.0.3 to 1.0.5. The README is the first thing a new user reads.

**Expected:** The version in README.md matches `pyproject.toml` and `__version__.py`.

**Why this matters**

New users (and anyone reviewing the GitHub landing page) see v1.0.3 and may believe they are installing an older version or that the repo is stale. Support questions about "I installed v1.0.3 but `--version` says 1.0.5" are likely.

**Blast radius**
- Adjacent code: `docs/index.html` (landing page) and `USER-MANUAL.md` may also contain stale version strings — sweep all doc artifacts.
- User-facing: every new user arriving at GitHub sees incorrect version.
- Migration: none — pure doc update.
- Tests to update: `scripts/verify-release.sh` apparently did not catch this; consider adding a `grep` check that all version-bearing files agree.
- Related findings: QA-003 (env var invalid values), QA-009-nit (version stamp in help text).

**Fix path**

Update `README.md` line ~6: change `**v1.0.3**` to `**v1.0.5**`. Run a repo-wide version audit (`grep -r "1\.0\.[0-9]"`) to catch any other stale references. Add a step to `scripts/verify-release.sh` that greps all version-bearing files and asserts they agree.

---

### QA-003 — Major — Flow — `AGENTSUITE_COST_CAP_USD` with non-float value raises raw `ValueError` with no actionable guidance

**Evidence**

1. `export AGENTSUITE_COST_CAP_USD=fifty-dollars`
2. Run any agent: `agentsuite founder run --business-goal "test"`
3. The `CostCap.from_env()` call is made in `CostTracker.__init__()`, which is called inside `_drive()` after the agent is already running.
4. Output:
   ```
   [OK] intake complete  (0.0s, $0.0000)
   Error: could not convert string to float: 'fifty-dollars'
   ```
   Exit code 1.

**Observed:** The error message tells the developer *what* failed (the Python float conversion) but not *where* or *how to fix it*. There is no mention of `AGENTSUITE_COST_CAP_USD`. An operator who set this env var days ago will not associate this error with that setting.

**Expected:** `Error: AGENTSUITE_COST_CAP_USD='fifty-dollars' is not a valid number. Set it to a dollar amount, e.g. AGENTSUITE_COST_CAP_USD=10.00`

**Why this matters**

This env var is surfaced as a cost-control mechanism for operators deploying AgentSuite in automation. An invalid value causes the agent to start (waste tokens on intake), then fail mid-run on the first LLM stage. The operator has no direct indication which env var is responsible.

**Blast radius**
- Adjacent code: `agentsuite/kernel/cost.py:CostCap.from_env()` — one-line fix; add a `try/except` around `float(raw)` and raise a `ValueError` with an actionable message naming the env var.
- User-facing: any operator using `AGENTSUITE_COST_CAP_USD` automation.
- Tests to update: `tests/unit/kernel/test_cost.py` — add a case for `CostCap.from_env()` with an invalid string.
- Related findings: QA-001 (bad env var → poor UX), QA-006 (missing input validation).

**Fix path**

In `CostCap.from_env()`, wrap `float(raw)` in a try/except and re-raise with: `ValueError(f"AGENTSUITE_COST_CAP_USD={raw!r} is not a valid dollar amount. Set it to a number, e.g. '10.00'.")`. Consider also validating early at CLI startup rather than lazily inside `_drive()`.

---

### QA-004 — Major — Flow — Gemini provider reports input model name, not actual API-returned model name

**Evidence**

1. Code inspection of `agentsuite/llm/gemini.py:GeminiProvider.complete()`:
   ```python
   model = request.model or self.default_model()
   # ... API call ...
   return LLMResponse(
       text=text,
       model=model,          # <-- uses the REQUEST model, not result.model
       ...
   )
   ```
2. Compare with Anthropic and OpenAI providers, which correctly return `result.model` (the SDK's actual model id returned by the API, including version date suffix):
   - `AnthropicProvider`: `model=result.model`
   - `OpenAIProvider`: `model=result.model`
   - `GeminiProvider`: `model=model` (the pre-call local variable)
3. The Gemini SDK does not expose a `result.model` field in a comparable way, but it does expose `model` via the `GenerateContentResponse` object in some SDK versions.

**Observed:** Gemini `cost_summary.json` always records the model name that was requested (e.g. `"gemini-2.5-flash"`), which may not match the model id the API actually used (e.g. `"gemini-2.5-flash-001"` or a different version). Anthropic's prior fix (ENG-002) that addressed this same class of bug for the Anthropic provider was not applied to Gemini.

**Expected:** `LLMResponse.model` reflects what the API actually ran, for accurate cost tracking and audit trails.

**Why this matters**

If the Gemini API serves a different model variant than requested (e.g. an alias like `gemini-2.5-flash` resolves to `gemini-2.5-flash-exp`), the cost summary silently logs the alias instead of the actual model. The pricing lookup will still work (the alias is in the pricing table), but the `cost_summary.json` artifact is not a reliable audit record.

**Blast radius**
- Adjacent code: `agentsuite/llm/gemini.py` — single-file fix. Check whether `result` from `client.models.generate_content()` exposes a model attribute; if so, use it with a fallback to the request model.
- Shared state: `cost_summary.json` written per run — existing run summaries in Gemini runs are unreliable for model provenance.
- User-facing: Gemini users see potentially inaccurate model names in `cost_summary.json`.
- Tests to update: `tests/unit/llm/test_gemini.py` — add a test that `LLMResponse.model` from `GeminiProvider.complete()` reflects the API-returned model, not just the request model.
- Related findings: Shares root cause class with ENG-002.

**Fix path**

In `GeminiProvider.complete()`, attempt to read the actual model from the response object. The google-genai SDK's `GenerateContentResponse` has a `model_version` field in some versions. Use it if present, otherwise fall back to `model` (the request value). Pattern: `model=getattr(result, 'model_version', None) or model`.

---

### QA-005 — Major — Flow — `AGENTSUITE_ENABLED_AGENTS` misconfiguration raises unhandled exception traceback from both CLI `agents` command and MCP server

**Evidence**

**CLI test:**
1. `export AGENTSUITE_ENABLED_AGENTS=bad_agent`
2. `agentsuite agents`
3. Output: Full Typer-formatted Python traceback (14 lines including file paths), ending in `UnknownAgent: "Unknown agents in AGENTSUITE_ENABLED_AGENTS: ['bad_agent']…"`. Exit 1.

**MCP server test:**
1. `export AGENTSUITE_ENABLED_AGENTS=bad_agent`
2. `agentsuite-mcp` (no flags)
3. Output: Unformatted Python traceback to stderr, ending in `agentsuite.agents.registry.UnknownAgent: "Unknown agents…"`. Exit 1.

**Observed:** Both surfaces produce raw Python tracebacks. The error content is correct (names the bad agent, lists registered agents), but the presentation is developer-grade noise rather than operator-grade guidance.

**Expected:**
- CLI: `Error: AGENTSUITE_ENABLED_AGENTS contains unknown agent 'bad_agent'. Known agents: cio, design, engineering, founder, marketing, product, trust_risk.` (exit 1)
- MCP server: same message on stderr, then exit 1. MCP hosts (Codex, Claude Code) read this and display it to the user.

**Why this matters**

MCP wiring often involves setting env vars in a config file (`.mcp.json`, `~/.codex/mcp.toml`). A typo like `trust-risk` vs `trust_risk` (the README normalizes but if a user copies from the wrong place) will cause the server to crash with a traceback rather than an actionable error. The traceback may be invisible in some MCP host UIs.

Note: the normalization from hyphen to underscore in `registry.py:enabled_names()` handles the `trust-risk` → `trust_risk` case correctly — this is about any genuinely unknown name.

**Blast radius**
- Adjacent code: `agentsuite/agents/registry.py:enabled_names()` raises `UnknownAgent`; neither `agentsuite/cli.py:agents_cmd()` nor `agentsuite/mcp_server.py:build_server()` catches it.
- User-facing: any MCP integrator who misconfigures `AGENTSUITE_ENABLED_AGENTS`.
- Tests to update: add a test for `agentsuite_cli.agents_cmd()` with a bad env var that asserts the error is caught and exits 1 cleanly.
- Related findings: QA-003 (env var validation UX).

**Fix path**

In `cli.py:agents_cmd()`, wrap the `reg.enabled_names()` call in a try/except for `UnknownAgent`; emit a `typer.echo(f"Error: {e}", err=True)` and `raise typer.Exit(1)`. In `mcp_server.py:main()`, wrap `build_server()` in a try/except for `UnknownAgent` (and general `Exception`) and write a clean message to stderr before exiting 1.

---

### QA-006 — Minor — Flow — Empty `business_goal` is accepted and produces an empty-prompt run

**Evidence**

1. `from agentsuite.agents.founder.input_schema import FounderAgentInput`
2. `inp = FounderAgentInput(agent_name="founder", role_domain="test", user_request="test", business_goal="")`
3. No exception raised. `inp.business_goal == ""`.
4. CLI: `agentsuite founder run --business-goal ""` — passes validation and attempts to run the agent.

**Observed:** An empty string is a valid `business_goal`. The extract stage will generate a prompt with an empty business goal, wasting LLM tokens producing artifacts based on nothing.

**Expected:** `business_goal` should require at least 1 non-whitespace character. Pydantic `Field(min_length=1)` would be sufficient.

**Why this matters**

Affects any caller (CLI or SDK) that passes an empty or whitespace-only goal. The agent runs to completion (spending money) and produces an artifact whose quality is undefined. Less severe because it requires user error to trigger.

**Fix path**

In `FounderAgentInput`, change `business_goal: str` to `business_goal: str = Field(min_length=1)`. Apply the same pattern to the other agents' required input fields. Check whether `AgentRequest.user_request` has the same issue.

---

### QA-007 — Minor — Flow — `extract_json` greedy `{`…`}` fallback fails when LLM response contains curly braces in prose before the real JSON

**Evidence**

```python
from agentsuite.llm.json_extract import extract_json
# Prose containing curly braces before the real JSON:
text = 'The {key} is {value}. Now: {"a": 1}'
extract_json(text)
# Raises:
# ValueError: LLM response is not valid JSON even after stripping fences/prose.
# First 200 chars: 'The {key} is {value}. Now: {"a": 1}'
```

**Root cause:** The fallback in `extract_json` uses `text.find('{')` (first `{`) and `text.rfind('}')` (last `}`). When prose contains single-brace characters before the JSON object, the slice is `{key} is {value}. Now: {"a": 1}` — which is not valid JSON. The `{"a": 1}` object is present but unreachable.

**Observed:** `ValueError` raised. The failure does not occur with the primary code path (fence-stripped clean JSON) or with a single leading line of prose that contains no `{` characters.

**Expected:** `extract_json` returns `{"a": 1}`.

**Why this matters**

LLMs sometimes narrate before returning JSON, using template-style syntax like "The {dimension} score is {value}" in their thinking. If this pattern appears in a stage response, the entire stage fails rather than gracefully degrading. The `spec` stage (which produces 9 artifacts from a JSON blob) is most at risk.

**Fix path**

Replace the `find('{')` + `rfind('}')` approach with a scan that finds the *last* `{` before the closing `}` that forms a valid JSON object, or use `json.JSONDecoder().raw_decode()` which finds the first decodable JSON value at each `{` position. A simple fix: scan rightward from index 0, skip any `{` that produces a `JSONDecodeError`, and try the next one.

---

### QA-008 — Minor — Flow — `RevisionRequired` error from `approve` does not tell the user what the revision instructions are

**Evidence**

1. Create a run where QA scoring produces `requires_revision=True`.
2. Run `agentsuite founder approve --run-id <id> --approver test --project-slug test`.
3. Output: `Error: QA flagged this run as requiring revision. Address the QA feedback and re-run before approving.`
4. The `qa_report.md` artifact exists in the run directory but is not referenced in the error message.

**Observed:** The error is actionable in principle ("review QA feedback"), but does not point to where the feedback lives. The user must know the run directory path independently.

**Expected:** `Error: QA flagged this run as requiring revision. Review qa_report.md at: .agentsuite/runs/<run-id>/qa_report.md` — with the actual path interpolated.

**Why this matters**

This is the most likely approval-gate failure for a real run. Without a pointer to the report, the user has to know where run artifacts live (not obvious from the `--help` output). Minor because the project slug and run ID are known from prior output, and the path is inferrable, but it costs friction.

**Fix path**

In `ApprovalGate.approve()`, when raising `RevisionRequired`, interpolate the `qa_report.md` path: `run_dir = self.writer.run_dir / "qa_report.md"`. In `cli.py`, `RevisionRequired` is caught by the broad `except Exception` and printed via `str(exc)` — so the fix is in the exception message itself in `approval.py`.

---

### QA-009 (Nit) — Install — `agentsuite-mcp --help` lists `trust_risk` with underscore; README and MCP config snippets use `trust-risk` with hyphen

**Evidence**

`agentsuite-mcp --help`:
```
  AGENTSUITE_ENABLED_AGENTS    … allowed: founder, design,
                                product, engineering, marketing, trust_risk, cio
```

README quick-start MCP config:
```toml
AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust-risk,cio"
```

The normalization in `registry.py:enabled_names()` handles this correctly (both forms work). But the `--help` output and the README inconsistency will cause first-time readers to wonder if `trust_risk` and `trust-risk` are different things.

**Fix path**

Decide on a canonical form for user-facing documentation. The hyphen form (`trust-risk`) is more readable and already used in the README. Update `agentsuite-mcp --help` to list it as `trust-risk`. The underscore normalization in the registry can stay.

---

### QA-010 (Nit) — Install — `agentsuite founder run` help text references `_kernel/` without explaining the concept

**Evidence**

`agentsuite founder run --help`:
```
  --project-slug  TEXT  Stable slug for `_kernel/` promotion
```

The term `_kernel/` is unexplained for a first-time user.

**Fix path**

Change to: `Stable slug for artifact promotion (e.g. "my-app"); approved artifacts go to .agentsuite/_kernel/<slug>/`

---

## Performance snapshot

| Metric | Observed | Benchmark | Verdict |
|---|---|---|---|
| CLI cold-start (`agentsuite --help`) | ~0.6s | <1s for CLI tools | Pass |
| CLI cold-start (`agentsuite founder run --help`) | ~0.8s | <1s | Pass |
| Auth-fail delay (fake key, 3 retries) | ~3s | Should be ~0s (no retry) | Fail — QA-001 |
| `agentsuite-mcp --help` | ~0.5s | <1s | Pass |
| State file atomic write (temp+fsync+replace) | Not measured directly; implementation correct | — | — |

CLI startup is within acceptable bounds for a developer tool. The ~0.6–0.8s cold start includes importing all seven agent modules at CLI registration time (`_register_agents()` runs all `build_cli_spec()` calls unconditionally). This is currently acceptable but may become a concern as more agents are added.

## Security / privacy snapshot

- **Path traversal: closed.** Both `validate_run_id` and `validate_project_slug` are wired at every path-construction boundary. `ArtifactWriter._resolve_safe()` adds a second layer. Tested with `../..`, absolute paths, null bytes — all rejected cleanly.
- **No secrets in client code or artifacts.** Confirmed: no API keys committed, `.gitignore` covers `.env` and credential files, `cost_summary.json` contains no secrets.
- **MCP server exposes no unauthenticated write surface beyond what is intended.** The `founder_run` tool accepts a `run_id` field from the MCP caller — this is validated by `validate_run_id`. Path traversal via MCP is blocked.
- **`RevisionRequired` enforcement is correct.** The approval gate refuses to promote artifacts when `requires_revision=True`, and this check cannot be bypassed via the CLI (it's in `ApprovalGate.approve()`, not in the CLI handler).
- **No SSRF surface identified.** The only outbound network calls are to provider APIs (Anthropic, OpenAI, Gemini) using official SDKs. URLs are not constructed from user input. Ollama probe is fixed to `localhost:11434`.

## Console and log observations

- `stderr` is used correctly throughout for warnings, progress lines, and skip-notices. `stdout` carries only structured JSON output. Verified by subprocess capture.
- The `tenacity` retry warnings (`Retrying <unknown> in N seconds`) include `<unknown>` as the function name because tenacity is used in a for-loop context rather than a decorator context. The function name is absent. This is a cosmetic issue with the retry log format but does not affect functionality.
- `_force_utf8_io()` is called at module import time and suppresses encoding errors gracefully. The Windows cp1252 console encoding issue that would affect em-dash characters in help text is pre-empted.

## Patterns and systemic observations

1. **Env var validation is lazy.** `AGENTSUITE_COST_CAP_USD` (QA-003) and `AGENTSUITE_ENABLED_AGENTS` (QA-005) are validated at first use, not at startup. This means the CLI can partially succeed (e.g. complete intake) before hitting the invalid config error. A validation pass at startup would improve operator experience for both the CLI and MCP server.

2. **Auth errors as a retry-eligible class is a systemic gap.** The `RetryingLLMProvider._NO_RETRY_EXCEPTIONS` tuple includes `ProviderNotInstalled`, `KeyboardInterrupt`, `SystemExit` — but no provider's auth error type. This is a pattern gap, not a one-off oversight. All three cloud providers share this exposure (QA-001).

3. **Input validation is absent on free-text fields.** `business_goal`, `user_request`, `role_domain` have no length limits, no non-empty enforcement (except where overridden in subclasses). A 100KB business_goal passed via CLI would silently generate an enormous LLM prompt that exceeds `max_tokens`. Consider adding `max_length` constraints or prompt truncation.

4. **The README version drift (QA-002) suggests the release checklist's version-bump step does not cover all files.** The `scripts/verify-release.sh` presumably checks some version locations but missed the README header badge. This is a process gap as much as a content gap.

---

## Appendix: environments and artifacts

**OS:** Windows 11 Pro 10.0.26200
**Python:** 3.14.0 (pythoncore-3.14-64)
**Shell:** bash (Git Bash)
**AgentSuite version:** 1.0.5 (installed from source in working directory)
**Provider SDKs available:** anthropic (installed), mcp (installed), ollama (not installed)
**Live API calls made:** None (fake key `sk-fake` used for error-flow testing only)
**Tools used:** Python subprocess, Bash, static code inspection via Read/Grep

**Files read during this audit:**
- `agentsuite/cli.py`
- `agentsuite/mcp_server.py`
- `agentsuite/kernel/base_agent.py`
- `agentsuite/kernel/artifacts.py`
- `agentsuite/kernel/cost.py`
- `agentsuite/kernel/schema.py`
- `agentsuite/kernel/state_store.py`
- `agentsuite/kernel/approval.py`
- `agentsuite/kernel/identifiers.py`
- `agentsuite/kernel/qa.py`
- `agentsuite/llm/base.py`
- `agentsuite/llm/resolver.py`
- `agentsuite/llm/retry.py`
- `agentsuite/llm/anthropic.py`
- `agentsuite/llm/openai.py`
- `agentsuite/llm/gemini.py`
- `agentsuite/llm/ollama.py`
- `agentsuite/llm/pricing.py`
- `agentsuite/llm/json_extract.py`
- `agentsuite/agents/registry.py`
- `agentsuite/agents/_common.py`
- `agentsuite/agents/founder/agent.py`
- `agentsuite/agents/founder/input_schema.py`
- `agentsuite/agents/founder/mcp_tools.py`
- `agentsuite/agents/founder/stages/intake.py`
- `agentsuite/agents/founder/stages/extract.py`
- `agentsuite/agents/founder/stages/execute.py`
- `agentsuite/agents/founder/stages/qa.py`
- `agentsuite/mcp_models.py`
- `pyproject.toml`
- `README.md` (first 100 lines)
- Reference files: `qa-engineer.md`, `severity-framework.md`, `blast-radius.md`, `05-qa-deepdive.md` (template)
