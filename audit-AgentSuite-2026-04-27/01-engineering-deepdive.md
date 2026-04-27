# Engineering Deep-Dive — AgentSuite

**Auditor:** Principal Engineer
**Date:** 2026-04-27
**Scope:** Full codebase — architecture, correctness, security, dependencies, performance

---

## Executive Summary

AgentSuite v0.7.0 is structurally sound: the 5-stage kernel pipeline is correctly abstracted in `BaseAgent`, all 7 agents subclass it uniformly, Jinja2 uses `StrictUndefined` throughout, and the cost-cap, state-persistence, and approval-gate subsystems are well-designed. However, three production-quality gaps exist. First, the consistency-check JSON schema is **split across two incompatible shapes** — Founder and Design expect `"mismatches"` while the five newer agents expect `"checks"` — meaning any LLM that follows one agent's prompt format will silently bypass the critical-failure gate in the other. Second, the **OpenAI default model is set to `"gpt-5"`**, a model that does not exist as of this audit date; any user without an explicit `model` override will receive a 404 from the OpenAI API on every call. Third, `AGENTSUITE_COST_CAP_USD` is parsed with a bare `float()` that raises `ValueError` on malformed input instead of a safe parse with a clear error message. Several additional major and minor issues are documented below. No secrets are hardcoded. Version numbers are consistent across all six checked locations.

---

## What's Working Well

1. **Pipeline architecture is clean and consistent across all 7 agents.** Every agent correctly subclasses `BaseAgent`, returns a `dict[str, StageHandler]` with all five stages keyed to `PIPELINE_ORDER`, and the `_wrap()` closure correctly re-validates inputs after JSON round-trip via `model_validate(state.inputs.model_dump())`. The Design/Product/Engineering/TrustRisk/CIO agents go one step further and also check for a pre-validated `edits["inputs"]` on resume — a defensive improvement over the Founder reference implementation.

2. **Jinja2 is configured with `StrictUndefined` everywhere.** Both `prompt_loader.py` and `template_loader.py` in every agent instantiate their `Environment` with `undefined=StrictUndefined`. This means any template variable mismatch raises `UndefinedError` immediately rather than rendering silently as an empty string — the correct production posture.

3. **State persistence and cost tracking are correct.** `RunState` is `model_dump_json`/`model_validate_json` round-tripped safely. `CostTracker` enforces hard cap with exclusive boundary semantics (equal is accepted, greater raises). `ArtifactWriter` is content-addressed with SHA-256 and idempotent on overwrite. `ApprovalGate` correctly guards against calling `approve()` from a non-`approval` stage. These subsystems have no correctness bugs.

4. **No secrets in committed code.** All API keys are read from environment variables. The resolver surfaces clear, actionable error messages when keys are missing. No credentials appear in any source file, config file, or CLAUDE.md.

5. **QA rubric scoring logic is correct.** `QARubric.score()` performs weighted-average scoring, validates both missing and unknown dimensions, computes `passed = average >= pass_threshold`, and populates `requires_revision` correctly. The `pass_threshold=7.0` is consistent across all 7 rubrics.

6. **Rubric dimension counts are exactly 9/9/9/9/9/7/9** (Founder is the exception at 7, not 9). See Major finding M-001.

---

## Findings

### Blockers

#### B-001 — Inconsistent consistency-check JSON schema: `"mismatches"` vs `"checks"` splits the critical-failure gate across agents

