# AgentSuite Project Standards

This file extends `~/.claude/CLAUDE.md` with project-scoped rules.

## Project priority

UX > docs/QA > code (per global Hard Gate). For AgentSuite specifically:
- "User experience" = the experience of a developer wiring AgentSuite into Codex / Claude Code / Cowork via MCP.
- "Documentation" = the 6 doc artifacts (README, CHANGELOG, CONTRIBUTING, LICENSE, .gitignore, docs/index.html) plus README-FULL.pdf and USER-MANUAL.md.
- "Tests" = unit + integration + golden + cleanroom on every PR; live tests gated to v0.X.0 releases.

## Pre-push gates

- Run `scripts/verify-release.sh` before any push.
- Run `scripts/run-cleanroom.sh` (mocked LLM) before any push.
- All 6 doc artifacts must exist (Hard Rule 9).
- Commits >800 lines must include a `[LARGE-CHANGE]` / `[REFACTOR]` / `[INITIAL]` tag (Hard Rule 11).

## Testing discipline

- No `pytest.skip` / `@pytest.mark.skip` / `xit` (Hard Rule 4a). Set up fixtures in `conftest.py` instead.
- vcr.py cassettes are checked in. Re-record only via `make rerecord-cassettes` with `RECORD_CASSETTES=1`.
- Live tests run only at v0.X.0 release tags with `RUN_LIVE_TESTS=1` and a `$10` total cap.

## Output convention

Agent output goes to `.agentsuite/` in the calling project's CWD (configurable via `AGENTSUITE_OUTPUT_DIR`). Never write to AgentSuite's own repo dir during execution.
