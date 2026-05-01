# AgentSuite v1.0.5 — Sprint Punch List

**Project:** AgentSuite v1.0.5
**Audit date:** 2026-04-30
**Sprint:** Current (close-of-sprint fixes)
**Total punch list items:** 11
**Total audit findings:** 57 (0B / 6C / 20M / 19m / 12n)

> Items the dev team should fix before close of sprint. Sorted by severity then effort.
> Each entry includes: ID, Severity, Size, Owner hint, Description, and Fix path.

---

## Summary Table

| ID | Severity | Size | Title |
|----|----------|------|-------|
| TEST-001 | Critical | S | Stress suite excluded from CI |
| ENG-001 | Critical | M | Path traversal in CIO + trust_risk MCP tools |
| UX-002 | Critical | M | RevisionRequired dead end — no recovery path |
| QA-001 | Critical | S | Auth errors silently retried 3x before failing |
| DOC-002 | Critical | S | USER-MANUAL version contradiction |
| UX-001 + DOC-005 | Critical | S | Landing page version and roadmap stale |
| ENG-005 + UX-005 | Major | S | Cost soft-warn threshold never surfaced to operator |
| ENG-006 + QA-007 | Major | S | extract_json rfind fallback broken when prose contains `{` |
| QA-005 | Major | S | AGENTSUITE_ENABLED_AGENTS misconfiguration raises unhandled traceback |
| DOC-004 | Major | S | CHANGELOG comparison links frozen at v0.9.1 |
| DOC-001 + QA-002 | Major | S | README version badge shows v1.0.3 |

---

## Detailed Entries

---

### 1. TEST-001 — Stress suite excluded from CI

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Size** | S (1 line) |
| **Owner** | Test Engineer |

**Description**
`.github/workflows/test.yml` runs only `tests/unit tests/integration tests/golden`. The 87-test stress suite (`tests/stress/`) never gates a PR.

**Fix**
In `.github/workflows/test.yml`, add `tests/stress` to the pytest invocation. One-line change. Verify CI goes green.

---

### 2. ENG-001 — Path traversal in CIO + trust_risk MCP tools

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Size** | M |
| **Owner** | Principal Engineer |

**Description**
`artifact_name` and `template_name` parameters in CIO and trust_risk `mcp_tools.py` are passed directly to `open(run_dir / artifact_name)` with no validation. Any caller can read arbitrary `.md` files outside the run directory.

**Fix**
Add an allowlist or `pathlib` containment check. Resolve the path, confirm it is within `run_dir`, raise `ValueError` otherwise. Cover with a unit test.

Files:
- `agentsuite/agents/cio/mcp_tools.py`
- `agentsuite/agents/trust_risk/mcp_tools.py`

---

### 3. UX-002 — RevisionRequired dead end — no recovery path

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Size** | M |
| **Owner** | UX Designer + Principal Engineer |

**Description**
When `approval.py` raises `RevisionRequired`, the CLI prints a vague error with no instructions. MCP tools propagate an unhandled exception. Users have no way to proceed.

**Fix**
- CLI: catch `RevisionRequired`, print the revision notes, and print a clear "re-run the agent with revised inputs" instruction.
- MCP: catch and return structured error JSON with a `revision_notes` field.
- Add a test that exercises this path.

---

### 4. QA-001 — Auth errors silently retried 3x before failing

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Size** | S |
| **Owner** | QA Engineer + Principal Engineer |

**Description**
`RetryingLLMProvider._NO_RETRY_EXCEPTIONS` does not include provider authentication error types (`anthropic.AuthenticationError`, `google.auth.exceptions.TransportError` / API auth errors, `openai.AuthenticationError`). A bad API key causes a 3-second retry loop before the real error surfaces.

**Fix**
Add the provider-specific auth exception classes to `_NO_RETRY_EXCEPTIONS` in `agentsuite/llm/retrying.py`. Test with a bad key to confirm immediate failure.

---

### 5. DOC-002 — USER-MANUAL version contradiction

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Size** | S |
| **Owner** | Technical Writer |

**Description**
`USER-MANUAL.md` footer says "v0.9.1" but the version header says "v1.0.2". Both are wrong (actual: v1.0.5). Draft patch file ready at `dev-reports/audit-AgentSuite-2026-04-30-v105/doc-rewrites/USER-MANUAL-version-patch.md`.

**Fix**
Apply the patch file. Find-replace all version strings to "v1.0.5". Verify no other stale version references remain.

