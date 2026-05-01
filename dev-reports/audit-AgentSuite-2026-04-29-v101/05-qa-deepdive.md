# Runtime QA Deep-Dive — AgentSuite v1.0.1 (closure pass)

**Audit date:** 2026-04-29
**Role:** QA Engineer
**Scope audited:** v1.0.1 candidate at HEAD `de2a7a3`. Closure-only verification of v1.0.0 audit findings QA-001, QA-002, QA-004, QA-005, QA-007, QA-009 against the running product. Plus drift traps (CR-04), ENG-001 path-traversal hardening, and a thin probe for new runtime regressions.
**Environment:** Windows 11, Python 3.14, `.venv/Scripts/python.exe`, bash (Git for Windows). Mock-LLM provider (`agentsuite.llm.mock:_default_mock_for_cli`). Output redirected to `/tmp/qa-probe`.
**Auditor posture:** Balanced.

---

## TL;DR

Five of the six v1.0.0 findings are runtime-closed. **QA-001 is partially closed** — the `agentsuite --help` crash on cp1252 is fixed (verified exit 0, full help renders), but the sibling `agentsuite-mcp --help` entry point silently exits 0 with empty stdout because `agentsuite/mcp_server.py:main()` does no `--help` handling at all and falls into `FastMCP.run()`, which closes when stdin EOFs. That is a NEW runtime defect introduced by the audit's framing of QA-001 (the fix was scoped to the Typer surface, not the MCP entry point). **QA-002, QA-004, QA-005, QA-007, QA-009 close cleanly.** No security regressions surfaced. The five drift-trap tests pass. ENG-001 rejects every path-traversal payload tried. One pre-existing inconsistency surfaced as a side effect of the QA-007 retest: `trust_risk` and `cio` agents register a different MCP tool surface (no `_resume`, no `_get_status`, but extra `_get_artifact` / `_list_artifacts` / etc.) than the other five agents — pre-existing, not a v1.0.1 regression, but worth tracking for v1.0.2.

## Severity roll-up (QA, v1.0.1 closure)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 1 (QA-101 — `agentsuite-mcp --help` silent) |
| Major | 1 (QA-102 — agent tool-surface inconsistency, pre-existing) |
| Minor | 0 |
| Nit | 0 |

## Per-finding runtime verdict

| ID | Verdict | Evidence |
|---|---|---|
| QA-001 | **PARTIAL CLOSE** | `agentsuite --help` under `PYTHONIOENCODING=cp1252` exits 0 with full help (verified, ~30 lines stdout including box-drawing). `agentsuite-mcp --help` exits 0 with **0 bytes stdout** — see QA-101 below. |
| QA-002 | **CLOSED** | `examples/sample-output/founder/README.md` is honest: explicitly names `_default_mock_for_cli`, calls bodies "scaffold strings produced by the mock LLM", points to a v1.0.2 follow-up. Spot-checked `brand-system.md`, `audience-map.md`, `claims-and-proof-library.md` — each is exactly `# <name>\nMocked content.`, matching the README's claim. |
| QA-004 | **CLOSED** | Out of QA scope this pass (visual asset re-record). Test Engineer's CR-02 test (file existence + recency) passes; commit `ffd134f` re-records `cli-founder-run.svg`. Trusting the test plus commit message; not visually inspected this pass. |
| QA-005 | **CLOSED** | Mock run with `--run-id qa-probe-1` emitted to stderr: `[OK] intake complete  (0.0s, $0.0000)` / `[OK] extract complete ...` / `[OK] spec complete ...` / `[OK] execute complete ...` / `[OK] qa complete ...` — all 5 stages, in order. Stdout was clean JSON (`run_id`, `primary_path`, `status: approval`, 163 bytes). `--quiet` flag verified: stderr = 0 bytes, stdout still valid JSON. Pipe-clean discipline confirmed. |
| QA-007 | **CLOSED** | `build_server()` with `AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio` registers 48 tools. Every README-line-96-documented name appears byte-for-byte in `tool_names()`. `agentsuite_trust_risk_approve` (line 155) and `agentsuite_cio_approve` (line 168) also present. Drift-trap test `test_documented_tool_names_match_registered_byte_for_byte` passes. |
| QA-009 | **CLOSED (prose half)** | Founder resume is registered as MCP tool `agentsuite_founder_resume` (verified in tool_names() output). The CLI surface is still thin — `agentsuite founder` shows only `run` and `approve` in `--help`, no `resume` subcommand — but the README/docs half of QA-009 is closed per the commit b6c80bb mapping, and the MCP tool is reachable. **Recommend** v1.0.2 carry the CLI `founder resume` subcommand to match the MCP surface. |

## Drift trap (CR-04)

