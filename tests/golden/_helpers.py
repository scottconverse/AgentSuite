# Golden tests verify mock-LLM output stability and detect prompt/template drift.
# They do NOT validate real-LLM output quality — that is the live tier's job.
# Artifact snapshots are captured from MockLLMProvider output (scaffold strings).

"""Helpers for golden tests.

Two assertion shapes, deliberately separated by argument types:

* :func:`assert_artifact_exact` — for text artifacts and JSON-with-fixed-keys.
  Signature accepts ``str | bytes``. Tolerance is **never** applied to text;
  any prompt change that produces materially different output must be either
  rolled back or re-snapshotted via the ``update-goldens`` make target.

* :func:`assert_qa_within_tolerance` — for numeric QA score dicts. Signature
  accepts ``dict[str, float]``-shaped data and a ``rtol`` parameter; refuses
  non-numeric input so a future contributor cannot accidentally mask text
  drift by sprinkling tolerance over the wrong call site.

The split exists because deterministic mock LLM output is byte-stable, but
``qa_scores.json`` averages can wobble fractionally between Python minor
versions when float ordering changes. Numeric tolerance for numbers, exact
match for everything else.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


def assert_artifact_exact(
    actual_path: Path,
    fixture_path: Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """Assert ``actual_path`` content equals the fixture byte-for-byte.

    Both paths must exist. Use this for markdown artifacts, scaffold prompts,
    and any JSON where every value is part of the contract. The error
    message includes a short diff snippet so failures are diagnosable
    without re-running.

    To regenerate the fixture intentionally, run ``make update-goldens``
    (documented in CONTRIBUTING.md).
    """
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Golden fixture missing: {fixture_path}. Run `make update-goldens` "
            f"to regenerate fixtures from the current mock output."
        )
    if not actual_path.exists():
        raise AssertionError(
            f"Generated artifact missing: {actual_path}. The agent did not "
            f"produce this file under the mock — fix the agent or remove the "
            f"fixture."
        )
    actual = actual_path.read_text(encoding=encoding)
    expected = fixture_path.read_text(encoding=encoding)
    if actual == expected:
        return
    # Build a short diff for the assertion message.
    import difflib
    diff_lines = list(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=str(fixture_path),
            tofile=str(actual_path),
            n=3,
        )
    )
    diff_blob = "".join(diff_lines[:60])  # cap so failure messages stay readable
    raise AssertionError(
        f"Artifact differs from golden fixture.\n"
        f"  fixture: {fixture_path}\n"
        f"  actual:  {actual_path}\n\n"
        f"{diff_blob}\n"
        f"To regenerate intentionally: `make update-goldens`."
    )


def assert_qa_within_tolerance(
    actual: dict[str, Any],
    fixture: dict[str, Any],
    *,
    rtol: float = 0.05,
    atol: float = 0.0,
) -> None:
    """Assert numeric QA score fields match the fixture within tolerance.

    Compares the per-dimension ``scores`` dict and the ``average`` field
    using ``pytest.approx(rel=rtol, abs=atol)``. Non-numeric fields
    (``passed``, ``requires_revision``) are compared exactly. Any field
    in the fixture that is not numeric and not on the exact-compare list
    raises a :class:`TypeError` to keep tolerance from leaking into text.

    Use this only for ``qa_scores.json``-shaped payloads. For other JSON
    artifacts use :func:`assert_artifact_exact` against the serialized form.
    """
    _exact_keys = {"passed", "requires_revision", "revision_instructions"}
    _numeric_top_keys = {"average"}
    for key, fixture_value in fixture.items():
        actual_value = actual.get(key)
        if key == "scores":
            if not isinstance(fixture_value, dict):
                raise TypeError(
                    f"Fixture key 'scores' must be a dict of "
                    f"dimension->float, got {type(fixture_value).__name__}"
                )
            if not isinstance(actual_value, dict):
                raise AssertionError(
                    f"Actual 'scores' is not a dict (got {type(actual_value).__name__})"
                )
            assert set(actual_value.keys()) == set(fixture_value.keys()), (
                f"qa_scores.scores dimension drift: "
                f"actual={sorted(actual_value)}, fixture={sorted(fixture_value)}"
            )
            for dim, expected_score in fixture_value.items():
                if not isinstance(expected_score, (int, float)):
                    raise TypeError(
                        f"qa_scores.scores['{dim}'] must be numeric in fixture; "
                        f"got {type(expected_score).__name__}"
                    )
                actual_score = actual_value[dim]
                assert actual_score == pytest.approx(
                    expected_score, rel=rtol, abs=atol
                ), (
                    f"qa_scores.scores['{dim}'] drift: "
                    f"{actual_score} vs {expected_score} (rtol={rtol})"
                )
        elif key in _numeric_top_keys:
            if not isinstance(fixture_value, (int, float)):
                raise TypeError(
                    f"Fixture key '{key}' must be numeric; got "
                    f"{type(fixture_value).__name__}"
                )
            assert actual_value == pytest.approx(
                fixture_value, rel=rtol, abs=atol
            ), f"qa_scores.{key} drift: {actual_value} vs {fixture_value}"
        elif key in _exact_keys:
            assert actual_value == fixture_value, (
                f"qa_scores.{key} differs: actual={actual_value!r}, "
                f"fixture={fixture_value!r}"
            )
        else:
            # Unknown keys in the fixture are a contract violation — they
            # would either be exact-checked silently (wrong) or tolerance-
            # checked silently (wrong). Force the contributor to update
            # this helper if the qa_scores schema gains a field.
            raise TypeError(
                f"Unknown qa_scores fixture key {key!r}; update "
                f"assert_qa_within_tolerance to classify it as exact or numeric."
            )


def load_qa_scores(run_dir: Path) -> dict[str, Any]:
    """Convenience loader: parse ``qa_scores.json`` from a run dir."""
    return json.loads(
        (run_dir / "qa_scores.json").read_text(encoding="utf-8")
    )
