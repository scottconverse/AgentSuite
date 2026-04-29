# Runtime QA Deep-Dive — AgentSuite v1.0.0 GA

**Audit date:** 2026-04-29
**Role:** QA Engineer
**Scope audited:** CLI (agentsuite typer entry point), MCP server tool registration, committed sample-output, error paths. Cleanroom script and live-LLM paths source-reviewed only (time budget).
**Environment:** Windows 11, Python 3.14 (cp1252 default console), .venv at repo root, commit 9540957 (v1.0.0 GA), bash (Git for Windows).
**Auditor posture:** Adversarial.

---

## TL;DR

AgentSuite ships with two unambiguous Blocker-class runtime defects on its first-impression surfaces. (1) `agentsuite --help` crashes with an unhandled UnicodeEncodeError on stock Windows consoles because Typer/Rich emits a right-arrow glyph into a cp1252 terminal — every Windows user on a default install hits this on their first command. (2) The committed `examples/sample-output/founder/` artifacts that the repo README explicitly markets as "real Founder output ... 7 founder spec artifacts" are literally one-line stubs reading `# brand-system\nMocked content.` (and the same for every other artifact). The accompanying README in that directory tells prospective adopters they are looking at production output. They are not. Beyond those: the README MCP tool names are wrong (UX-002 confirmed — actual names are `agentsuite_*`-prefixed), the run UX is silent JSON-only with no stage progress (UX-003/UX-006 confirmed), `--inputs-dir` accepts non-existent paths without error, and there is no `agentsuite founder resume` command despite ADR-0007 being cited as governing resume idempotency. No security blockers surfaced in the time budget.

## Severity roll-up (QA)

| Severity | Count |
|---|---|
| Blocker | 2 |
| Critical | 4 |
| Major | 4 |
| Minor | 2 |
| Nit | 1 |

## What is working

- **Mock-LLM CLI execution path is fast and deterministic** — `agentsuite founder run` against `_default_mock_for_cli` finishes in ~0.7s with full artifact tree written to `.agentsuite/runs/<run-id>/`. Wall-clock real run end-to-end on a fresh CWD: 704ms.
- **AGENTSUITE_OUTPUT_DIR env var is respected.** Output landed in the calling CWD .agentsuite/, not in the AgentSuite repo, matching the project stated convention.
- **Existing-run-id collision is handled with an actionable error.** `Error: run qa-run-001 already exists. Use --force to overwrite.` — names the conflict, names the fix, exits non-zero. Good template for other error messages.
- **MCP server boots cleanly via build_server()** and exposes a tracked tool list with stable, namespaced names (agentsuite_founder_*, agentsuite_kernel_artifacts, agentsuite_cost_report).
- **Six doc artifacts are present on disk.** README.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, .gitignore, docs/index.html all exist.
- **Founder CLI subcommands match the pyproject entry point** — `agentsuite founder run`, `agentsuite founder approve` resolve and emit help.

## What could not be assessed

- **Live LLM provider paths** (Anthropic / OpenAI / Gemini / Ollama). No credentials provisioned for this audit run; covered by source review only.
- **scripts/run-cleanroom.sh end-to-end.** The script copies the repo into a tempdir, builds a fresh venv, pip-installs, and runs the pipeline; runtime exceeds the 1-minute long-task watchdog window. Source-reviewed (102 lines, looks correct). Recommend Test Engineer cover as part of suite.
- **Resume idempotency (ADR-0007).** Cannot be exercised at runtime because no `agentsuite founder resume` CLI subcommand exists. The MCP layer registers agentsuite_founder_resume, but it is not reachable from the CLI surface that the README quick-start uses.
- **Mid-stage kill behavior.** Mock pipeline is sub-second; there is no realistic window to interrupt. Live-LLM kill+resume needs separate testing.
- **Background-run no-provider error message at runtime.** Three attempts to capture the exact NoProviderConfigured message with all keys unset got swallowed by the harness auto-background behavior; source-reviewed agentsuite/llm/resolver.py shows the messages are actionable strings (e.g. "ANTHROPIC_API_KEY not set").

