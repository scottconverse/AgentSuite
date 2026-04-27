# Executive Audit Report — AgentSuite v0.7.0

**Audit date:** 2026-04-27  
**Scope:** Full codebase, all documentation, test suite, runtime behavior, UX surfaces  
**Posture:** Balanced — credit what's done well, flag what's broken  
**Roles:** Principal Engineer · UI/UX Designer · Technical Writer · Test Engineer · QA Engineer

---

## Executive Summary

AgentSuite v0.7.0 is a well-architected, structurally coherent library. The 5-stage kernel pipeline is correctly abstracted in `BaseAgent`, all 7 agents subclass it consistently, Jinja2 uses `StrictUndefined` everywhere, version numbers are consistent across all checked locations, and 551 tests pass with zero failures. The foundation is solid.

However, four issues require immediate attention before external users hit them:

1. **The consistency-check critical-failure gate is silently broken for 5 of 7 agents** — a schema naming split (`"mismatches"` vs `"checks"`) means the gate that should halt a pipeline on a critical LLM mismatch always passes for Engineering, Product, Marketing, TrustRisk, and CIO.
2. **The OpenAI default model is `"gpt-5"`, which does not exist** — any user with `OPENAI_API_KEY` gets a 404 on first call.
3. **The landing page install command (`pip install agentsuite`) fails** — the package is not on PyPI, the landing page is the public storefront, and every user who lands there and follows the instructions hits an error immediately.
4. **The CLI surfaces a raw Python traceback** when no API keys are configured — the most common first-run failure path has the worst possible UX.

The documentation sprint produced real value: the USER-MANUAL is genuinely excellent, the CHANGELOG is honest and thorough, and the README is accurate. The gaps are concentrated in the landing page, the PDF generator's agent data tables, and CONTRIBUTING.md.

The test suite is professionally structured with zero failures and no skip markers. The gaps are contract-enforcement surfaces: MCP tool dispatch is never exercised by any test, CLI coverage is frozen at 2 of 7 agents, and the consistency-check failure path is tested only for Marketing.

---

## Severity Roll-Up

| Role | Blockers | Critical | Major | Minor | Nit | Total |
|---|---|---|---|---|---|---|
| Principal Engineer | 2 | 3 | 4 | 6 | 7 | 22 |
| UI/UX Designer | 0 | 2 | 5 | 6 | 5 | 18 |
| Technical Writer | 2 | 4 | 6 | 5 | 5 | 22 |
| Test Engineer | 0 | 3 | 6 | 5 | 4 | 18 |
| QA Engineer | 0 | 2 | 3 | 3 | 3 | 11 |
| **Total (pre-merge)** | **4** | **14** | **24** | **25** | **24** | **91** |
| **After cross-role merge** | **4** | **10** | **17** | **20** | **18** | **69** |

*Cross-role merges: "missing approve CLI" (UX M1 + QA MAJ-01), "landing page install command" (Doc B-1 + UX M4), "MCP dispatch untested" (Test C-1 + UX C2), "CLI discoverability" (UX C1 + QA context).*

---

## Top 10 Findings (By Severity, Merged)

### #1 — Consistency-check gate silently broken for 5 of 7 agents (Blocker · Engineering)

**Schema split: `"mismatches"` (Founder/Design) vs `"checks"` (Engineering/Product/Marketing/TrustRisk/CIO)**

The critical-failure gate that should raise `ConsistencyCheckFailed` and halt the pipeline calls `.get("mismatches", [])` in Founder/Design and `.get("checks", [])` in the five newer agents. The mock LLM returns `{"mismatches": []}`. Result: the critical gate **always returns an empty list and never fires** for 5 agents, regardless of what the LLM actually returns.

*Files: `agentsuite/agents/{engineering,product,marketing,trust_risk,cio}/stages/spec.py:101` — all use `"checks"`. `agentsuite/llm/mock.py:90` — returns `"mismatches"` envelope.*  
*Fix: Standardize on `"mismatches"` across all agents. Update prompts, stage files, and mock.*

---

### #2 — OpenAI default model `"gpt-5"` does not exist (Blocker · Engineering)

`agentsuite/llm/openai.py:27` returns `"gpt-5"` as the default model. No such model exists in the OpenAI API as of audit date. Every user with `OPENAI_API_KEY` configured (without an explicit `--model` override) gets a 404 from the OpenAI API on their first LLM call.

*Fix: Change to `"gpt-4.1"` or `"gpt-4o"` — both are priced in the pricing table.*

---

### #3 — Landing page install command fails: `pip install agentsuite` (Blocker · Doc/UX)

`docs/index.html:54-55` shows `pip install agentsuite`. The package is not on PyPI. The README explicitly states "no PyPI publication." The `uvx agentsuite-mcp` no-install command on the same page also fails without PyPI. Every user who finds AgentSuite via GitHub Pages and follows the install instructions hits an immediate error.

*Fix: Change landing page install block to `pip install git+https://github.com/scottconverse/AgentSuite.git`. Update uvx form accordingly.*

---

### #4 — PDF generator hard-codes wrong artifact names for Design and Product agents (Blocker · Doc)