**Evidence:**
- `agentsuite/agents/founder/stages/spec.py:118` — `critical = [m for m in report.get("mismatches", []) if m.get("severity") == "critical"]`
- `agentsuite/agents/design/stages/spec.py:154` — same, uses `"mismatches"`
- `agentsuite/agents/founder/prompts/consistency_check.jinja2:12` — instructs LLM to return `{"mismatches": [...]}`
- `agentsuite/agents/design/prompts/consistency_check.jinja2:19` — same
- `agentsuite/agents/engineering/stages/spec.py:116` — `critical = [c for c in report.get("checks", []) if c.get("severity") == "critical"]`
- `agentsuite/agents/marketing/stages/spec.py:101` — same, uses `"checks"`
- `agentsuite/agents/product/stages/spec.py:115` — same, uses `"checks"`
- `agentsuite/agents/trust_risk/stages/spec.py:101` — same, uses `"checks"`
- `agentsuite/agents/cio/stages/spec.py:101` — same, uses `"checks"`
- Mock LLM (`agentsuite/llm/mock.py:90`) returns `{"mismatches": []}` — so `"checks"`-based agents always get an empty list and the critical gate silently passes even when the mock is keyed to return critical findings.

**Blast radius:** Every spec stage consistency check for 5 of 7 agents. If an LLM follows the prompt format for the founder/design agents, it returns `"mismatches"` — the `"checks"`-based agents will call `.get("checks", [])` and get `[]`, so `ConsistencyCheckFailed` is **never raised**, even on genuinely critical mismatches. The gate is silently bypassed.

