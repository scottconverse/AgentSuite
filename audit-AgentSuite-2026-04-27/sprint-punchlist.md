# Sprint Punch List — AgentSuite v0.7.0 Audit

**Generated:** 2026-04-27  
**For:** Dev team — fix this sprint before next release  
**Source:** `00-executive-audit.md` findings

---

> **SCOPE IS LOCKED TO THE ITEMS BELOW.** Do NOT expand scope, do NOT opportunistically clean up adjacent code, do NOT touch repos/branches not named here. If you find something else worth fixing, surface it as a follow-up — don't slip it into this batch.

---

## Blockers — Fix First

### P1 — Fix consistency-check schema split (`"mismatches"` vs `"checks"`)
**Role:** Principal Engineer | **Severity:** Blocker

5 of 7 agents have a silently broken critical-failure gate because they look for `"checks"` in the JSON envelope but the mock (and likely real LLMs following the Founder/Design prompt) returns `"mismatches"`.

**Files to change:**
- `agentsuite/agents/engineering/stages/spec.py:116` — change `.get("checks", [])` → `.get("mismatches", [])`
- `agentsuite/agents/product/stages/spec.py:115` — same
- `agentsuite/agents/marketing/stages/spec.py:101` — same
- `agentsuite/agents/trust_risk/stages/spec.py:101` — same
- `agentsuite/agents/cio/stages/spec.py:101` — same
- `agentsuite/agents/engineering/prompts/spec_consistency_check.jinja2` — update JSON schema instruction to use `"mismatches"` key
- `agentsuite/agents/product/prompts/spec_consistency_check.jinja2` — same
- `agentsuite/agents/marketing/prompts/spec_consistency_check.jinja2` — same
- `agentsuite/agents/trust_risk/prompts/spec_consistency_check.jinja2` — same
- `agentsuite/agents/cio/prompts/spec_consistency_check.jinja2` — same

**Test:** After fix, add `ConsistencyCheckFailed` integration tests for these 5 agents (see P11 below). Run `pytest tests/ -q` — expect 551 pass.

---

### P2 — Fix OpenAI default model from `"gpt-5"` to `"gpt-4.1"`
**Role:** Principal Engineer | **Severity:** Blocker

**File:** `agentsuite/llm/openai.py:27`
```python
# BEFORE
return "gpt-5"
# AFTER
return "gpt-4.1"
```
Verify `agentsuite/llm/pricing.py` already has `"gpt-4.1"` priced (it does — no pricing table change needed).

---

### P3 — Fix landing page install command
**Role:** Technical Writer | **Severity:** Blocker

**File:** `docs/index.html` — find the install code block (lines 54–55) and replace:
```html
<!-- BEFORE -->
<pre><code>pip install agentsuite
# or, no install:
uvx agentsuite-mcp</code></pre>

<!-- AFTER -->
<pre><code>pip install git+https://github.com/scottconverse/AgentSuite.git
# or, no install:
uvx --from git+https://github.com/scottconverse/AgentSuite.git agentsuite-mcp</code></pre>
```
Also check the Quick Start CLI block on the landing page — it uses `--business-goal`/`--inputs-dir` flags that don't match USER-MANUAL. Align with the actual Founder CLI interface (see P14).

---

### P4 — Fix PDF generator artifact tables for Design and Product agents
**Role:** Technical Writer | **Severity:** Blocker

**File:** `scripts/generate_readme_pdf.py` — the `AGENTS` list (lines 354–560) contains hard-coded artifact names for Design and Product that don't match USER-MANUAL or CHANGELOG.

**Action:** Read the actual `SPEC_ARTIFACTS` from:
- `agentsuite/agents/design/stages/spec.py` — whatever `SPEC_ARTIFACTS` is defined as
- `agentsuite/agents/product/stages/spec.py` — same

Use those exact names in the PDF generator's `AGENTS[1]` (Design) and `AGENTS[2]` (Product) entries. After updating, regenerate the PDF: `python scripts/generate_readme_pdf.py`.

Also fix: the CLI command code blocks in the PDF use Founder flags (`--business-goal`, `--project-slug`, `--inputs-dir`) for ALL agents. Each agent's code block should show that agent's actual required flags.

---

## Critical — Fix This Sprint

### P5 — Wrap CLI provider resolution to catch `NoProviderConfigured`
**Role:** QA Engineer | **Severity:** Critical

