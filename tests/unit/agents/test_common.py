"""Unit tests for agentsuite.agents._common path-construction helpers."""
from __future__ import annotations

import pytest

from agentsuite.agents._common import require_kernel_dir, require_run_dir
from agentsuite.kernel.identifiers import InvalidIdentifier


# ---------------------------------------------------------------------------
# require_run_dir
# ---------------------------------------------------------------------------

def test_require_run_dir_validates_and_returns_path(tmp_path):
    """A valid run_id resolves to ``output_root / "runs" / run_id``."""
    result = require_run_dir(lambda: tmp_path, "run-20260430-123456-789012")
    assert result == tmp_path / "runs" / "run-20260430-123456-789012"


@pytest.mark.parametrize(
    "payload",
    [
        "../../etc",
        "/etc",
        "",
        "foo/../bar",
        "..",
        "./run-1",
    ],
)
def test_require_run_dir_rejects_traversal(tmp_path, payload):
    """Path-traversal payloads must raise InvalidIdentifier before any I/O."""
    with pytest.raises(InvalidIdentifier):
        require_run_dir(lambda: tmp_path, payload)


# ---------------------------------------------------------------------------
# require_kernel_dir
# ---------------------------------------------------------------------------

def test_require_kernel_dir_validates_and_returns_path(tmp_path):
    """A valid project_slug resolves to ``output_root / "_kernel" / slug``."""
    result = require_kernel_dir(lambda: tmp_path, "my-project")
    assert result == tmp_path / "_kernel" / "my-project"


@pytest.mark.parametrize(
    "payload",
    [
        "../../etc",
        "/etc",
        "",
        "foo/../bar",
        "..",
        "./slug",
    ],
)
def test_require_kernel_dir_rejects_traversal(tmp_path, payload):
    """Path-traversal payloads must raise InvalidIdentifier before any I/O."""
    with pytest.raises(InvalidIdentifier):
        require_kernel_dir(lambda: tmp_path, payload)


# ---------------------------------------------------------------------------
# Boundary lengths — 1 and 64 chars
# ---------------------------------------------------------------------------

def test_require_run_dir_accepts_boundary_lengths(tmp_path):
    """Single-char and 64-char run_ids must both validate."""
    one = require_run_dir(lambda: tmp_path, "a")
    assert one == tmp_path / "runs" / "a"

    long_id = "a" * 64
    sixty_four = require_run_dir(lambda: tmp_path, long_id)
    assert sixty_four == tmp_path / "runs" / long_id

    # 65 chars must be rejected
    with pytest.raises(InvalidIdentifier):
        require_run_dir(lambda: tmp_path, "a" * 65)