---

## Product shape

AgentSuite is a Python CLI + MCP server that runs reasoning agents (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO) against an LLM provider to produce structured Markdown/JSON artifacts in `.agentsuite/runs/<run-id>/`. There is no web UI. QA focused on the CLI install-and-first-run surface, the MCP tool registration contract, error-message actionability, and the committed sample-output that doubles as the project marketing screenshot.

## Flows exercised

| Flow | Result | Findings |
|---|---|---|
| `agentsuite --help` (Windows default console) | **Fail (Blocker)** | QA-001 |
| `agentsuite founder --help` (PYTHONIOENCODING=utf-8) | Pass | — |
| `agentsuite founder run --help` (PYTHONIOENCODING=utf-8) | Pass | QA-004 (flag mismatch with screenshots) |
| `agentsuite founder run` against mock LLM, fresh CWD | Pass (functional) | QA-005, QA-006 |
| Inspect committed examples/sample-output/founder/ | **Fail (Blocker)** — stubs marketed as real | QA-002, QA-003 |
| MCP build_server() boot + tool list | Pass | QA-007 (name mismatch with README) |
| Existing-run-id collision (--run-id already exists) | Pass — actionable error | — |
| Non-existent --inputs-dir | **Fail** — silently succeeds | QA-008 |
| `agentsuite founder resume` (per ADR-0007) | **Fail** — command does not exist on CLI | QA-009 |
| Cleanroom script (bash scripts/run-cleanroom.sh) | Not run (time budget) | — |

## Adversarial scenarios exercised

| Scenario | Outcome | Findings |
|---|---|---|
| First run on a stock Windows console | UnicodeEncodeError traceback before any work | QA-001 |
| Non-existent --inputs-dir path passed to founder run | Run succeeds with stub artifacts; no validation | QA-008 |
| --run-id colliding with existing run | Clean actionable error | (positive) |
| Reading sample-output as a prospective adopter would | Stub content directly contradicts README claim | QA-002, QA-003 |
| Querying actual MCP tool names via build_server().tool_names() | Names do not match README documentation | QA-007 |

---

## Findings

### [QA-001] — Blocker — Install — `agentsuite --help` crashes on default Windows console

**Evidence**

Reproduction (Windows 11, Python 3.14, default cp1252 console encoding):

```
$ source .venv/Scripts/activate
$ agentsuite --help
... [Rich pretty-traceback approximately 80 lines] ...
File "...\rich\_win32_console.py", line 402, in write_text
    self.write(text)
File "...\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: charmap codec cant encode character u2192 in position 47: character maps to <undefined>
```

Workaround verified: `export PYTHONIOENCODING=utf-8` then `agentsuite --help` renders correctly.

The offending arrow is in the Typer help string at `agentsuite/cli.py:18` ("AgentSuite — reasoning agents for vague intent -> precise artifacts" with em-dash and right-arrow). Both fall outside cp1252.

**Why this matters**

Every Windows user following the README quick-start hits this on the very first command after `pip install`. Their first impression of AgentSuite is an 80-line Rich traceback. The README does not warn about console encoding. The help-string crash applies to `agentsuite --help`, `agentsuite founder` (no subcommand), and any error path that re-invokes help formatting. v1.0.0 GA shipped with a non-functional first-run experience on a Tier 1 platform.

**Blast radius**
- Adjacent code: agentsuite/cli.py:18 (typer.Typer help string) and any docstring containing right-arrow, em-dash, en-dash, smart quotes, or other non-cp1252 characters. A grep for non-ASCII across CLI-reachable docstrings is warranted.
- Shared assumption: project assumes UTF-8 stdout. Python on Windows defaults to cp1252 unless PYTHONIOENCODING or PYTHONUTF8=1 is set; Python 3.15 makes UTF-8 the default but 3.14 (current GA target) does not.
- User-facing: every Windows user on first run.
- Migration: none.
- Tests to update: add a test that runs `agentsuite --help` under PYTHONIOENCODING=cp1252 and asserts exit code 0. Cleanroom script should also force the broken encoding.
- Related findings: TEST suite did not catch this — Test Engineer should flag the gap.

