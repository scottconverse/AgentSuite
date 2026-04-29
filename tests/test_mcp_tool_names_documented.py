"""Drift gate: documented MCP tool names must match the live registration.

Builds the AgentSuite MCP server, extracts the registered tool names, and
compares them against tool-name-shaped strings inside inline backticks across
README, USER-MANUAL, troubleshooting, the docs landing page, the press kit,
and the community drafts.

A failing test means a doc names a tool the server doesn't expose. v1.0.0 GA
shipped with this gap (CR-03): README documents ``founder_run`` while the
registered name is ``agentsuite_founder_run`` (and ``trust-risk_run`` is
documented vs. the registered ``agentsuite_trust_risk_run``).

This is the second half of the v1.0.1 drift trap (CR-04). Together with
``test_readme_cli_invocations.py``, every prose-level reference to a public
AgentSuite surface — CLI flags or MCP tools — now falls under a CI gate.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "USER-MANUAL.md",
    REPO_ROOT / "docs" / "troubleshooting.md",
    REPO_ROOT / "docs" / "index.html",
    REPO_ROOT / "docs" / "press-kit" / "README.md",
    REPO_ROOT / "docs" / "community" / "discussions-seeds.md",
    REPO_ROOT / "docs" / "community" / "launch-posts.md",
]

# A tool-name-shaped token inside a backtick span.
# Matches:
#   agentsuite_founder_run                — canonical registered form
#   founder_run                           — shortened
#   trust-risk_run                        — hyphenated (drift; audit-flagged)
#   agentsuite_trust_risk_get_artifact    — multi-word verb
# The verb suffix list is the public set of MCP verbs registered across all
# seven agents — keep this in lockstep with the agent mcp_tools modules.
_TOOL_VERBS = (
    "run",
    "resume",
    "approve",
    "list_runs",
    "list_artifacts",
    "get_artifact",
    "get_qa_scores",
    "get_brief_template",
    "list_brief_templates",
    "get_revision_instructions",
    "get_run_status",
    "get_status",
)
_TOOL_AGENTS = (
    "founder",
    "design",
    "product",
    "engineering",
    "marketing",
    "trust_risk",
    "trust-risk",
    "cio",
)
_TOOL_NAME_RE = re.compile(
    r"`((?:agentsuite_)?(?:" + "|".join(_TOOL_AGENTS) + r")_(?:" + "|".join(_TOOL_VERBS) + r"))`"
)


def _expected_form(name: str) -> str:
    """Return what the documented name *should* have been.

    Strict mode: documented tool names must match the registered name byte
    for byte, because users paste the documented string into their MCP
    client config and AgentSuite does not accept a shortened form. The
    expected form is ``agentsuite_<agent>_<verb>`` with underscores.
    """
    name = name.replace("trust-risk", "trust_risk")
    if not name.startswith("agentsuite_"):
        name = "agentsuite_" + name
    return name


def _doc_relpath(p: Path) -> str:
    return p.relative_to(REPO_ROOT).as_posix()


@pytest.fixture(scope="module")
def registered_tool_names(monkeypatch_module: pytest.MonkeyPatch) -> list[str]:
    """Build the MCP server with all 7 agents enabled; return registered tool names.

    The default registry only enables Founder; the other six agents register
    via ``AGENTSUITE_ENABLED_AGENTS``. The docs reference tool names from
    every agent (which is correct — they're documenting the full surface a
    user can opt into), so the drift gate must validate against the
    *full* registered superset, not the default-enabled subset.

    Skips cleanly if the [mcp] extra is not installed.
    """
    pytest.importorskip(
        "mcp.server.fastmcp",
        reason="MCP SDK not installed — install with `pip install agentsuite[mcp]`",
    )
    monkeypatch_module.setenv(
        "AGENTSUITE_ENABLED_AGENTS",
        "founder,design,product,engineering,marketing,trust_risk,cio",
    )
    # Reset the cached default_registry so the new env var is honored.
    import agentsuite.agents.registry as registry_module

    monkeypatch_module.setattr(registry_module, "_DEFAULT_REGISTRY", None)

    from agentsuite.mcp_server import build_server

    server = build_server()
    return server.tool_names()


@pytest.fixture(scope="module")
def monkeypatch_module() -> pytest.MonkeyPatch:
    """Module-scoped monkeypatch (the default fixture is function-scoped)."""
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


def _iter_doc_tool_mentions() -> list[tuple[Path, int, str]]:
    """Yield (file, line_no, raw_tool_name_inside_backticks) tuples."""
    out: list[tuple[Path, int, str]] = []
    for doc in DOC_FILES:
        if not doc.exists():
            pytest.fail(f"Doc file expected but missing: {doc}")
        lines = doc.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, start=1):
            for match in _TOOL_NAME_RE.findall(line):
                out.append((doc, i, match))
    return out


def test_at_least_one_tool_name_documented() -> None:
    """Sanity: regex extraction returns non-empty across the doc set."""
    mentions = _iter_doc_tool_mentions()
    assert len(mentions) > 0, (
        "No MCP tool-name-shaped backtick spans found across "
        f"{[_doc_relpath(p) for p in DOC_FILES]}. "
        "If the docs really mention zero tool names that's the bigger "
        "problem; if they do, the regex in this test is broken."
    )


def test_documented_tool_names_match_registered_byte_for_byte(
    registered_tool_names: list[str],
) -> None:
    """Every tool name in inline backticks must equal a registered name exactly.

    Users paste the documented string verbatim into their MCP client config.
    AgentSuite does not accept a shortened or hyphenated form. So the test
    is strict: ``founder_run`` is drift even though it ``looks like`` the
    real tool — pasting it into Claude Code or Codex will fail to resolve.
    """
    registered = set(registered_tool_names)
    failures: list[str] = []
    seen: set[tuple[str, str]] = set()  # de-dupe (file, raw) per run
    for doc, line_no, raw in _iter_doc_tool_mentions():
        if raw in registered:
            continue
        key = (_doc_relpath(doc), raw)
        if key in seen:
            continue
        seen.add(key)
        expected = _expected_form(raw)
        # If even after canonicalization the name doesn't exist, the doc
        # is referencing a tool that doesn't exist at all — distinct error.
        if expected not in registered:
            failures.append(
                f"  {_doc_relpath(doc)}:{line_no}: `{raw}` — "
                f"no such tool is registered (canonical form `{expected}` also missing)."
            )
        else:
            failures.append(
                f"  {_doc_relpath(doc)}:{line_no}: `{raw}` — drift; "
                f"the registered form is `{expected}`. Update the doc."
            )
    if failures:
        sample_registered = "\n".join(f"    {n}" for n in sorted(registered)[:20])
        pytest.fail(
            "Documented MCP tool names do not match the live registration "
            "byte-for-byte:\n"
            + "\n".join(failures)
            + "\n\n  Registered names (sample, sorted):\n"
            + sample_registered
            + "\n\nFix: update the docs to use the literal `agentsuite_<agent>_<verb>` form. "
            "Do NOT rename registered tools — breaks the v1.0 compat freeze."
        )