---

### 6. UX-001 + DOC-005 — Landing page version and roadmap stale

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Size** | S |
| **Owner** | UX Designer + Technical Writer |

**Description**
`docs/index.html` shows a v1.0.1 badge. The roadmap section lists shipped features as "coming soon." Patch file ready at `dev-reports/audit-AgentSuite-2026-04-30-v105/doc-rewrites/index.html-version-roadmap-patch.html`.

**Fix**
Apply patch. Update version badge to v1.0.5. Move shipped roadmap items to "Shipped" or remove them.

---

### 7. ENG-005 + UX-005 — Cost soft-warn threshold never surfaced to operator

| Field | Value |
|-------|-------|
| **Severity** | Major |
| **Size** | S |
| **Owner** | Principal Engineer + UX Designer |

**Description**
`CostTracker.warned` flag is set correctly when spend exceeds `soft_warn_usd`, but no message is emitted to stderr during the run. Operators get zero real-time cost signal.

**Fix**
In `agentsuite/core/cost.py`, emit the following when `warned` is first set:

```python
print(f"[COST WARNING] Spend ${amount:.4f} exceeded soft warn threshold ${threshold:.4f}", file=sys.stderr)
```

Add a test.

---

### 8. ENG-006 + QA-007 — extract_json rfind fallback broken when prose contains `{`

| Field | Value |
|-------|-------|
| **Severity** | Major |
| **Size** | S |
| **Owner** | Principal Engineer + QA Engineer |

**Description**
`extract_json()` fallback uses `find('{')` + `rfind('}')`. When LLM prose contains a `{` before the real JSON object, the slice is wrong and JSON parsing fails. Affects all 7 agents.

**Fix**
Replace the fallback with a regex scan (`re.findall(r'\{.*\}', text, re.DOTALL)`) that finds the last valid JSON object. Update tests.

File: `agentsuite/core/extract_json.py` (or wherever `extract_json` lives).

---

### 9. QA-005 — AGENTSUITE_ENABLED_AGENTS misconfiguration raises unhandled traceback

| Field | Value |
|-------|-------|
| **Severity** | Major |
| **Size** | S |
| **Owner** | QA Engineer |

**Description**
An invalid agent name in `AGENTSUITE_ENABLED_AGENTS` raises an unhandled exception in both CLI and MCP server. No user-friendly error.

**Fix**
Validate enabled agent names at startup against the known agent registry. Raise a descriptive `ConfigurationError` listing valid agents. Cover with a test.

---

### 10. DOC-004 — CHANGELOG comparison links frozen at v0.9.1

| Field | Value |
|-------|-------|
| **Severity** | Major |
| **Size** | S |
| **Owner** | Technical Writer |

**Description**
`CHANGELOG.md` footer comparison links stop at v0.9.1 — ten versions (v1.0.0 through v1.0.5) are missing. Patch file ready at `dev-reports/audit-AgentSuite-2026-04-30-v105/doc-rewrites/CHANGELOG-footer-links.md`.

**Fix**
Apply patch. Add comparison links for:
- v1.0.0 → v1.0.1
- v1.0.1 → v1.0.2
- v1.0.2 → v1.0.3
- v1.0.3 → v1.0.4
- v1.0.4 → v1.0.5

---

### 11. DOC-001 + QA-002 — README version badge shows v1.0.3

| Field | Value |
|-------|-------|
| **Severity** | Major |
| **Size** | S |
| **Owner** | Technical Writer + QA Engineer |

**Description**
`README.md` badge shows v1.0.3. Actual version is v1.0.5.

**Fix**
Update the badge URL to v1.0.5. One-line change.

---

## Blast-Radius Notes

The following fixes carry cross-cutting risk and require targeted regression verification after applying.

**ENG-001 (path traversal)**
Changes MCP tool behavior — any caller that was (incorrectly) reading files outside `run_dir` will now receive an error. Run all CIO and trust_risk MCP integration tests after applying this fix.

**UX-002 (RevisionRequired)**
Changes CLI exit behavior. Verify that existing approval-stage unit tests still pass and that the new error output format is captured in the help text.

**QA-001 (auth retry)**
Changes retry behavior for auth errors only. Regression-test the full retry suite to confirm transient (non-auth) errors still retry normally.

**ENG-006 + QA-007 (extract_json)**
Touches all 7 agents indirectly via the shared `extract_json` utility. Run the full golden test suite after applying this fix to verify no regressions.