**Fix path**

Either (a) replace right-arrow with `->` and em-dash with `--` in all CLI-reachable strings; (b) call `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` early in cli.py; (c) document `PYTHONUTF8=1` as a Windows install prerequisite in README. Option (a) is cheapest and most robust. Add a CI matrix job that runs the help command under cp1252.

---

### [QA-002] — Blocker — Docs/Marketing — examples/sample-output/founder/ is mock stub content marketed as real Founder output

**Evidence**

`examples/sample-output/founder/README.md` says verbatim:

> "This directory is a complete, deterministic Founder run committed to the repo so prospective adopters can browse what AgentSuite produces without installing anything."
> "This is real Founder output rendered against a fixed prompt template under a deterministic mock — exactly what a live `agentsuite founder run` produces, minus the LLM-specific phrasing on free-text bodies."

The actual contents:

```
$ cat examples/sample-output/founder/brand-system.md
# brand-system
Mocked content.

$ cat examples/sample-output/founder/audience-map.md
# audience-map
Mocked content.

$ cat examples/sample-output/founder/founder-voice-guide.md
# founder-voice-guide
Mocked content.

$ cat examples/sample-output/founder/visual-style-guide.md
# visual-style-guide
Mocked content.
```

Seven of the artifacts are this exact one-line `Mocked content.` stub. qa_report.md shows uniform 8.00 across nine dimensions — the literal mock pass score, not real QA scoring. cost_summary.json reports `"provider": null, "model": null`.

**Why this matters**

This directory is the project storefront for adopters who do not want to install before evaluating. The README explicitly invites them in, then shows them a placeholder. Anyone who reads the directory and the README together will conclude AgentSuite v1.0.0 produces empty artifacts. This is a marketing-claim defect at the same severity as a screenshot showing a feature the product does not have.

**Blast radius**
- Adjacent code: tests/golden/ likely uses the same mock fixtures; verify those goldens are not pinning the stub content as expected output.
- User-facing: PyPI page, GitHub landing, any external link to examples/sample-output/. Screenshot referenced in UX-001 is downstream of this same defect.
- Migration: none — content-only fix.
- Tests to update: any test that asserts examples/sample-output/founder/brand-system.md contains specific content needs to be updated.
- Related findings: UX-001 (screenshot in docs/index.html shows the same "Mocked content"), QA-003, DOC findings on landing-page truthfulness.

**Fix path**

Two real options. (a) Run a live Founder pipeline against examples/patentforgelocal/ with a paid Anthropic key under a $1 cap, commit the resulting artifacts, and update the sample-output README. (b) Re-key MockLLMProvider._default_mock_for_cli to return realistic-looking demo content (a paragraph each), and rename to examples/mock-output/ with a header note that it is shaped-but-not-substantive. Option (a) is the right answer for a v1.0 GA project — cost is bounded and credibility gain is large.

---

### [QA-003] — Critical — Docs — examples/sample-output/founder/README.md actively misleads readers

Same root as QA-002, separately tagged because the README wording goes beyond passive incompleteness — it asserts these stub files are "real Founder output ... exactly what a live `agentsuite founder run` produces." A reader who clicks through and inspects the files will conclude the maintainers are either careless or dishonest. Fix path: rewrite as part of QA-002, OR if the sample-output is left as-is during a hotfix window, replace the README with an honest "intentionally stubbed mock-LLM output for shape-illustration; live samples coming in v1.0.1" note. The current README is worse than no README.

---

### [QA-004] — Critical — Docs — Hero CLI screenshot/README invokes flags that do not exist

**Evidence**

Actual `agentsuite founder run --help` (under PYTHONIOENCODING=utf-8):

```
Options:
  *  --business-goal  TEXT  Required business goal [required]
     --project-slug   TEXT  Stable slug for _kernel/ promotion
     --inputs-dir     PATH  Directory of source materials
     --run-id         TEXT  Run ID (default: auto-generated timestamp+uuid)
     --force                Overwrite existing run directory if it exists
```