`scripts/generate_readme_pdf.py` contains hard-coded agent artifact tables that disagree with USER-MANUAL, CHANGELOG, and each other for the Design and Product agents. Three different artifact lists exist across three authoritative sources for those two agents. The PDF is positioned as the "Technical Reference" — its tables are wrong for 2 of 7 agents.

*Fix: Trace actual artifact names from the agent `SPEC_ARTIFACTS` constants and hard-code from that single source of truth.*

---

### #5 — CLI surfaces raw traceback on first run with no API keys (Critical · QA)

`agentsuite/cli.py:_resolve_llm_for_cli()` calls `resolve_provider()`, which raises `NoProviderConfigured` (a `RuntimeError` subclass). No CLI caller wraps this in a try/except. A first-time user with no API keys configured gets a Python traceback as their first interaction with the tool. The error message embedded in the traceback is actually good — it's just buried.

*Blast radius: All 7 agent `run` commands, all `approve` commands.*  
*Fix: One try/except in `_resolve_llm_for_cli()` with `typer.echo(f"Error: {e}", err=True); raise typer.Exit(1)`.*

---

### #6 — `mcp_server.py` silently swallows agent-load failures (Critical · QA/Engineering)

`agentsuite/mcp_server.py:55-58` has `except Exception: continue` with no logging. If any agent fails to load during MCP server startup, it is silently absent from the tool list. An operator running `agentsuite mcp` with a broken dependency could have 3 of 7 agents missing with no diagnostic signal.

*Fix: `except Exception as e: logging.warning("Skipping agent %s: %r", name, e); continue`.*

---

### #7 — Engineering and Marketing have no `approve` CLI command (Critical · QA/UX)

`agentsuite/cli.py` defines `run` for all 7 agents but `approve` only for Founder, Design, Product, TrustRisk, and CIO. A user who runs `agentsuite engineering run` or `agentsuite marketing run` successfully has no CLI path to approve and promote the output. They must drop to the Python API.

*Fix: Add `@engineering_app.command("approve")` and `@marketing_app.command("approve")` following the `product_approve_cmd` pattern.*

---

### #8 — `pyproject.toml` missing package-data for Product and CIO agents (Critical · Engineering)

`pyproject.toml [tool.setuptools.package-data]` does not list `agentsuite.agents.product` or `agentsuite.agents.cio`. Both have `prompts/` and `templates/` directories required at runtime. When installed from wheel (not editable), these files are absent — any prompt or template render call for those agents raises `TemplateNotFound`.

*Fix: Add both agents to `[tool.setuptools.package-data]` with `["prompts/*.jinja2", "templates/*.md"]`.*

---

### #9 — CONTRIBUTING.md contradicts the no-PyPI decision and is Windows-only (Critical · Doc)

CONTRIBUTING.md (a) tells contributors the project publishes to PyPI on every release — the opposite of the documented architectural decision; (b) provides only the Windows venv activation path (`.venv/Scripts/pip`) — a Mac/Linux contributor following these instructions exactly will get `No such file or directory` before running their first test.

*Fix: Remove PyPI publishing section. Add Mac/Linux activation path or use `python -m pip install -e .[dev]` cross-platform form.*

---

### #10 — MCP tool dispatch is completely untested; CLI frozen at 2/7 agents (Critical · Test)

The entire MCP tool handler layer — argument validation, error wrapping, return serialization — has zero test coverage. `test_mcp_server.py` only verifies registration. Additionally, CLI tests exist only for Founder and Design; the remaining 5 agents (Product, Engineering, Marketing, TrustRisk, CIO) have no CLI test at all. A CLI regression on any uncovered agent goes undetected until a user hits it.

*Fix: Add MCP dispatch tests calling `founder_run`, `founder_approve`, and at minimum add `agentsuite <agent> run --help` exit-0 tests for the 5 uncovered agents.*

---

## What's Working Well

**Architecture is coherent and correctly implemented.** All 7 agents subclass `BaseAgent` with the same structural shape. `_wrap()` correctly handles resume deserialization. Jinja2 `StrictUndefined` is enforced everywhere — template variable mismatches surface immediately rather than silently. The cost/state/approval subsystems have no correctness bugs.

**551 tests pass with zero failures and zero skips.** Hard Rule 4a is respected. Kernel unit tests (artifacts, cost, QA, state store, base agent) are thorough and sharp. `MockLLMProvider` is well-designed with keyword dispatch and call recording. All 7 agents have unit + integration + golden coverage.

**USER-MANUAL is the standout documentation artifact.** Genuinely written for non-technical readers. Agent-by-agent walkthroughs, platform-specific instructions, actionable error tables, and a 40-term glossary. A non-technical person could successfully use AgentSuite with this document.

**Version consistency is perfect.** `0.7.0` appears in `pyproject.toml`, `__version__.py`, `CHANGELOG.md`, and `docs/index.html`. No drift. CHANGELOG follows Keep a Changelog format with honest, specific entries for all 7 versions.

**No secrets in committed code.** All API keys are environment variables. No credentials in any source file. `AGENTSUITE_ENABLED_AGENTS` env var pattern is clean and well-documented. Cross-platform path handling is correct — `pathlib.Path` used throughout, no hardcoded separators.

