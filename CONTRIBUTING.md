# Contributing to AgentSuite

Thanks for your interest. AgentSuite is open-source under MIT.

## Development setup

```bash
git clone https://github.com/scottconverse/AgentSuite.git
cd AgentSuite
python -m venv .venv
# Windows:
.venv\Scripts\pip install -e ".[dev]"
# Mac/Linux:
# .venv/bin/pip install -e ".[dev]"
# Cross-platform alternative:
# python -m pip install -e ".[dev]"
pytest
```

You'll need Python 3.11 or 3.12. For the full doc-build pipeline you also need `pandoc` and (optionally) `mmdc` (mermaid-cli):

- pandoc: https://pandoc.org/installing.html
- mermaid-cli: `npm install -g @mermaid-js/mermaid-cli`

## Project standards

This project follows the global standards in `~/.claude/CLAUDE.md` and the project-scoped `CLAUDE.md` at the repo root. Highlights:

1. **UX > docs/QA > code.** User experience first, documentation second, code third.
2. **Hard Rule 9 — 6 doc artifacts must always exist** before any push: `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `.gitignore`, `docs/index.html`.
3. **Hard Rule 11 — commits >800 lines need an explicit tag** (`[INITIAL]`, `[LARGE-CHANGE]`, `[REFACTOR]`, etc.).
4. **No skipped tests.** `pytest.skip()` is forbidden in production tests. The only permitted skips are capability gates (e.g., `bash` not available on Windows for the cleanroom test) and cost gates (e.g., live tests opt-in via `RUN_LIVE_TESTS=1`).
5. **Tests for logic changes.** Every PR adds or updates ≥1 test for the changed behavior.
6. **vcr.py cassettes** are checked in and re-recorded only via `make rerecord-cassettes` with `RECORD_CASSETTES=1`.

## Test tiers

| Tier | Location | When | Cost |
|---|---|---|---|
| Unit | `tests/unit/` | every commit (CI on PR) | $0 |
| Integration | `tests/integration/` | every commit (CI on PR) | $0 (mock) |
| Golden | `tests/golden/` | every commit (CI on PR) | $0 (mock) |
| Cleanroom | `pytest -m cleanroom` | every PR | $0 (mock) or $5 cap (live) |
| Live | `tests/live/` (`RUN_LIVE_TESTS=1`) | release tag only | up to $10 total |

Run everything in mocked mode:

```bash
make test
```

Run cleanroom (mocked):

```bash
make cleanroom
```

Run live tier (release boundaries only — costs money):

```bash
RUN_LIVE_TESTS=1 make test-live
```

## Adding a new agent

The kernel is designed for the seven planned agents (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO). To add one:

1. Create `agentsuite/agents/<name>/` with `agent.py`, `input_schema.py`, `rubric.py`, `prompts/`, and `stages/`.
2. Subclass `BaseAgent` from `agentsuite/kernel/base_agent.py`. Implement `stage_handlers()` returning a dict for `intake`, `extract`, `spec`, `execute`, `qa` (the kernel handles `approval` and state persistence for you).
3. Build a domain-specific QA rubric using `QARubric(dimensions=[RubricDimension(...), ...], pass_threshold=...)`.
4. Add prompt templates in `prompts/*.jinja2`. The kernel's `prompt_loader` pattern is a starting point; copy and adapt.
5. Register in `agentsuite/agents/registry.py`'s `_bootstrap_default_registry()`.
6. Add MCP tool wiring in `<name>/mcp_tools.py` following the pattern in `agents/founder/mcp_tools.py`.
7. Tests: full unit coverage in `tests/unit/agents/<name>/`, golden snapshot in `tests/golden/<name>/`, integration test in `tests/integration/`.

## Testing

The default `pytest` invocation runs 688 of 691 tests; the three deselected tests (cleanroom, live, live_ollama) are gated by markers and documented in [`docs/test-coverage.md`](docs/test-coverage.md). Hard Rule 4a forbids skipped tests at v1.0 — `pytest.skip` and `@pytest.mark.skip` are not used.

## Pre-push gate

Before any `git push`:

```bash
bash scripts/verify-release.sh
```

This script runs all 8 checks (doc artifacts, version sync, CHANGELOG entry, lint, tests, cleanroom, build, secrets scan). Push only if it exits zero.

## Releases

1. Bump version in `pyproject.toml` AND `agentsuite/__version__.py` (single commit).
2. Add a CHANGELOG.md entry under `[Unreleased]`, then promote to `[X.Y.Z] — YYYY-MM-DD`.
3. Run `bash scripts/verify-release.sh` and `RUN_LIVE_TESTS=1 make test-live`.
4. Commit, tag (`git tag vX.Y.Z`), push tag.

AgentSuite does not publish to PyPI. Releases are distributed via GitHub only.

## Code style

- ruff for formatting and linting (`make lint`).
- mypy strict mode for type checking.
- Pydantic for all data shapes that cross module boundaries.
- Jinja2 for prompts and templates with `StrictUndefined` (fail loudly on missing variables).

## Regenerating golden snapshots

Golden tests in `tests/golden/` compare each agent's output to committed
snapshots under `tests/golden/snapshots/<agent>/<scenario>/`. v0.9.0 adds
content-aware fixtures (e.g. `brand-system.md`, `qa_scores.json`) on top
of the existing structural assertions.

When a deliberate prompt or template change shifts the rendered output:

1. Run `make update-goldens` (alias for `make resnap-golden`). The target
   sleeps 5s as a safety beat, then re-runs `pytest tests/golden -v` with
   `RESNAP=1` so the test runner overwrites the snapshot files in place.
2. Review the diff with `git diff -- tests/golden/snapshots/`. Every
   changed line should reflect the intended change. If you see drift you
   didn't intend, roll back instead of committing the snapshot.
3. Commit the snapshot changes alongside the prompt/template change in
   the same commit so the rationale lives in the same blame entry.

`make resnap-golden` and `make update-goldens` are equivalent — the
sprint plan named the alias.

## Architecture decisions

Load-bearing design decisions live in [`docs/adr/`](docs/adr/) as short
Architecture Decision Records. Read them before proposing a change that
crosses a recorded decision (rubric shape, RunState contract, retry
policy, MCP naming, cost-cap split, distribution channel, resume
semantics). New ADRs follow the template in [`docs/adr/README.md`](docs/adr/README.md).

For rubric changes specifically, also update [`docs/rubric-audit.md`](docs/rubric-audit.md) — it is the cross-reference source of truth backing ADR-0001.

## Reporting bugs

Open an issue at https://github.com/scottconverse/AgentSuite/issues with: Python version, OS, full traceback, the command you ran, and the contents of `.agentsuite/runs/<failing-run-id>/_state.json` if applicable.

## License

MIT.