UI/UX role report flagged the screenshot using `--user-request` and `--founder-voice-samples`. Neither flag exists. Confirmed by reading agentsuite/cli.py and by --help output above.

**Why this matters**

A user copy-pasting from the hero screenshot gets `Error: No such option: --user-request`. First-run failure for the demonstrated path.

**Blast radius**
- Adjacent: any screenshot, demo GIF, asciicast, or copy-pasted snippet in README, USER-MANUAL.md, README-FULL.pdf, docs/index.html.
- Tests to update: none code-side; this is a docs/asset regen.
- Related findings: UX-003, UX-004 from UI/UX role.

**Fix path**

Re-record the hero screenshot/asciicast against actual flag names, or rename flags to match the screenshot if `--user-request` was intended. Add a docs check verifying flag names in docs match `--help` output.

---

### [QA-005] — Critical — UX — `agentsuite founder run` emits no stage progress, only terminal JSON

**Evidence**

Full stdout of a complete founder run against the mock LLM:

```
{
  "run_id": "qa-run-001",
  "primary_path": ".agentsuite\\runs\\qa-run-001\\brand-system.md",
  "status": "approval"
}
```

No "Stage 1/5: extract", no "Generating artifact 3/8: visual-style-guide", no spinner, no progress bar. Real Anthropic/OpenAI runs will take 30–120 seconds per stage. The user sees nothing until the JSON appears.

**Why this matters**

A live run goes silent for minutes. Users will reasonably assume it hung, kill it, and lose work. The hero screenshot UI/UX flagged showing checkmarks for stage markers does not match runtime — meaning either the screenshot lied, or there is a code path that emits progress and is not wired in.

**Blast radius**
- Adjacent code: every agent run() method (agentsuite/agents/founder/agent.py and parallels for design/product/engineering/marketing/trust_risk/cio).
- User-facing: every CLI run on a real provider.
- Tests to update: golden tests likely depend on stdout being JSON-only — adding stderr progress output will not break them, but be deliberate about stdout/stderr discipline.
- Related findings: UX-003, UX-006 from UI/UX role.

**Fix path**

Emit per-stage progress to **stderr** so JSON on stdout stays pipe-clean for scripting. Use rich.Progress or simple `[stage 2/5] extract...` lines. Honor `--quiet` for JSON-only. Add `--no-color`.

---

### [QA-006] — Critical — UX — JSON output uses Windows backslashes in primary_path

**Evidence**

```json
"primary_path": ".agentsuite\\runs\\qa-run-001\\brand-system.md"
```

This is what a user piping into jq or programmatic consumers will see on Windows. POSIX consumers get forward slashes. Cross-platform scripts that consume this output break on path normalization.

**Why this matters**

The structured-output contract is platform-dependent. Anyone wiring AgentSuite into a CI workflow that runs on both Linux and Windows agents will hit this. It is a minor inconsistency that becomes a real bug the moment someone does `cd $(jq -r .primary_path < output.json)`.

**Blast radius**
- Adjacent code: every place a Path is serialized into JSON output. Recommend `path.as_posix()` at JSON-serialization boundaries.
- Migration: minor — anyone consuming primary_path as a string today expects backslashes on Windows. CHANGELOG note suffices.
- Tests to update: any golden that asserts path shape.

**Fix path**

Normalize all path values to POSIX form at the JSON boundary. Document the contract in README ("paths in JSON output are always forward-slash, regardless of OS").

---

### [QA-007] — Major — Docs/MCP — README documents MCP tool names without the agentsuite_ prefix

**Evidence**

README.md line 96:
> "Restart Codex. Tools `founder_run`, `founder_approve`, `founder_get_status`, `founder_list_runs`, `founder_resume`, plus the cross-agent `agentsuite_list_agents`, `agentsuite_kernel_artifacts`, `agentsuite_cost_report` are now callable."

Actual registered names (from `python -c "from agentsuite.mcp_server import build_server; s=build_server(); print(sorted(s.tool_names()))"`):