**File:** `agentsuite/cli.py`, `_resolve_llm_for_cli()` (line 37–49)
```python
def _resolve_llm_for_cli(provider: Optional[str], model: Optional[str]) -> LLMProvider:
    try:
        return resolve_provider(provider=provider, model=model)
    except NoProviderConfigured as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
```
Import `NoProviderConfigured` at top of `cli.py`. This single change fixes all 7 agent `run` commands and all `approve` commands.

---

### P6 — Add warning log to `mcp_server.py` silent exception swallow
**Role:** QA Engineer | **Severity:** Critical

**File:** `agentsuite/mcp_server.py:55–58`
```python
# BEFORE
for name in enabled:
    try:
        agent_class = registry.get_class(name)
    except Exception:
        continue

# AFTER
import logging
_log = logging.getLogger(__name__)

for name in enabled:
    try:
        agent_class = registry.get_class(name)
    except Exception as e:
        _log.warning("Skipping agent %s: failed to load — %r", name, e)
        continue
```

---

### P7 — Add `approve` CLI commands for Engineering and Marketing
**Role:** QA Engineer / UI/UX | **Severity:** Critical

**File:** `agentsuite/cli.py`

Add these two commands following the exact pattern of `product_approve_cmd` (lines 190–200):

```python
@engineering_app.command("approve")
def engineering_approve_cmd(
    run_id: str = typer.Argument(..., help="Run ID to approve"),
    approver: str = typer.Option("human", help="Approver identifier"),
    output_dir: Path = typer.Option(Path(".agentsuite"), ...),
) -> None:
    """Approve an engineering pipeline run and promote artifacts."""
    # Follow product_approve_cmd pattern exactly

@marketing_app.command("approve")
def marketing_approve_cmd(
    run_id: str = typer.Argument(..., help="Run ID to approve"),
    approver: str = typer.Option("human", help="Approver identifier"),
    output_dir: Path = typer.Option(Path(".agentsuite"), ...),
) -> None:
    """Approve a marketing pipeline run and promote artifacts."""
    # Follow product_approve_cmd pattern exactly
```

Also add `project_slug: Optional[str] = typer.Option(None, ...)` to both `engineering_run_cmd` and `marketing_run_cmd` (currently missing, blocks `_kernel/` promotion).

---

### P8 — Add Product and CIO to `pyproject.toml` package-data
**Role:** Principal Engineer | **Severity:** Critical

**File:** `pyproject.toml`, `[tool.setuptools.package-data]` section

Add:
```toml
"agentsuite.agents.product" = ["prompts/*.jinja2", "templates/*.md"]
"agentsuite.agents.cio" = ["prompts/*.jinja2", "templates/*.md"]
```

After adding, build the wheel (`python -m build`) and install it in a fresh venv to verify prompt/template files are present.

---

### P9 — Fix CONTRIBUTING.md: PyPI references and cross-platform venv
**Role:** Technical Writer | **Severity:** Critical

**File:** `CONTRIBUTING.md`

1. Remove lines 87–99 (PyPI Trusted Publishing setup section). Replace with: "AgentSuite does not publish to PyPI. Releases are made via GitHub only."
2. Change the venv activation step from:
   ```bash
   .venv/Scripts/pip install -e .[dev]
   ```
   to:
   ```bash
   # Windows:
   .venv\Scripts\pip install -e .[dev]
   # Mac/Linux:
   .venv/bin/pip install -e .[dev]
   # Or (cross-platform):
   python -m pip install -e .[dev]
   ```
3. Remove any line that says "CI builds and uploads to PyPI on tag push."

---

### P10 — Add MCP dispatch tests + CLI tests for remaining 5 agents
**Role:** Test Engineer | **Severity:** Critical

**Files to create/modify:**

`tests/unit/test_mcp_server.py` — add handler dispatch tests:
```python
def test_founder_run_tool_callable(tmp_path):
    """founder_run tool can be called and returns a dict with run_id."""
    # Get the registered tool handler, call it with valid FounderRunRequest fields
    # Assert output contains "run_id" key
```

`tests/unit/test_cli.py` — add `--help` exit-0 tests for 5 uncovered agents:
```python
@pytest.mark.parametrize("cmd", ["product", "engineering", "marketing", "trust-risk", "cio"])
def test_agent_run_help_exits_zero(cmd, runner):
    result = runner.invoke(app, [cmd, "run", "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
```

