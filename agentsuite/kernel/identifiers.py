"""Identifier validators for ``run_id`` and ``project_slug``.

These are user-controllable strings that flow into filesystem paths via
``ArtifactWriter.run_dir`` and ``ArtifactWriter.promote()``. Without
validation, a caller can construct a path that escapes the configured
output root by passing values like ``../../etc`` or absolute paths.

ENG-001 in the v1.0.0 audit flagged this as a Critical finding: the MCP
server takes both fields from a remote request and threads them straight
through to ``Path.mkdir``, ``Path.rglob``, and ``shutil.rmtree``. With
this module wired in at every path-construction boundary, malformed input
fails fast with a clear ``InvalidIdentifier`` error before any I/O.

Allowed shape:
- 1-64 characters
- ASCII alphanumeric, underscore, hyphen, dot
- First and last characters must be alphanumeric or underscore (forbids
  leading/trailing dot or hyphen, prevents ``..`` from validating)
- Empty string rejected
- ``.`` alone rejected (would point at the parent directory under
  ``output_root / "runs" / "."``)

Rationale for permitting dots in the middle: project slugs commonly look
like ``pfl.v2`` or ``acme.app``; rejecting all dots would force a churny
rename in real codebases.
"""
from __future__ import annotations

import re


class InvalidIdentifier(ValueError):
    """Raised when a ``run_id`` or ``project_slug`` does not match the allowed shape."""


# Single-char names allowed (e.g. "a"); otherwise first/last char must be
# alphanumeric or underscore. ``..`` is rejected because the leading char
# would have to be `.` which is not in the start-character class.
_ID_RE = re.compile(r"^[a-zA-Z0-9_]([a-zA-Z0-9._-]{0,62}[a-zA-Z0-9_])?$")


def validate_identifier(value: str, *, kind: str) -> str:
    """Return ``value`` unchanged if it matches the allowed shape.

    Raises :class:`InvalidIdentifier` with a message naming the offending
    field and the rule violated. The error is intentionally catalog-style
    (no clever phrasing) so the message can be surfaced verbatim by a
    server, CLI, or test runner.
    """
    if not isinstance(value, str):
        raise InvalidIdentifier(
            f"{kind} must be a string, got {type(value).__name__}"
        )
    if not value:
        raise InvalidIdentifier(f"{kind} cannot be empty")
    if len(value) > 64:
        raise InvalidIdentifier(
            f"{kind} too long ({len(value)} chars; limit 64): {value!r}"
        )
    if not _ID_RE.match(value):
        raise InvalidIdentifier(
            f"{kind} {value!r} does not match required shape "
            r"^[a-zA-Z0-9_]([a-zA-Z0-9._-]*[a-zA-Z0-9_])?$. "
            "Allowed: ASCII alphanumeric, underscore, hyphen, dot in the "
            "middle. First and last characters must be alphanumeric or "
            "underscore. This rule blocks path-traversal payloads "
            "(``..``, ``./``, absolute paths, encoded slashes)."
        )
    return value


def validate_run_id(value: str) -> str:
    """Validate a ``run_id`` (used to construct ``output_root/runs/<run_id>/``)."""
    return validate_identifier(value, kind="run_id")


def validate_project_slug(value: str) -> str:
    """Validate a ``project_slug`` (used to construct ``output_root/_kernel/<slug>/``)."""
    return validate_identifier(value, kind="project_slug")