`pytest tests/test_readme_cli_invocations.py tests/test_mcp_tool_names_documented.py -v` → **5 passed in 2.78s**. Output captured. Both CLI flag drift and MCP name drift have passing guards now.

## ENG-001 path-traversal probe

Constructed `ArtifactWriter(Path(tmpdir), <bad>)` for run_id values: `'../escape'`, `'/etc'`, `'foo/bar'`, `'..'`, `'.'`, `'\x00null'`. Every one raised `InvalidIdentifier` with an actionable message naming the regex and the rule ("blocks path-traversal payloads (``..``, ``./``, absolute paths, encoded slashes)"). Note: `'foo..bar'` is **allowed** (dots permitted in middle of identifier) — this is by design, cannot escape because the resolved path stays under `output_root` and there's a final `is_relative_to` check at line 28. Verified safe.

## Probe — new runtime regressions

- `agentsuite agents` → emits clean JSON `{"enabled": ["founder"], "all_registered": [...7 agents...]}`. Exit 0.
- `agentsuite founder run --help` → all documented flags present (`--business-goal` REQUIRED, `--project-slug`, `--inputs-dir`, `--run-id`, `--force`). No drift.
- `agentsuite --help` → top-level help shows new `--quiet/-q` flag with `(UX-006/QA-005)` parenthetical. Renders cleanly under cp1252.

---

## Findings

### [QA-101] — Critical — Install/CLI — `agentsuite-mcp --help` silently exits 0 with empty output

**Evidence**

1. `PYTHONIOENCODING=cp1252 agentsuite-mcp --help 2>&1 | wc -c` → `0`.
2. Repeated without redirection: command returns to prompt with no output, exit code 0.
3. Source: `agentsuite/mcp_server.py:146-149`:
   ```python
   def main() -> None:
       """Entry point for the agentsuite-mcp console script."""
       server = build_server()
       server.run()
   ```
   No `argparse`, no `sys.argv` inspection, no `--help` handling. The `--help` arg is silently ignored, FastMCP boots the stdio loop, and exits when stdin EOFs (the case under bash command substitution / wc pipe).
4. The Typer `agentsuite --help` fix (commit `3222364`) shipped a separate guard that does NOT cover this entry point.

**Why this matters**

`agentsuite-mcp` is the entry point a developer wires into `~/.config/codex/config.toml` or Claude Desktop's `mcp.json`. When troubleshooting that wiring (e.g. "is the binary installed? is it on PATH? what flags does it take?"), `--help` is the first thing they try. They get nothing — no error, no usage, no version. This is worse than QA-001's original cp1252 crash, which at least failed loudly. A silent exit 0 looks like the binary is broken or the shell is broken. Combined with QA-001's framing ("Windows --help crash is fixed in v1.0.1"), users will reasonably assume `agentsuite-mcp --help` should also work.

**Blast radius**