```
agentsuite_cost_report
agentsuite_founder_approve
agentsuite_founder_get_status
agentsuite_founder_list_runs
agentsuite_founder_resume
agentsuite_founder_run
agentsuite_kernel_artifacts
agentsuite_list_agents
```

Per-agent tool names are agentsuite_founder_* — README drops the prefix.

Additionally: README mentions Marketing, Trust/Risk, CIO agents in the agent table, but **no** agentsuite_marketing_*, agentsuite_trust_risk_*, or agentsuite_cio_* tools are registered. The seven agents claimed via CLI exist; only Founder is exposed via MCP. README does not disclose this asymmetry.

**Why this matters**

A user wiring AgentSuite into Codex or Claude Code per the README will get `Tool not found: founder_run`. The fix is one prefix (add agentsuite_), but the user has to discover it. The bigger Critical-adjacent issue is that six of seven agents are CLI-only despite README implying full MCP parity.

**Blast radius**
- Adjacent code: any other doc that references tool names — USER-MANUAL.md, README-FULL.pdf, docs/index.html, CHANGELOG release notes for v1.0.0.
- Tests to update: a doc-truthfulness test that imports build_server() and asserts every tool name mentioned in README is in tool_names() would prevent recurrence.
- Related findings: UX-002 from UI/UX role.

**Fix path**

(a) Update README to use actual agentsuite_* names. (b) Disclose the MCP-exposure asymmetry: list which agents have MCP tools and which are CLI-only. (c) Add a CI doc check.

---

### [QA-008] — Major — Validation — --inputs-dir accepts non-existent paths silently

**Evidence**

```
$ agentsuite founder run --business-goal test --project-slug x --run-id qa-run-bad-inputs --inputs-dir /tmp/does-not-exist-xyz
{
  "run_id": "qa-run-bad-inputs",
  "primary_path": ".agentsuite\\runs\\qa-run-bad-inputs\\brand-system.md",
  "status": "approval"
}
$ ls /tmp/does-not-exist-xyz
ls: cannot access /tmp/does-not-exist-xyz: No such file or directory
```

Run succeeds with status approval against an inputs dir that does not exist. The Typer option is declared `--inputs-dir PATH` but lacks `exists=True`.

**Why this matters**

A user typing the inputs path wrong gets a "successful" run with no inputs incorporated. They may approve it and promote stub content into _kernel/. Silent acceptance of bad input is a Major correctness issue.

**Blast radius**
- Adjacent code: every Typer Path option in cli.py — likely needs `exists=True, file_okay=False, dir_okay=True, readable=True` consistently.
- User-facing: any user with a typo or stale path.
- Tests to update: add a CLI test that asserts `--inputs-dir /nonexistent` exits non-zero with an actionable error.

**Fix path**

```python
inputs_dir: Optional[Path] = typer.Option(
    None,
    exists=True, file_okay=False, dir_okay=True, readable=True,
    help="Directory of source materials",
)
```

---

### [QA-009] — Major — CLI Surface — No `agentsuite founder resume` command despite ADR-0007 / MCP agentsuite_founder_resume

**Evidence**

`agentsuite founder --help` shows only `run` and `approve`. `agentsuite founder resume --help` exits with `No such command resume`. Yet mcp_server.build_server() registers agentsuite_founder_resume, and the project memory references ADR-0007 as governing resume idempotency.

**Why this matters**

A user whose long live-LLM run fails midway has no documented CLI escape hatch — only the MCP path, which requires Codex/Claude Code to be wired in. The CLI is the documented quick-start surface; resume must exist there. Idempotency cannot be QA-d at runtime without it.

**Blast radius**
- Adjacent code: agentsuite/cli.py (add founder resume command); agentsuite/agents/founder/agent.py (resume entry-point likely already exists since MCP wraps it).
- User-facing: any user with a failed long run.
- Tests to update: add CLI integration test for resume happy-path and resume-from-mid-stage.
- Related findings: ADR-0007 cross-check from Engineering role.

**Fix path**

