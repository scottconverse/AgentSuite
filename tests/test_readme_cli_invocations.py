"""Drift gate: documented CLI invocations must match the live Typer schema.

Parses fenced bash blocks from `README.md` and `docs/USER-MANUAL.md`, extracts
every `agentsuite <agent> <subcommand>` invocation along with its long flags,
and validates each flag against the Typer app's introspected parameter list.

A failing test means a doc says the user can run something the CLI cannot
actually accept. v1.0.0 GA shipped with this gap (CR-04) — the install-block
drift check pattern only covered one specific README block. This generalizes
the same idea to every documented CLI invocation.

Verbatim doc strings remain part of the public contract: change the docs to
match the CLI, or change the CLI to match the docs, in the same commit.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import typer

from agentsuite.cli import app


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "USER-MANUAL.md",
    REPO_ROOT / "docs" / "troubleshooting.md",
]
SVG_FILES = sorted((REPO_ROOT / "docs" / "screenshots").glob("*.svg"))

# Match a fenced block opening with a shell-ish language tag.
_FENCE_OPEN = re.compile(r"^\s*```(?:bash|sh|console|shell)\s*$")
_FENCE_CLOSE = re.compile(r"^\s*```\s*$")

# Match the start of an `agentsuite <subcommand>` line. Optional shell
# prompt prefixes (e.g. ``$ ``) are allowed; pipes and redirects after the
# command are ignored.
_INVOCATION_RE = re.compile(r"^\s*(?:\$\s+)?agentsuite\s+(\S+)(?:\s+(\S+))?(.*)$")

# A long-form flag inside a command (skip values, skip short flags, skip
# placeholder tokens like ``<flag>``).
_LONG_FLAG_RE = re.compile(r"--([a-zA-Z][a-zA-Z0-9_-]*)")


# Match an `agentsuite ...` substring inside a backtick-quoted span. Captures
# everything up to the closing backtick or the end of the line.
_INLINE_BACKTICK_RE = re.compile(r"`((?:\$\s+)?agentsuite[^`]*?)`")

# SVG text content: rich's terminal-style SVGs put each rendered terminal line
# inside one or more <text> nodes. We rejoin per-line text content (across
# multiple <text ...>...</text> spans on the same line) before scanning.
_SVG_TEXT_RE = re.compile(r"<text[^>]*>([^<]*)</text>")
_SVG_LINE_GROUP_RE = re.compile(r'clip-path="url\(#[^"]*?-line-(\d+)\)"')
_SVG_ENTITY_NBSP = "&#160;"
_SVG_ENTITY_APOS = "&#x27;"


def _decode_svg_entities(text: str) -> str:
    return text.replace(_SVG_ENTITY_NBSP, " ").replace(_SVG_ENTITY_APOS, "'")


def _iter_svg_invocations() -> list[tuple[Path, int, str]]:
    """Yield (svg_file, line_no, joined_terminal_line) for each rendered line
    that contains an `agentsuite` invocation.

    rich's `Console.save_svg()` emits one `<text>` node per styled span. We
    group spans by their `terminal-...-line-N` clip-path id so a single
    rendered terminal line is reassembled before we scan for invocations.
    """
    out: list[tuple[Path, int, str]] = []
    for svg in SVG_FILES:
        content = svg.read_text(encoding="utf-8")
        # Collect (line_id, span_text) pairs. Only spans that have an explicit
        # `terminal-...-line-N` clip-path on the same tag are part of the
        # rendered terminal grid; chrome elements (titles, prompt-bar text)
        # are filtered out to keep the extractor stable.
        spans: list[tuple[int, str]] = []
        last_line_id: int | None = None
        for match in re.finditer(r"<text\b[^>]*>([^<]*)</text>", content):
            tag_open = match.group(0)[: match.group(0).index(">") + 1]
            line_match = _SVG_LINE_GROUP_RE.search(tag_open)
            if line_match:
                last_line_id = int(line_match.group(1))
            elif last_line_id is None:
                continue  # chrome span before any line tag — skip
            spans.append((last_line_id, match.group(1)))
        # Reduce to one combined string per line id (sorted ascending).
        per_line: dict[int, str] = {}
        for line_id, span_text in spans:
            per_line.setdefault(line_id, "")
        for line_id, span_text in spans:
            per_line[line_id] = per_line[line_id] + span_text
        ordered_lines = [
            (line_id, _decode_svg_entities(text).rstrip())
            for line_id, text in sorted(per_line.items())
        ]
        # Walk lines in order. When a line contains "agentsuite ", treat it
        # as the start of an invocation; absorb subsequent lines while the
        # current accumulated text ends with a backslash continuation.
        i = 0
        while i < len(ordered_lines):
            line_id, text = ordered_lines[i]
            # Strip a leading shell prompt.
            stripped = text.lstrip()
            if stripped.startswith("$ "):
                stripped = stripped[2:].lstrip()
            if "agentsuite " not in stripped:
                i += 1
                continue
            buf = [stripped.rstrip()]
            j = i + 1
            while buf[-1].endswith("\\") and j < len(ordered_lines):
                buf[-1] = buf[-1].rstrip("\\").rstrip()
                next_text = ordered_lines[j][1].strip()
                buf.append(next_text)
                j += 1
            out.append((svg, line_id + 1, " ".join(buf)))
            i = max(j, i + 1)
    return out


def _iter_doc_invocations() -> list[tuple[Path, int, str]]:
    """Yield (file, line_no, full_invocation_text) tuples.

    Sources:
    1. Fenced ``bash``/``sh``/``console``/``shell`` blocks in DOC_FILES.
       Multi-line continuations (lines ending with ``\\``) are joined.
    2. Inline backtick spans matching ``agentsuite ...`` in DOC_FILES — these
       are how the docs reference real CLI commands in prose.
    3. SVG terminal screenshots in ``docs/screenshots/`` — rendered terminal
       lines containing ``agentsuite`` invocations.
    """
    out: list[tuple[Path, int, str]] = []
    for doc in DOC_FILES:
        if not doc.exists():
            pytest.fail(f"Doc file expected but missing: {doc}")
        in_fence = False
        lines = doc.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if not in_fence:
                # Inline backtick scanning happens on every prose line.
                for inline in _INLINE_BACKTICK_RE.findall(line):
                    out.append((doc, i + 1, inline))
                if _FENCE_OPEN.match(line):
                    in_fence = True
                i += 1
                continue
            if _FENCE_CLOSE.match(line):
                in_fence = False
                i += 1
                continue
            if not _INVOCATION_RE.match(line):
                i += 1
                continue
            start_line = i + 1
            buf: list[str] = []
            current = line
            while current.rstrip().endswith("\\") and i + 1 < len(lines):
                buf.append(current.rstrip().rstrip("\\").rstrip())
                i += 1
                current = lines[i]
                if _FENCE_CLOSE.match(current):
                    in_fence = False
                    break
            buf.append(current.rstrip())
            full = " ".join(buf)
            out.append((doc, start_line, full))
            i += 1
    out.extend(_iter_svg_invocations())
    return out


def _typer_app_param_names(typer_app: typer.Typer, path: list[str]) -> list[str]:
    """Return the long-flag names registered on the subcommand at *path*.

    *path* is e.g. ``["founder", "run"]``. The top-level ``app`` has both
    direct ``@app.command`` registrations (``list-runs``, ``agents``) and
    nested Typer instances (``founder``, ``design``, etc.) attached via
    ``app.add_typer``. We walk down the path resolving each step against
    the appropriate registry.
    """
    current_app = typer_app
    for level, segment in enumerate(path):
        is_last = level == len(path) - 1

        # Look for a nested Typer first (intermediate path segments).
        sub: typer.Typer | None = None
        for ti in current_app.registered_groups:
            if ti.name == segment:
                sub = ti.typer_instance
                break

        if sub is not None and not is_last:
            current_app = sub
            continue

        # Look for a direct command at the current level.
        cmd = None
        host = sub if sub is not None else current_app
        for ci in host.registered_commands:
            cname = ci.name or (ci.callback.__name__ if ci.callback else None)
            if cname == segment or (cname and cname.replace("_", "-") == segment):
                cmd = ci
                break

        if cmd is None and sub is not None and is_last:
            # Path resolves to a Typer group with no command of that name —
            # caller asked for an invalid subcommand.
            raise KeyError(f"no command '{segment}' on subgroup '{path[level - 1]}'")

        if cmd is None:
            raise KeyError(f"no command '{segment}' on app at depth {level}")

        if not is_last:
            raise KeyError(
                f"path step '{segment}' resolved to a leaf command but "
                f"more path segments remain ({path[level + 1:]})"
            )

        # Collect parameter long-form names from the callback signature via
        # Typer's own click introspection.
        import click
        from typer.main import get_command

        click_cmd = get_command(typer_app)
        # Walk the click command to the leaf using path.
        node: click.Command = click_cmd
        for seg in path:
            if isinstance(node, click.Group):
                # Click prefers hyphenated names; try both.
                next_node = node.commands.get(seg) or node.commands.get(seg.replace("_", "-"))
                if next_node is None:
                    raise KeyError(f"click: no command '{seg}'")
                node = next_node
            else:
                raise KeyError(f"click: '{seg}' is not a group")

        names: list[str] = []
        for param in node.params:
            for opt in getattr(param, "opts", []):
                if opt.startswith("--"):
                    names.append(opt[2:])
            for opt in getattr(param, "secondary_opts", []):
                if opt.startswith("--"):
                    names.append(opt[2:])
        return names

    raise KeyError(f"unreachable: empty path {path}")


def _extract_subcommand_path(invocation: str) -> list[str]:
    """Return the subcommand path, e.g. ``['founder', 'run']`` or ``['agents']``.

    Stops before the first token that starts with ``-`` (a flag) or that
    looks like a positional value (everything is a flag-ish token after the
    first flag is seen).
    """
    parts = invocation.strip().split()
    # Find ``agentsuite`` and slice from there.
    try:
        start = parts.index("agentsuite")
    except ValueError:
        return []
    path: list[str] = []
    for tok in parts[start + 1 :]:
        if tok.startswith("-") or tok.startswith("$") or tok.startswith("<"):
            break
        # Stop on shell metacharacters that signal the command is over.
        if tok in {"|", "&&", "||", ";", ">", ">>", "<", "2>&1", "\\"}:
            break
        path.append(tok)
    return path


def _doc_relpath(p: Path) -> str:
    return p.relative_to(REPO_ROOT).as_posix()


@pytest.fixture(scope="module")
def documented_invocations() -> list[tuple[Path, int, str]]:
    return _iter_doc_invocations()


def test_at_least_one_invocation_documented(documented_invocations: list[tuple[Path, int, str]]) -> None:
    """Sanity check: if extraction returns nothing, the regex broke, not docs."""
    assert len(documented_invocations) > 0, (
        "No `agentsuite ...` invocations found in README.md or USER-MANUAL.md. "
        "If docs really have no examples that's the bigger problem; if they do, "
        "the fence/regex extraction in this test is broken."
    )


def test_documented_subcommands_resolve_to_real_commands(
    documented_invocations: list[tuple[Path, int, str]],
) -> None:
    """Every `agentsuite <a> <b>` path must resolve to a registered command."""
    failures: list[str] = []
    for doc, line_no, invocation in documented_invocations:
        path = _extract_subcommand_path(invocation)
        if not path:
            continue
        try:
            _typer_app_param_names(app, path)
        except KeyError as exc:
            failures.append(
                f"  {_doc_relpath(doc)}:{line_no}: "
                f"`agentsuite {' '.join(path)}` -> {exc}"
            )
    if failures:
        pytest.fail(
            "Documented subcommands do not resolve to registered Typer commands:\n"
            + "\n".join(failures)
            + "\n\nFix: update the doc to match the CLI, or register the command."
        )


def test_documented_flags_exist_on_their_subcommand(
    documented_invocations: list[tuple[Path, int, str]],
) -> None:
    """Every `--flag` mentioned in a doc must exist on its subcommand."""
    failures: list[str] = []
    for doc, line_no, invocation in documented_invocations:
        path = _extract_subcommand_path(invocation)
        if not path:
            continue
        try:
            valid_flags = set(_typer_app_param_names(app, path))
        except KeyError:
            # Subcommand resolution failure is reported by the other test;
            # don't double-report here.
            continue
        # Always-available global flags (registered on the app callback).
        valid_flags.update({"debug", "help", "install-completion", "show-completion"})
        used_flags = set(_LONG_FLAG_RE.findall(invocation))
        bad = sorted(f for f in used_flags if f not in valid_flags)
        if bad:
            failures.append(
                f"  {_doc_relpath(doc)}:{line_no}: "
                f"`agentsuite {' '.join(path)}` uses unknown flag(s): "
                f"{', '.join('--' + f for f in bad)}\n"
                f"    valid flags: {sorted(valid_flags)}"
            )
    if failures:
        pytest.fail(
            "Documented `--flag`s do not exist on their subcommand:\n"
            + "\n".join(failures)
            + "\n\nFix: update the doc to use real flag names, or add the flag to the CLI."
        )
