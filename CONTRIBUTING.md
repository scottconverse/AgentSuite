# Contributing to AgentSuite

Thanks for your interest. AgentSuite is open-source under MIT.

## Development setup

```bash
git clone https://github.com/scottconverse/AgentSuite.git
cd AgentSuite
python -m venv .venv
.venv/Scripts/pip install -e .[dev]
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
5. CI builds and uploads to PyPI on tag push.

Per `feedback_pypi_push.md`: every GitHub push of an AgentSuite release is paired with a PyPI publish.

### One-time PyPI Trusted Publishing setup

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new pending publisher:
   - PyPI Project Name: `agentsuite`
   - Owner: `scottconverse`
   - Repository: `AgentSuite`
   - Workflow: `release.yml`
   - Environment: (leave blank)
3. After the first release, the publisher becomes active automatically.

## Code style

- ruff for formatting and linting (`make lint`).
- mypy strict mode for type checking.
- Pydantic for all data shapes that cross module boundaries.
- Jinja2 for prompts and templates with `StrictUndefined` (fail loudly on missing variables).

## Reporting bugs

Open an issue at https://github.com/scottconverse/AgentSuite/issues with: Python version, OS, full traceback, the command you ran, and the contents of `.agentsuite/runs/<failing-run-id>/_state.json` if applicable.

## License

MIT.
