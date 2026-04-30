"""Shared path-construction helpers for MCP tool modules.

All helpers validate their identifier arguments before constructing any
filesystem path, so a path-traversal payload (``../../etc``, ``/etc``,
null bytes) fails fast with ``InvalidIdentifier`` rather than silently
escaping the output root.

These functions exist because several MCP tool functions construct
``output_root / "runs" / run_id`` and ``output_root / "_kernel" / project_slug``
locally without going through ``ArtifactWriter``. Every such callsite should
use these helpers instead of bare ``Path`` division.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from agentsuite.kernel.identifiers import validate_project_slug, validate_run_id


def require_run_dir(output_root_fn: Callable[[], Path], run_id: str) -> Path:
    """Validate *run_id* and return ``output_root / "runs" / run_id``.

    Raises :class:`~agentsuite.kernel.identifiers.InvalidIdentifier` if
    *run_id* contains path-traversal characters or does not match the
    allowed identifier shape.
    """
    validate_run_id(run_id)
    return output_root_fn() / "runs" / run_id


def require_kernel_dir(output_root_fn: Callable[[], Path], project_slug: str) -> Path:
    """Validate *project_slug* and return ``output_root / "_kernel" / project_slug``.

    Raises :class:`~agentsuite.kernel.identifiers.InvalidIdentifier` if
    *project_slug* contains path-traversal characters or does not match the
    allowed identifier shape.
    """
    validate_project_slug(project_slug)
    return output_root_fn() / "_kernel" / project_slug
