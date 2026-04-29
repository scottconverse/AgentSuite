# v1.0.1 Sprint Punch List

**Source:** Audit-team pass against `v1.0.0` at `9540957`, dated 2026-04-29.
**Scope:** Blockers + Criticals + cheap-or-urgent Majors. Structural and long-lived Majors are in [`next-sprint-watchlist.md`](next-sprint-watchlist.md).
**Sort:** by priority (Blockers first, then Criticals by leverage, then high-leverage Majors).

Each item: ID, title, severity, owner-hint role, one-line "what to do," size (S/M/L), and pointer to the deep-dive entry for full evidence/blast-radius.

---

## Blockers (must close before v1.0.1)

| # | ID(s) | Title | Owner | What to do | Size |
|---|---|---|---|---|---|
| 1 | CR-01 (UX-001 + QA-002 + DOC-S01) | Mocked content shipped as real GA output | UX + Engineering | Run real LLM Founder pass against patentforgelocal fixture, commit to `examples/sample-output/founder/`, regenerate `brand-system-rendered.svg` + `qa-report-rendered.svg` from real markdown. Update `examples/sample-output/founder/README.md` to drop "exactly what a live run produces" claim or qualify precisely. | S |
| 2 | QA-001 | Windows `agentsuite --help` UnicodeEncodeError | Engineering | Replace U+2192 right-arrow + U+2014 em-dash in `agentsuite/cli.py:18` with ASCII (`->` and `--`), or set typer's stdout to UTF-8 explicitly. Add Windows job to release.yml smoke matrix. | S |
| 3 | CR-02 (DOC-S02 + UX-003 + UX-004 + QA-004) | Hero CLI screenshot uses non-existent flags + fake stage messages | UX + Engineering | Re-record `cli-founder-run.svg` from a real `agentsuite founder run` invocation against mock LLM. Capture actual stdout. Use `--business-goal --project-slug --inputs-dir`. Drop the synthetic `✔ stage complete` markers (CLI doesn't emit them) or implement the markers in CLI per UX-006/QA-005 design. | S-M |
| 4 | DOC-001 | Compat-freeze locks 6-stage pipeline; code is 5 stages | Tech Writer | Edit `CHANGELOG.md` v1.0.0 entry "Kernel pipeline" line: `intake → extract → spec → execute → qa` (five stages). Approval is a kernel-managed transition, not a pipeline stage. Note this in v1.0.1 CHANGELOG as a documentation correction, not an API change. | S |
| 5 | DOC-006 | `docs/README-FULL.pdf` 4 broken links | Tech Writer | Either (a) move the PDF from repo root into `docs/` (preserves linked refs), or (b) edit the 4 referencing files (CONTRIBUTING.md, docs/index.html, USER-MANUAL.md, README.md per the deep-dive) to point to `README-FULL.pdf` at repo root. Pick (a) — fewer touch points. | S |

---

## Criticals (must close before v1.0.1)

| # | ID | Title | Owner | What to do | Size |
|---|---|---|---|---|---|
| 6 | ENG-001 | MCP path traversal via run_id / project_slug | Engineering | Add validation in `kernel/artifacts.py::ArtifactWriter.__init__` and any path-construction sites: assert `run_id`/`project_slug` matches `^[a-zA-Z0-9_-]+$`, normalize via `Path.resolve()`, assert resolved path is inside `output_root`. Test with `..`, absolute paths, encoded slashes. | M |
| 7 | ENG-002 | Cost telemetry silent fallback on aliased model IDs | Engineering | In `agentsuite/llm/pricing.py`: replace silent default with `KeyError` raise OR explicit fallback flag in cost_summary.json. In each provider, normalize `result.model` to canonical pricing-table key before lookup. Add unit test: feed each provider its actual response model strings, assert pricing-table hit. | M |
| 8 | CR-03 (UX-002 + QA-007 + DOC-009/S03) | MCP tool name drift: README says `founder_run`, registry says `agentsuite_founder_run`; `trust-risk` vs `trust_risk` | Tech Writer | Drop `doc-rewrites/README-mcp-section.md` into README. Update `docs/USER-MANUAL.md` MCP examples in same pass. Update `docs/community/discussions-seeds.md` Q&A and `launch-posts.md` MCP Discord block. **Do not rename registered tools** (breaks compat-freeze). | S |
| 9 | TEST-001 | Cassettes never landed; integration tier is mock-only | Test Engineering | Either (a) re-record cassettes for at least Founder under all 4 providers (ANTHROPIC/OPENAI/GEMINI/OLLAMA) into `tests/integration/cassettes/`, or (b) explicitly retire the vcr scaffold and update `docs/test-coverage.md` to state integration tier is intentionally mock-only. Pick (b) for v1.0.1; (a) is a v1.1 spike — see watchlist. | S (for b) |
| 10 | CR-04 (TEST-004) | No CI test pins README CLI / MCP names to running code | Test Engineering | Add `tests/test_readme_cli_invocations.py` that parses bash blocks from README/USER-MANUAL, extracts `agentsuite ... run` lines, validates flag names against the live Typer schema. Add `tests/test_mcp_tool_names_documented.py` that diffs registered tool names against names in README/USER-MANUAL. Both fail with clear messages. | M |
| 11 | UX-006 + QA-005 | CLI silent during long LLM phases | Engineering + UX | Emit stage progress to stderr (so JSON stdout stays clean): `✔ <stage> complete` with elapsed time and running cost. Gate behind `--quiet` flag (already on the good-first-issue list). | M |
| 12 | TEST-006 | release.yml clean-install-check does NOT validate wheel-install mypy (claim refuted) | Test Engineering | Either (a) add a mypy step to release.yml's clean-install-check job that imports AgentSuite from the wheel and runs mypy --strict on a tiny consumer, or (b) update CHANGELOG and `tests/integration/test_downstream_consumer.py` docstring to remove the false claim that the wheel-install path is verified there. (a) preferred — small CI addition. | S-M |

---

## High-leverage Majors (cheap or urgent enough to do now)

| # | ID | Title | Owner | What to do | Size |
|---|---|---|---|---|---|
| 13 | ENG-003 | Default model IDs may not exist on live API | Engineering | Audit `agentsuite/llm/{anthropic,openai,gemini}.py` default model strings (`claude-sonnet-4-6`, `gpt-5.4`, etc.) against current provider model lists. Replace with conservatively-current defaults. Add a smoke test that hits each provider's `/models` endpoint weekly via the existing provider-drift workflow. | S |
| 14 | ENG-004 | Ollama auto-detect uses HEAD on a GET-only endpoint | Engineering | Change probe from HEAD to GET in `agentsuite/llm/ollama.py`. Test with running daemon. | S |
| 15 | ENG-005 | OpenAI provider sends deprecated `max_tokens`; reasoning models expect `max_completion_tokens` | Engineering | Switch parameter name in `agentsuite/llm/openai.py`. Verify with current OpenAI SDK version. | S |
| 16 | TEST-003 | MockLLMProvider keyword-substring matcher silently masks prompt drift | Test Engineering | Tighten the matcher: require unique-substring match per response, fail loudly on no-match instead of returning the default. Or switch to exact-prompt-hash matching with a regenerator. | M |
| 17 | DOC-S04 | Missing SECURITY.md (no security policy / disclosure path) | Tech Writer | Drop `doc-rewrites/SECURITY.md` into repo root. | S |

---

## Sprint shape

**Total items:** 17 (5 Blockers + 7 Criticals + 5 Majors)
**Total size:** 5 S, 5 S-M, 7 M = comfortable for one focused 1-2 week sprint.
**Critical path:** CR-04 (drift tests) blocks confident regeneration of CR-01 + CR-02 + CR-03 — write the tests first so the regenerated artifacts are pinned in CI from day one of v1.0.1.

**Suggested commit sequence:**
1. CR-04 first (test additions; reveals every existing drift item)
2. QA-001 + ENG-001 + ENG-002 (security + Windows install Blockers; independent of doc work)
3. CR-01 + CR-02 + CR-03 + DOC-001 + DOC-006 (one big "regenerate storefront" commit)
4. UX-006 / QA-005 (CLI progress; design + implement)
5. ENG-003/004/005 + TEST-003 + TEST-006 + DOC-S04 (cleanup)
6. Tag `v1.0.1` with full CHANGELOG entry citing each closed audit ID.

**Acceptance for v1.0.1 tag:**
- Every Blocker and Critical from this list closed
- New CI tests (CR-04) green
- Re-run audit-team's UI/UX + QA spot-check against the storefront before tagging
- CHANGELOG entry credits every audit ID closed (`closes UX-001, QA-002, DOC-S01` etc.)