---

## This-Sprint Punch List

*Ordered by severity. See `sprint-punchlist.md` for the dev-team-ready version with file paths.*

1. **[Blocker]** Fix consistency-check schema split — standardize on `"mismatches"` in all 5 newer agent specs and prompts
2. **[Blocker]** Fix OpenAI default model from `"gpt-5"` to `"gpt-4.1"` in `agentsuite/llm/openai.py`
3. **[Blocker]** Fix landing page install command — replace `pip install agentsuite` with GitHub form
4. **[Blocker]** Fix PDF generator artifact tables for Design and Product agents
5. **[Critical]** Wrap `_resolve_llm_for_cli()` in try/except to catch `NoProviderConfigured` gracefully
6. **[Critical]** Add `logging.warning()` in `mcp_server.py:build_server()` before `continue`
7. **[Critical]** Add `approve` commands for Engineering and Marketing in `cli.py`
8. **[Critical]** Add `agentsuite.agents.product` and `agentsuite.agents.cio` to `pyproject.toml` package-data
9. **[Critical]** Fix CONTRIBUTING.md: remove PyPI section, add Mac/Linux venv activation
10. **[Critical]** Add MCP tool dispatch tests + CLI tests for remaining 5 agents
11. **[Major]** Fix `cio_name` — add `cio_name: str` field to `CIOAgentInput`; remove `split()[0]` hack
12. **[Major]** Fix CIO execute hardcoded date literals — derive from `datetime.now()` or add input field
13. **[Major]** Add `ConsistencyCheckFailed` integration tests for Founder, Design, Product, Engineering, TrustRisk, CIO
14. **[Major]** Fix `base_agent.py` module docstring: "six-stage pipeline" → "five-stage pipeline"
15. **[Major]** Fix Founder CLI flag inconsistency — README/landing page use `--business-goal`; USER-MANUAL uses `--company-name` — pick one and align all docs

---

## Next-Sprint Watchlist

*See `next-sprint-watchlist.md` for full detail.*

1. **Founder rubric has 7 dimensions, not 9** — inconsistent quality standard vs. all other agents
2. **Ollama is a hard dependency** — should be optional in `pyproject.toml`
3. **QA pass/fail exact-boundary (7.0) is untested** — comparison operator behavior (`>=` vs `>`) is unverified
4. **HardCapExceeded propagation through stage loop** — exception behavior under mid-pipeline cap hit is untested
5. **ArtifactWriter path traversal guard missing** — no containment check on relative paths (low risk now, grows with MCP surface)
6. **CostTracker not updated when stage raises** — cost is lost for failed runs
7. **Golden tests assert existence, not content** — structural regressions are invisible until live run
8. **RunState deserialization is shallow in tests** — agent-subclass-specific fields are not verified to survive round-trip
9. **GitHub Discussions not seeded** — no community presence; requires manual toggle in repo settings
10. **No visual content anywhere** — landing page, README, and USER-MANUAL have zero screenshots or output examples

---

## Blast-Radius Notes

**Consistency-check schema fix (Finding #1):** Changing 5 agent spec.py files and 5 Jinja2 prompt templates. After the fix, `ConsistencyCheckFailed` will actually fire in agents where it previously silently passed — this may cause integration tests to fail if the mock response triggers a critical finding. Coordinate with test fixes (#13 in punch list).

**package-data fix (Finding #8):** After adding Product and CIO to `pyproject.toml`, rebuild the wheel and verify with `pip install dist/*.whl` in a fresh venv. An editable install (`pip install -e .`) masks this bug — only a real wheel install exposes it.

**OpenAI model fix (Finding #2):** Changing the default model may alter pricing table lookups. Verify `_cost_usd("gpt-4.1", ...)` resolves correctly against the pricing table.

**CLI approve commands (Finding #7):** Adding `approve` to Engineering and Marketing changes their CLI surface. MCP tool registration for those agents already includes `approve` (via `mcp_tools.py`) — the gap is CLI-only. No MCP blast radius.

---

## Deep-Dive Cross-References

| Finding | Eng | UX | Doc | Test | QA |
|---|---|---|---|---|---|
| Consistency-check schema split | B-001 | — | — | M-1 (partial) | — |
| OpenAI model gpt-5 | B-002 | — | — | — | — |
| Landing page install command | — | M4 | B-1 | — | — |
| PDF generator wrong artifacts | — | — | B-2 | — | — |
| CLI raw traceback on no API keys | — | C1 (related) | — | — | CRIT-01 |
| MCP server silent exception swallow | C-002 (related) | — | — | — | CRIT-02 |
| Missing approve (Engineering/Marketing) | — | M1 | — | — | MAJ-01 |
| pyproject.toml missing package-data | M-001 | — | N-5 | — | — |
| CONTRIBUTING.md PyPI/venv errors | — | — | C-1, C-2 | — | — |
| MCP dispatch untested | — | C2 | — | C-1 | — |
| cio_name from strategic_priorities | M-004 | — | — | — | — |
| CIO hardcoded date literals | M-003 | — | — | — | — |
