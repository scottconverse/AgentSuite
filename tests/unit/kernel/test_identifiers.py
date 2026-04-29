"""Tests for ``agentsuite.kernel.identifiers`` (ENG-001 path-traversal gate)."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.identifiers import (
    InvalidIdentifier,
    validate_identifier,
    validate_project_slug,
    validate_run_id,
)


# Things the gate must accept (legitimate, common cases)
VALID_IDENTIFIERS = [
    "a",
    "ab",
    "abc",
    "founder",
    "patentforgelocal",
    "pfl",
    "pfl-v2",
    "pfl_v2",
    "pfl.v2",
    "Acme",
    "Acme123",
    "team_42",
    "x_y",
    "a-b-c",
    "a.b.c",
    "X" * 64,
    "run-2026-04-29-a4f2",
    "golden_d1",
]


# Path-traversal payloads + malformed input. Constructed via chr() for the
# control-character cases so the test source itself contains no null bytes
# or unusual whitespace that would trip pytest's ast parser.
INVALID_IDENTIFIERS = [
    "",
    ".",
    "..",
    "...",
    "../etc",
    "../../passwd",
    "/abs",
    "a/b",
    "a/../b",
    "%2e%2e",
    ".hidden",
    "trailing.",
    "trailing-",
    "-leading",
    "X" * 65,
    " spaces",
    "spaces ",
    "tab" + chr(9) + "here",
    "newline" + chr(10) + "here",
    "weird" + chr(0) + "null",
    "unicode" + chr(0xe9),
    "back" + chr(92) + "slash",
]


@pytest.mark.parametrize("value", VALID_IDENTIFIERS)
def test_validate_accepts_valid(value: str) -> None:
    assert validate_identifier(value, kind="run_id") == value
    assert validate_run_id(value) == value
    assert validate_project_slug(value) == value


@pytest.mark.parametrize("value", INVALID_IDENTIFIERS)
def test_validate_rejects_invalid(value: str) -> None:
    with pytest.raises(InvalidIdentifier):
        validate_identifier(value, kind="run_id")


def test_validate_rejects_non_string() -> None:
    with pytest.raises(InvalidIdentifier, match="must be a string"):
        validate_identifier(None, kind="run_id")  # type: ignore[arg-type]
    with pytest.raises(InvalidIdentifier, match="must be a string"):
        validate_identifier(42, kind="run_id")  # type: ignore[arg-type]


def test_artifact_writer_rejects_traversal_run_id(tmp_path: Path) -> None:
    with pytest.raises(InvalidIdentifier):
        ArtifactWriter(output_root=tmp_path, run_id="../escape")


def test_artifact_writer_rejects_absolute_run_id(tmp_path: Path) -> None:
    with pytest.raises(InvalidIdentifier):
        ArtifactWriter(output_root=tmp_path, run_id="/etc/passwd")


def test_artifact_writer_accepts_clean_run_id(tmp_path: Path) -> None:
    writer = ArtifactWriter(output_root=tmp_path, run_id="my-run-1")
    assert writer.run_id == "my-run-1"
    assert writer.run_dir.is_relative_to(tmp_path.resolve())


def test_artifact_writer_promote_rejects_traversal_slug(tmp_path: Path) -> None:
    writer = ArtifactWriter(output_root=tmp_path, run_id="run-1")
    with pytest.raises(InvalidIdentifier):
        writer.promote(project_slug="../escape")


def test_artifact_writer_promote_rejects_absolute_slug(tmp_path: Path) -> None:
    writer = ArtifactWriter(output_root=tmp_path, run_id="run-1")
    with pytest.raises(InvalidIdentifier):
        writer.promote(project_slug="/abs/path")


def test_error_message_names_offending_field() -> None:
    try:
        validate_run_id("../bad")
    except InvalidIdentifier as exc:
        msg = str(exc)
        assert "run_id" in msg
        assert "../bad" in msg
        assert "shape" in msg or "Allowed" in msg
    else:
        pytest.fail("Expected InvalidIdentifier")


def test_validator_messages_are_distinct_per_kind() -> None:
    with pytest.raises(InvalidIdentifier, match="run_id"):
        validate_run_id("..")
    with pytest.raises(InvalidIdentifier, match="project_slug"):
        validate_project_slug("..")
