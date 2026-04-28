# ADR-0006: No-PyPI distribution policy

**Status:** Accepted
**Date:** 2026-04-28

## Context

AgentSuite is a developer-facing tool that wires into MCP hosts (Codex,
Claude Code, Cowork) on a developer's machine. The natural distribution
channel for a Python package is PyPI — `pip install agentsuite` is what
contributors expect to run. However, AgentSuite ships rapid breaking
changes during the pre-1.0 sprint cycle, depends on optional provider
SDKs whose own version pinning is volatile, and pulls in agent prompt
templates whose layout drifts release-to-release. Publishing each
intermediate release to PyPI would create a slow-moving public API
contract on a fast-moving private one.

## Decision

AgentSuite is distributed only as GitHub releases (wheels + sdist
attached to `gh release`) plus the Git repo itself. There is no PyPI
publish step in `release.yml`. Users install via `pip install
git+https://github.com/scottconverse/AgentSuite.git@v<version>` or by
downloading the wheel from a GitHub Release. This holds at least
through v1.0; reopen this ADR after v1.0 if a stable PyPI publish makes
sense alongside a slower release cadence.

## Consequences

- Installation instructions are slightly more verbose than `pip install
  agentsuite`. Documentation must state the GitHub URL pattern
  prominently and explain why.
- `pyproject.toml` still ships the metadata (description, classifiers,
  authors) so a future PyPI flip is a one-step change, not a refactor.
- Supply-chain audit happens at the GitHub Release level (`pip-audit` +
  CycloneDX SBOM attached to each release per ADR-0005's neighbor in
  v0.8.3). Downstream consumers verify the wheel's SBOM, not the PyPI
  package's.
- Users who need a package-manager-installable build can build the
  wheel locally from the tagged source.