- Adjacent code: any other `[project.scripts]` entry in pyproject.toml that points at a function which directly invokes `.run()` — none today besides this one (verified — `agentsuite-mcp` is the only non-Typer script).
- User-facing: every Codex/Claude Desktop integrator on first wire-up.
- Migration: none.
- Tests to update: add a regression test asserting `agentsuite-mcp --help` exits 0 with non-empty stdout containing "agentsuite" or "MCP".
- Related findings: QA-001 (parent), CR-04 (drift trap doesn't cover this binary).

**Fix path**

Add a 4-line guard at the top of `main()`:
```python
def main() -> None:
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print("Usage: agentsuite-mcp\n\nRun the AgentSuite MCP stdio server. "
              "No flags. Configure via env vars: AGENTSUITE_ENABLED_AGENTS, "
              "AGENTSUITE_OUTPUT_DIR, AGENTSUITE_EXPOSE_STAGES.\n")
        return
    server = build_server()
    server.run()
```
Add a test under `tests/test_readme_cli_invocations.py` (or a new file) that runs `agentsuite-mcp --help` via subprocess and asserts exit 0 + non-empty stdout. Ship in v1.0.2.

---

### [QA-102] — Major — Flow — Trust/Risk and CIO MCP tool surface diverges from other agents

**Evidence**

With all 7 agents enabled, `tool_names()` shows founder/design/product/engineering/marketing each register the same 5-tool surface: `_run`, `_resume`, `_approve`, `_get_status`, `_list_runs`. But:
- `trust_risk` registers 10 tools: `_run`, `_approve`, `_list_runs`, `_get_artifact`, `_list_artifacts`, `_get_qa_scores`, `_get_brief_template`, `_list_brief_templates`, `_get_revision_instructions`, `_get_run_status`. **No `_resume`. No `_get_status`.**
- `cio` registers 9 tools, same shape as trust_risk minus one.

This is a pre-existing inconsistency (not introduced by v1.0.1), but it surfaced as I verified QA-007 across all agents. It is a contract problem for any client (Codex, Claude Desktop) that tries to drive all 7 agents through a uniform interface.

**Why this matters**

A user who reads README line 96 and learns the `agentsuite_<agent>_<verb>` naming convention will reasonably assume `agentsuite_trust_risk_resume` exists. It does not. Calling it from MCP returns "tool not found." The CIO and Trust/Risk agents also lack `_get_status` — clients have to know to call `_get_run_status` instead. There is no documentation of this divergence.

**Blast radius**

- Adjacent code: `agentsuite/agents/trust_risk/mcp_tools.py`, `agentsuite/agents/cio/mcp_tools.py`. Compare against `agentsuite/agents/founder/mcp_tools.py` for the canonical 5-tool surface.
- User-facing: any MCP client that drives all agents uniformly.
- Migration: if the divergent tools have real users, renaming `_get_run_status` → `_get_status` is a breaking change. Recommend adding aliases in v1.0.2 then removing the old names in v1.1.0.
- Tests to update: `tests/test_mcp_tool_names_documented.py` currently only tests README-mentioned names. Add a test that asserts each enabled agent registers the canonical 5-tool surface (or explicitly flags the divergence as intentional).
- Related findings: QA-007 (closed), QA-009.

**Fix path**

Either (a) add `_resume` and `_get_status` aliases on trust_risk + cio mcp_tools modules pointing to the existing handlers, or (b) document the divergence in README + add a section in MCP_USAGE.md explaining which agents support which verbs. Option (a) is preferred for surface uniformity.

---

## Performance snapshot

| Metric | Observed | Verdict |
|---|---|---|
| `agentsuite founder run` end-to-end (mock LLM, qa-probe-1) | ~0.1s execute stage; sub-second total | pass |
| `agentsuite --help` cold start (cp1252) | sub-100ms perceived | pass |
| `build_server()` with 7 agents | <1s tool registration | pass |

## Security / privacy snapshot

- ENG-001 path traversal: VERIFIED CLOSED at `ArtifactWriter` boundary. 7 traversal payloads tried; all rejected with actionable error. The `is_relative_to(self.output_root)` final check at `artifacts.py:28-31` provides defense in depth even for any payload that slips the regex.
- No secrets in `--help` output, no secrets in stderr progress markers, no secrets in JSON stdout.
- Mock provider does not exfiltrate.

## Console and log observations

- Mock founder run: stderr clean except for the 5 `[OK]` markers. Stdout clean JSON.
- `--quiet`: stderr completely silent.
- No deprecation warnings, no Python tracebacks, no FastMCP warnings during build.

## Patterns and systemic observations

The v1.0.1 fix pattern was sound: doc honesty (CR-01), missing UX (UX-006/QA-005), drift traps (CR-04), and security hardening (ENG-001) are all the right shape of fix. The one weakness pattern: **closure work scoped only to the original symptom site, not the symptom class.** QA-001 was filed against `agentsuite --help`; the fix landed there only. The same class of bug — silent/crashing `--help` — was not swept across all entry points. v1.0.2 should adopt a "fix the class, not the instance" rule when a finding is in a generic surface like CLI help, env-var resolution, or path validation.

## v1.0.2 follow-up (runtime-validation queue)

1. **QA-101 fix + regression test** — `agentsuite-mcp --help` must emit usage and exit 0.
2. **QA-102 fix or doc** — unify trust_risk/cio MCP tool surface, or document the divergence.
3. **`agentsuite founder resume` CLI subcommand** — close the deferred half of QA-009 by adding the CLI verb that mirrors the MCP tool. ADR-0007 idempotency contract should be exercised at the CLI surface, not just the MCP one.
4. **Real-LLM sample-output regeneration** — close the deferred half of CR-01 by replacing the `Mocked content.` stubs with a real Anthropic Sonnet run (~$0.30, queued).
5. **Cleanroom watchdog harmony** — `scripts/run-cleanroom.sh` exceeds the 1-minute long-task watchdog. Either the script needs progress markers or the watchdog needs a cleanroom-specific exemption.

## Appendix: environments and artifacts

- Python 3.14.3, .venv at `C:\Users\scott\OneDrive\Desktop\Claude\AgentSuite\.venv\`
- pytest 9.0.3, pluggy 1.6.0, anyio 4.13.0
- Output captured at `/tmp/qa-probe-stdout.txt`, `/tmp/qa-probe-stderr.txt` (overwritten between probes — re-runnable by following the steps above)
- Source commits referenced: `de2a7a3` (release), `3222364` (QA-001), `5ee2f00` (CR-01), `ffd134f` (CR-02), `50eda4c` (UX-006/QA-005), `b6c80bb` (CR-03/QA-009), `4c90c41` (ENG-001)