**Fix path:** Standardize on a single JSON envelope (recommend `"mismatches"` since it's the older/reference shape). Update all 5 newer agent prompts and stage files. Update the mock to match. Add a test that asserts `ConsistencyCheckFailed` is raised when the LLM returns a critical entry.

---

#### B-002 — OpenAI default model is `"gpt-5"`, which does not exist

**Evidence:**
- `agentsuite/llm/openai.py:27` — `return "gpt-5"`
- `agentsuite/llm/pricing.py:20` — `"gpt-5": {"in": 5.0, "out": 15.0}`

**Blast radius:** Any user who sets `AGENTSUITE_LLM_PROVIDER=openai` (or has `OPENAI_API_KEY` set without an Anthropic key and openai is auto-detected) will get a model-not-found error from the OpenAI API on every LLM call. This is a hard runtime crash at first use.

**Fix path:** Change `default_model()` to `"gpt-4.1"` or `"gpt-4o"` — an actual available model. The pricing table already has `"gpt-4.1"` priced correctly.

---

### Critical

#### C-001 — `AGENTSUITE_COST_CAP_USD` crashes with `ValueError` on malformed input

**Evidence:**
- `agentsuite/kernel/cost.py:27` — `hard = float(raw)`
- If `AGENTSUITE_COST_CAP_USD=foo` (typo, stray shell variable, etc.), `float("foo")` raises `ValueError` with a Python traceback, not a user-actionable error.

**Blast radius:** Any user who sets the env var incorrectly gets an unhandled exception at agent startup — not at the LLM call, but at `CostCap.from_env()` which is called from `CostTracker.__init__`, which is called from `_drive()`. The error surface is confusing.

**Fix path:**
```python
try:
    hard = float(raw)
except ValueError:
    raise ValueError(
        f"AGENTSUITE_COST_CAP_USD must be a number; got '{raw}'"
    ) from None
```

---

#### C-002 — No path traversal guard in `ArtifactWriter.write()`

**Evidence:**
- `agentsuite/kernel/artifacts.py:51-52`:
  ```python
  full = self.run_dir / relative_path
  full.parent.mkdir(parents=True, exist_ok=True)
  ```
- `relative_path` is caller-supplied. If any stage handler (or a future MCP-exposed endpoint) passes `"../../etc/passwd"` or `"../other_run/spec.md"`, the writer will silently write outside `run_dir`.

**Blast radius:** Currently all callers are internal and use literal strings — no active exploit path. But the MCP tool surface (`mcp_tools.py` exists in all 7 agents) could expose this to external callers. As the public MCP API surface grows, this becomes a real path-traversal vector.

**Fix path:** Add a guard after constructing `full`:
```python
full = (self.run_dir / relative_path).resolve()
if not str(full).startswith(str(self.run_dir.resolve())):
    raise ValueError(f"Artifact path escapes run_dir: {relative_path}")
```

---

#### C-003 — Founder rubric has only 7 dimensions, not 9

**Evidence:**
- `agentsuite/agents/founder/rubric.py` — 7 `RubricDimension` entries: `reusability`, `brand_consistency`, `claims_grounded`, `voice_fit`, `template_specificity`, `goal_alignment`, `anti_genericity`.
- All other 6 agents have exactly 9 dimensions.
- The audit spec states expected shape is `9/8/9` — but actual shape is `7/9/9/9/9/9/9`.

**Blast radius:** The Founder agent's QA pass threshold of 7.0 is out of 10.0 scale, which still works numerically. But the rubric covers 2 fewer quality dimensions than all other agents, creating an inconsistent quality standard. A founder run that passes QA has been evaluated on fewer axes than a design or product run.

**Fix path:** Add the two missing dimensions that the founder spec implies but the rubric omits — likely `"constraint_adherence"` (legal/brand constraints from Constraints model) and `"completeness"` (all 9 spec artifacts present and substantive). Update tests that snapshot the rubric.

---

### Major

#### M-001 — `pyproject.toml` package-data missing 5 agent template/prompt directories

**Evidence:**
- `pyproject.toml` `[tool.setuptools.package-data]` lists: `founder`, `design`, `engineering`, `marketing`, `trust_risk`, `kernel` — but **omits `product` and `cio`**.
- `agentsuite.agents.product` and `agentsuite.agents.cio` both have `prompts/` and `templates/` directories containing Jinja2 templates that are required at runtime.

**Blast radius:** When AgentSuite is installed from the wheel/sdist (as opposed to an editable install), the Product and CIO agent prompt and template files will not be included in the distribution. Any call to `render_prompt()` or `render_template()` for those agents will raise `UnknownPrompt` / `UnknownTemplate` / `TemplateNotFound` — a hard crash on first real use post-install.

**Fix path:** Add to `pyproject.toml`:
```toml
"agentsuite.agents.product" = ["prompts/*.jinja2", "templates/*.md"]
"agentsuite.agents.cio" = ["prompts/*.jinja2", "templates/*.md"]
```

---

#### M-002 — `CostTracker` is created fresh per `_drive()` call but is never surfaced to the caller if a stage raises mid-pipeline

**Evidence:**
- `agentsuite/kernel/base_agent.py:89` — `cost_tracker = CostTracker()` created inside `_drive()`
- If any stage raises (e.g., `ConsistencyCheckFailed`, `ValueError` from JSON parse), the accumulated cost up to that point is lost — not saved to `RunState`, not propagated in the exception.
- `RunState.cost_so_far` is only updated after a successful stage completes (line 97: `state.cost_so_far = cost_tracker.total`).

**Blast radius:** A run that processes 8 of 9 spec artifacts before the consistency check raises `ConsistencyCheckFailed` will have spent real money on 8+ LLM calls, but `RunState` in the state file shows `cost_so_far = $0` (or whatever it was before the stage started). Cost tracking becomes unreliable for failed runs.

**Fix path:** Wrap the stage loop in try/except, update `state.cost_so_far` from the tracker and save state in the except handler before re-raising.

---

#### M-003 — CIO `execute_stage` hardcodes date/time literals

**Evidence:**
- `agentsuite/agents/cio/stages/execute.py:28-29`:
  ```python
  "briefing_date": "Q2 2026",
  "meeting_date": "Q2 2026",
  "meeting_time": "10:00 AM",
  ```
- 15+ hardcoded temporal strings in `_values_from_input()`: `"Q2 2026"`, `"Q3 2026"`, `"FY2026"`, etc.

**Blast radius:** Every CIO artifact generated after Q2 2026 will contain stale quarter/year references embedded in template fills. The `briefing_date`, `fiscal_year`, `fiscal_years`, `review_quarter`, etc. will all be wrong. Since these appear in executive-facing documents (board briefings, steering committee reports), this is a professional credibility issue.

**Fix path:** Generate dates dynamically from `datetime.now()`, or add `effective_date` / `fiscal_year` fields to `CIOAgentInput` so callers can supply them explicitly.

---

#### M-004 — `cio_name` is derived by splitting `strategic_priorities` on whitespace

**Evidence:**
- `agentsuite/agents/cio/stages/execute.py:17`:
  ```python
  cio_name = inp.strategic_priorities.split()[0] if inp.strategic_priorities else "CIO"
  ```
- `strategic_priorities` is a free-text field describing IT priorities (e.g., "Modernize legacy ERP, reduce vendor sprawl"). The first word of this string ("Modernize") becomes the CIO's name in all generated documents.

**Blast radius:** Every CIO brief will have the wrong name in headers, signature blocks, and attribution lines. This is a correctness bug that will appear in all CIO agent output.

**Fix path:** Add an explicit `cio_name: str` field to `CIOAgentInput`.

---

### Minor

#### m-001 — `ollama` is a hard dependency, not optional

**Evidence:**
- `pyproject.toml` line 29: `"ollama>=0.4"` is in `dependencies`, not `optional-dependencies`.
- Ollama requires a local daemon. Users who will only use cloud providers are forced to install the ollama Python package (and by implication, think about the daemon) even if they never use it.

**Fix path:** Move `ollama>=0.4` to `[project.optional-dependencies]` under `ollama = ["ollama>=0.4"]`. Guard the import in `resolver.py` and `llm/ollama.py` with `try/except ImportError`.

---

#### m-002 — `_FALLBACK` dicts in LLM providers use unguarded `dict[str, dict[str, float]]` fallback pricing

**Evidence:**
- `agentsuite/llm/anthropic.py:11`: `rates = _PRICING.get(model, {"in": 3.0, "out": 15.0})`
- `agentsuite/llm/openai.py:11`: `rates = _PRICING.get(model, {"in": 5.0, "out": 15.0})`
- Unknown models silently use stale/guessed prices. A new model like `claude-opus-4-5` (not in the pricing table) would cost-calculate silently at the default rate, potentially over- or under-charging the cost cap.

**Fix path:** Log a warning when the fallback is used: `warnings.warn(f"No pricing for model '{model}'; using default rates.", UserWarning)`.

---

#### m-003 — `QARubric` not validated at class definition time (agent startup)

**Evidence:**
- `FOUNDER_RUBRIC`, `DESIGN_RUBRIC`, etc. are module-level constants but `QARubric.score()` is only called at runtime during the `qa` stage.
- A misconfigured rubric (e.g., duplicate dimension names, zero total weight) would only fail at QA stage after all prior LLM calls have been made and money spent.

**Fix path:** Add a `model_validator` on `QARubric` that checks for duplicate names and non-positive weights at construction time, raising immediately at import.

---

#### m-004 — `Founder` intake stage classifies `.txt` and `.md` files as `"product-doc"` regardless of content

**Evidence:**
- `agentsuite/agents/founder/stages/intake.py:22-24`:
  ```python
  if suffix in _VOICE_EXTS:
      return "product-doc"
  ```
- `_VOICE_EXTS = {".txt", ".md"}` — but the field `founder_voice_samples` is also `.txt`/`.md`. This means voice samples explicitly listed in `inp.founder_voice_samples` get classified as `"brand-doc"` (correct path), but any `.txt`/`.md` files swept from `inputs_dir` are classified as `"product-doc"` even if they are voice samples.

**Fix path:** Either rename `_VOICE_EXTS` to `_TEXT_EXTS` to reflect that the classification is format-based (not content-based), or extend the intake walk to check whether a file was already listed in `founder_voice_samples` before reclassifying it.

---

#### m-005 — `StateStore.save()` mutates `state.updated_at` in-place on a Pydantic model with `extra="forbid"`

**Evidence:**
- `agentsuite/kernel/state_store.py:19`: `state.updated_at = datetime.now(tz=timezone.utc)`
- `RunState` has `model_config = ConfigDict(extra="forbid")` but does not set `frozen=True`, so attribute mutation works. This is not a bug, but it is a side-effectful mutation of the state object the caller passed in — callers may not expect their state reference to be modified.

**Fix path:** Use `state = state.model_copy(update={"updated_at": datetime.now(tz=timezone.utc)})` and return the new state, or document the mutation explicitly in the docstring.

---

#### m-006 — `TrustRiskAgent` and `CIOAgent` `_wrap()` have an extra `elif isinstance(typed_inputs, dict)` branch not present in other agents

**Evidence:**
- `agentsuite/agents/trust_risk/agent.py:55-57` and `agentsuite/agents/cio/agent.py:55-57`:
  ```python
  elif isinstance(typed_inputs, dict):
      state = state.model_copy(update={"inputs": TrustRiskAgentInput(**typed_inputs)})
  ```
- No other agent has this branch. It uses `**typed_inputs` (not `model_validate`) which bypasses Pydantic validation and alias handling.

**Fix path:** Remove the `dict` branch (it's unreachable in normal use since `edits["inputs"]` is always either a typed model or `None`) or replace `**typed_inputs` with `TrustRiskAgentInput.model_validate(typed_inputs)`.

---

### Nits

- **N-001** `agentsuite/__init__.py` exports only `__version__`. None of the 7 agent classes are in `__all__`. A `from agentsuite import FounderAgent` fails without going through `agentsuite.agents.founder.agent`. Add a top-level re-export in `__init__.py`.
- **N-002** `LLMProvider` is a `Protocol` but `AnthropicProvider`, `OpenAIProvider`, etc. are plain classes — not decorated with `@runtime_checkable` on the Protocol, so `isinstance(obj, LLMProvider)` will raise `TypeError`. Either mark the Protocol `@runtime_checkable` or remove implicit isinstance checks from internal code.
- **N-003** `ArtifactWriter.promote()` does a `shutil.rmtree(dest)` before `copytree()` — no backup or atomic swap. A crash between rmtree and copytree leaves `_kernel/<slug>/` empty.
- **N-004** `derive_project_slug()` in `founder/input_schema.py` truncates to 40 chars but does not handle empty `business_goal` (returns `""` after strip).
- **N-005** CIO `execute_stage` docstring says "8 CIO brief templates" but `TEMPLATE_NAMES` may have a different count — the docstring count should be derived from `len(TEMPLATE_NAMES)`, not hardcoded.
- **N-006** `agentsuite/llm/gemini.py` reads `api_key=os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")` — key priority is opposite to the check order in `resolver.py` (`GEMINI_API_KEY` first, `GOOGLE_API_KEY` second). Inconsistent key precedence between resolver and provider.
- **N-007** `pyproject.toml` dependency pins use `>=` ranges only — `pydantic>=2.5`, `anthropic>=0.40`, etc. For a library, this is acceptable. For reproducible installs, consider adding upper bounds at major version (`<3`, `<1` respectively) to guard against future breaking changes.

---

## Version Consistency Check

| Location | Version Found | Matches v0.7.0? |
|---|---|---|
| `pyproject.toml` | `0.7.0` | Yes |
| `agentsuite/__version__.py` | `0.7.0` | Yes |
| `agentsuite/__init__.py` | (imports from `__version__`) | Yes (via import) |
| `README.md` | (no version string found in grep) | **Not verified** — version not pinned in README |
| `CHANGELOG.md` | `[0.7.0] - 2026-04-27` (top entry) | Yes |
| `docs/index.html` | `v0.7.0` (line 46) | Yes |

**Note:** README.md contains no version string — it does not carry a pinned version badge or explicit version number. This is not a mismatch (nothing to mismatch against), but it means users reading the README cannot determine the current release version without checking pyproject.toml or CHANGELOG. Consider adding a version badge.

---

## Dependency Audit

| Package | Pin in pyproject.toml | Assessment |
|---|---|---|
| `pydantic` | `>=2.5` | Open upper bound. Acceptable for library. |
| `anthropic` | `>=0.40` | Open upper bound. Monitor for v1.x breaking changes. |
| `google-genai` | `>=1.0` | Correct package name (not deprecated `google-generativeai`). |
| `openai` | `>=1.50` | Open upper bound. |
| `mcp` | `>=1.0` | Open upper bound. |
| `ollama` | `>=0.4` | **Should be optional** (see m-001). |
| `typer` | `>=0.12` | Open upper bound. |
| `httpx` | `>=0.27` | Open upper bound. |
| `jinja2` | `>=3.1` | Open upper bound. |
| `pillow` | `>=10.0` | Open upper bound. |

**Key finding:** `ollama` is listed as a required dependency (line 29) rather than optional. All other packages are cloud-provider SDKs that are reasonable to always require. Ollama is the odd one out — it requires a local daemon and is useful only for local/zero-cost runs.

**Package correctness:** `google-genai>=1.0` is the correct, non-deprecated package name. This is a positive finding.

---

## Security Review

| Area | Finding |
|---|---|
| Hardcoded secrets | None found. All API keys read from env vars. |
| Env var safety | Safe reads (`os.environ.get()`). One unsafe `float()` parse (C-001). |
| Path traversal | `ArtifactWriter.write()` has no containment guard (C-002). |
| Command injection | No `subprocess`, `os.system`, or shell execution found. CLI uses Typer. |
| LLM prompt injection | No user-supplied content is interpolated into system prompts. User inputs go into the user-turn prompt via Jinja2 with StrictUndefined. |
| File write scope | Writes confined to `output_root/runs/<run_id>/` by convention, not enforcement (C-002). |
| Ollama probe | `_ollama_daemon_running()` makes an unauthenticated HEAD request to `localhost:11434` with a 0.5s timeout — safe, local-only. |

---

## Performance Review

| Area | Finding |
|---|---|
| LLM call batching | All 9 spec artifact LLM calls are sequential (one per artifact in a for loop). No parallelism. This is by design for determinism but means spec stage takes 9× single-call latency. |
| O(N²) operations | None found. |
| Blocking I/O | All LLM calls are synchronous. No async support. This blocks the thread for the full pipeline duration (potentially minutes). Acceptable for v0.7 but will limit MCP server concurrency. |
| File reads in extract | Each source file is read up to 1500 bytes in `_summarize_sources()`. No lazy loading issue. |
| State save frequency | State is saved after every stage (5 saves per run). Acceptable. |
| ArtifactWriter deduplication | `_register()` does a linear scan of `_refs` to find the existing path — O(N) per write. With ~15 artifacts per run, this is negligible. |

---

## Data Provenance

The data flow through all 5 stages is traceable and correct:

1. **intake** → writes `inputs_manifest.json` (source index), advances to `extract`. No data is dropped.
2. **extract** → reads `inputs_manifest.json`, writes `extracted_context.json`, surfaces `gaps` array as `open_questions` on `RunState`. `open_questions` accumulates across stages (uses `state.open_questions + open_questions`), correctly preserving prior entries.
3. **spec** → reads `extracted_context.json` from disk (not from RunState), generates 9 artifacts, writes `consistency_report.json`. The disk re-read is correct since the writer already flushed the file in stage 2.
4. **execute** → reads `extracted_context.json` again from disk, renders templates. No LLM call. Values are derived from extracted context, not re-inferred. Minor issue: if `extracted_context.json` is manually edited between stages, execute would use the edited version.
5. **qa** → reads all 9 spec artifacts from disk (not from memory), calls LLM, scores rubric, writes `qa_report.md` and `qa_scores.json`, sets `requires_revision` on RunState.

**RunState field preservation:** `model_copy(update=...)` is used consistently — all unmodified fields are preserved. `artifacts` and `cost_so_far` are updated by `_drive()` after each stage returns, not by the stage handlers themselves — correctly separating concerns.

**One gap:** If a stage raises mid-pipeline, `cost_so_far` is not updated for the partially-executed stage (see M-002).