Wire the existing resume function from agents/founder/agent.py into a `founder resume --run-id <id>` Typer subcommand. Document in README and USER-MANUAL.md.

---

### [QA-010] — Minor — Console — Help-output rendering tied to platform default encoding

Even after QA-001 is fixed for the right-arrow and em-dash, any future maintainer adding a unicode glyph to a help string re-introduces the same crash. The robust fix is encoding-agnostic stdout setup at CLI entry.

**Fix path**

`sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at the top of cli.py entry, gated on Windows (or unconditional — harmless on POSIX).

---

### [QA-011] — Minor — Discoverability — `agentsuite agents` listing does not indicate MCP-exposure status

A user running `agentsuite agents` sees seven agents. They have no way to know that only Founder has MCP tools registered (per QA-007). Add an `mcp_tools_registered: bool` column to the listing.

---

### [QA-012] — Nit — UX — --debug flag is global but not surfaced from subcommand errors

A user hitting an error in a subcommand naturally types `agentsuite founder run --debug`, which is rejected because --debug is on the parent group. A one-line note in error output ("for full traceback, prepend --debug before the subcommand") would smooth the UX.

---

## Performance snapshot

| Metric | Observed | Benchmark | Verdict |
|---|---|---|---|
| Mock-LLM founder run end-to-end (cold venv, fresh CWD) | 704 ms | <2 s for mock | Pass |
| `agentsuite --help` (PYTHONIOENCODING=utf-8) | <500 ms | <1 s for CLI help | Pass |
| MCP server build_server() boot (in-process) | ~150 ms | <1 s | Pass |
| Live-LLM stage latency | not measured | 30–120 s/stage typical | — |

Mock-path performance is good. The interesting question is live-LLM latency × silent UX (QA-005) — perceived performance will be much worse than wall-clock.

## Security / privacy snapshot

- No credentials surfaced in repo grep for ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY outside of source-as-string-literal in resolver.py (intentional). .gitignore covers .env.
- No security-class issues surfaced in the runtime budget. Recommend Engineering role check the AGENTSUITE_LLM_PROVIDER_FACTORY import-by-string env var path — `getattr(importlib.import_module(module_name), fn_name)()` will execute arbitrary user code from any module name set in env. Acceptable for a dev tool but worth a docstring warning.

## Console and log observations

- Clean run on stdout under mock LLM: single JSON object. No stray prints, no warnings, no Rich noise.
- `agentsuite --help` on Windows default console: 80-line traceback (QA-001).
- No deprecation warnings observed under Python 3.14.

## Patterns and systemic observations

- **Doc–reality drift across surfaces.** QA-001/002/003/004/007/009 share a root pattern: shipped artifacts (READMEs, screenshots, sample-output, MCP names, ADR references) describe a product slightly different from the one that runs. A doc-truthfulness CI step that imports the live CLI/MCP and asserts every tool name and flag mentioned in README.md exists at runtime would have caught most of these.
- **Mock-content marketing leak.** The mock fixture (`Mocked content.`) is the literal default response for unmatched prompts in _default_mock_for_cli. It made it all the way into the storefront. Recommend the mock provider write something obviously labeled as `[MOCK]` so leaks are visually screaming.
- **Windows-as-second-class.** Two of the most user-visible defects (QA-001 cp1252, QA-006 backslash paths) are Windows-only. The CI matrix likely has a Linux-only happy path. Adding Windows + cp1252 + non-UTF-8 locale jobs to the CI matrix would have caught both.

## Appendix: environments and artifacts

- **OS:** Windows 11 Pro (10.0.26200)
- **Shell:** bash (Git for Windows MSYS), PYTHONIOENCODING toggled per test
- **Python:** 3.14
- **AgentSuite:** commit 9540957 (v1.0.0 GA), .venv at repo root
- **Tools used:** typer/click CLI, in-process build_server() call to enumerate MCP tools, cat/head for sample-output inspection. No browser. No network calls (all mock-LLM).
- **Test CWD for runtime runs:** /tmp/agentsuite-qa-test/ (separate from the AgentSuite repo, per project convention).
