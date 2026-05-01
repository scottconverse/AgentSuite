"""Unit tests for kernel.stages.spec — path confinement (ENG-004)."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentsuite.kernel.stages.spec import check_path_confinement


def test_path_inside_project_dir_passes(tmp_path: Path):
    """ENG-004: a path inside the project directory is accepted without error."""
    source = tmp_path / "docs" / "readme.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.touch()
    # Should not raise.
    check_path_confinement(source, tmp_path)


def test_path_equal_to_project_dir_file_passes(tmp_path: Path):
    """ENG-004: a file directly at the project root is accepted."""
    source = tmp_path / "notes.txt"
    source.touch()
    check_path_confinement(source, tmp_path)


def test_path_outside_project_dir_raises(tmp_path: Path):
    """ENG-004: a path outside the project directory raises ValueError."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    outside = tmp_path / "secret.txt"
    outside.touch()

    with pytest.raises(ValueError) as exc:
        check_path_confinement(outside, project_dir)

    msg = str(exc.value)
    assert "outside the project directory" in msg
    assert str(project_dir) in msg


def test_path_traversal_via_dotdot_raises(tmp_path: Path):
    """ENG-004: a path using '..' to escape the project directory raises ValueError."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    # Construct a traversal path: project/../secret.txt → tmp_path/secret.txt
    traversal = project_dir / ".." / "secret.txt"

    with pytest.raises(ValueError) as exc:
        check_path_confinement(traversal, project_dir)

    msg = str(exc.value)
    assert "outside the project directory" in msg
    assert str(project_dir) in msg


def test_error_message_names_the_bad_path(tmp_path: Path):
    """ENG-004: the ValueError message includes the offending path so operators can act."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    outside = tmp_path / "etc" / "passwd"

    with pytest.raises(ValueError) as exc:
        check_path_confinement(outside, project_dir)

    msg = str(exc.value)
    # The bad path and the allowed root must both appear in the message.
    assert "etc" in msg or "passwd" in msg
    assert str(project_dir) in msg
