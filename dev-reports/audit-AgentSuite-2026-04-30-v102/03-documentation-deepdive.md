# Documentation Deep-Dive — AgentSuite v1.0.2-dev (Post-Sprint Audit)

**Role:** Technical Writer  
**Date:** 2026-04-30  
**Scope:** All 6 required doc artifacts, code comments, error message accuracy  

---

## What's Working Well

- **CHANGELOG is Keep a Changelog compliant.** The `[1.0.2] - Unreleased` entry is detailed, categorized correctly (Added/Fixed), and explains *why* each fix matters — not just what changed. Developers upgrading will understand the blast radius.
- **README.md "five-stage pipeline" correction is complete.** All 7 instances of "six-stage" were replaced. Cross-references between stages and approval are now correctly described.
- **`agentsuite/agents/_common.py` module docstring is excellent.** It explains what the module is for, why it exists, and what problem it solves in plain language. The kind of comment that pays for itself when a new developer extends the codebase.
- **`agentsuite/kernel/identifiers.py` module docstring is thorough.** Character classes, why dots are permitted in the middle, what `..` does to the path — all explained. A code reviewer can verify the security fix without reading the regex.
- **All 6 required artifacts exist on disk:** README.md ✓, CHANGELOG.md ✓, CONTRIBUTING.md ✓, LICENSE ✓, .gitignore ✓, docs/index.html ✓.

---

## Findings

### CRITICAL — DOC-301: USER-MANUAL.md version badge is 3 versions stale

**Category:** Accuracy  
**Severity:** Critical  
**Evidence:** `USER-MANUAL.md:3`: `**Version 0.9.1**`. Current released version is 1.0.1. A user reading the manual to troubleshoot a 1.0.x installation sees version 0.9.1 at the top and immediately distrusts the content.

**Blast radius:** USER-MANUAL.md is linked from README.md and docs/index.html. It is the primary destination for non-developer users.

**Fix path:** Update version badge. Audit the 984-line manual for any procedures that changed since 0.9.1 (new flags `--force`, `--quiet`, `--latest`; schema version error behavior; MCP tool naming changes).

---

### MAJOR — DOC-302: Version skew between CHANGELOG and package files

**Category:** Release hygiene  
**Severity:** Major  
**Evidence:** CHANGELOG declares `[1.0.2] - Unreleased`. `pyproject.toml:7` and `agentsuite/__version__.py:1` both say `1.0.1`. `README.md:5` says `v1.0.1`. The package self-reports a version that contradicts the CHANGELOG entry describing the sprint's work as already done.

**Fix path:** Bump `pyproject.toml`, `agentsuite/__version__.py`, and `README.md` to `1.0.2` in the same commit as the fixes, so all three sources agree.

---

### MAJOR — DOC-303: No developer documentation for `_common.py` helpers

**Category:** Completeness  
**Severity:** Major  
**Evidence:** `CONTRIBUTING.md` does not mention `require_run_dir` or `require_kernel_dir`. A developer adding a new agent will not know to use these helpers and will likely repeat the unsafe raw path construction that the helpers were designed to eliminate.

**Blast radius:** Every future agent module written without this knowledge re-opens the ENG-001 class of path-traversal vulnerability.

**Fix path:** Add a "Security: path validation" section to CONTRIBUTING.md naming both helpers as required for any code that constructs paths from user-supplied `run_id` or `project_slug`. Cross-reference `agentsuite/agents/_common.py`.

---

### MINOR — DOC-304: USER-MANUAL.md does not document `--force`, `--quiet`, `--latest` flags

**Category:** Completeness  
**Severity:** Minor  
**Evidence:** These user-facing flags were added in v0.9.x/v1.0.x. The manual (last updated for 0.9.1) does not describe any of them. A non-developer user who wants to suppress progress output or re-run a failed run won't find the information.

**Fix path:** Add a "CLI Flags Reference" section to USER-MANUAL.md covering all currently available flags with plain-language explanations.

---

### MINOR — DOC-305: `agentsuite migrate` referenced in warning but not implemented or documented

**Category:** Accuracy  
**Severity:** Minor  
**Evidence:** `mcp_server.py:133` warning recommends `agentsuite migrate` which does not exist. No documentation mentions it anywhere.

**Fix path:** Either implement the stub command and document it, or update the warning to say "delete {run_dir} and re-run."

---

## Severity Counts

| Severity | Count |
|----------|-------|
| Critical | 1 |
| Major | 2 |
| Minor | 2 |
| Nit | 0 |

---

## Summary

Source-code docstrings are informative and audit-ready. The primary consumer doc (README) pipeline description is now accurate. Weaknesses concentrate in USER-MANUAL.md (version staleness, missing flags) and developer onboarding (no documentation of `_common.py` helpers). The version skew between CHANGELOG and package files is the most operationally confusing gap — a developer cannot tell whether the 1.0.2 work is shipped or in-progress.