---

### P11 — Add `ConsistencyCheckFailed` integration tests for 6 remaining agents
**Role:** Test Engineer | **Severity:** Major (dependent on P1)

**File:** Each of `tests/integration/test_{agent}_pipeline.py` for: founder, design, product, engineering, trust_risk, cio

Copy the pattern from `tests/integration/test_marketing_pipeline.py::test_marketing_consistency_check_failure_raises`:
```python
def test_{agent}_consistency_check_failure_raises(tmp_path):
    """ConsistencyCheckFailed is raised when spec consistency check returns critical."""
    mock = MockLLMProvider(responses={
        # Normal responses for non-spec stages...
        # spec stage mock returns critical finding:
        "spec_consistency_check": json.dumps({
            "mismatches": [{"field": "tone", "severity": "critical", "description": "Mismatch"}]
        }),
    })
    agent = {AgentClass}(output_root=tmp_path, llm=mock)
    with pytest.raises(ConsistencyCheckFailed):
        agent.run({MinimalInput}())
```

**Note:** Must complete P1 first (schema standardization) or mock response key won't match.

---

## Major — Fix This Sprint

### P12 — Fix `cio_name` derived from `strategic_priorities`
**Role:** Principal Engineer | **Severity:** Major

**File 1:** `agentsuite/agents/cio/input_schema.py` — add field:
```python
cio_name: str = "CIO"  # Name used in generated documents
```

**File 2:** `agentsuite/agents/cio/stages/execute.py:17` — change:
```python
# BEFORE
cio_name = inp.strategic_priorities.split()[0] if inp.strategic_priorities else "CIO"
# AFTER
cio_name = inp.cio_name
```

---

### P13 — Fix CIO execute stage hardcoded date/time literals
**Role:** Principal Engineer | **Severity:** Major

**File:** `agentsuite/agents/cio/stages/execute.py:28-29`

Replace all hardcoded `"Q2 2026"`, `"Q3 2026"`, `"FY2026"` with dynamic values:
```python
from datetime import datetime
_now = datetime.now()
_quarter = f"Q{(_now.month - 1) // 3 + 1} {_now.year}"
_next_quarter = ...  # compute next quarter
_fiscal_year = f"FY{_now.year}"
```

Or add `effective_date: str = ""` and `fiscal_year: str = ""` to `CIOAgentInput` and fall back to computed defaults when empty.

---

### P14 — Reconcile Founder CLI flag inconsistency across all docs
**Role:** Technical Writer | **Severity:** Major

README quick-start and landing page use `--business-goal`, `--project-slug`, `--inputs-dir`.  
USER-MANUAL Founder chapter uses `--company-name`, `--mission`, `--core-values`.

**Action:**
1. Read `agentsuite/cli.py` — determine which flags actually exist on `founder_run_cmd`
2. Update every doc that uses the wrong set: README, landing page (Quick Start), USER-MANUAL Founder chapter

---

### P15 — Fix `base_agent.py` module docstring: "six-stage" → "five-stage"
**Role:** Technical Writer | **Severity:** Major

**File:** `agentsuite/kernel/base_agent.py`, line 1 module docstring

Change `"persisted six-stage pipeline"` to `"persisted five-stage pipeline (intake, extract, spec, execute, qa) with a separate approval gate"`.

---

## Out of Scope (Do NOT touch in this pass)

- Founder rubric 7→9 dimensions (tracked in next-sprint watchlist)
- Ollama optional dependency refactor
- GitHub Discussions seeding (manual repo settings step)
- Visual content / screenshots for landing page
- Golden test content assertions (next sprint)
- StateStore corrupted JSON test
- ArtifactWriter path traversal guard
- CostTracker cost preservation on mid-pipeline exception

---

## Done Definition

This sprint batch is complete when:
1. All 4 Blockers are fixed, verified by `pytest tests/ -q` passing and `scripts/verify-release.sh` passing
2. All 6 Critical fixes are merged (P5–P10)
3. `python -m build && pip install dist/*.whl` in a fresh venv loads Product and CIO agents with their prompts intact
4. Landing page shows correct install command when viewed in browser
5. `agentsuite engineering approve --help` exits 0 without error
6. `agentsuite founder run` with no API keys exits with a clean error message, not a traceback
