"""Verify the README install block matches the canonical fixture.

This is the dev-side mirror of the release-workflow drift check: a copy
edit to the install commands in README.md must be mirrored to
``tests/fixtures/install-block.md`` (or vice versa) so the public
storefront and the install-verification fixture never silently diverge.

Exits 0 on match; exits 1 with a unified diff on drift. Run via
``python scripts/check_install_block_drift.py`` or via the release
workflow (which runs this on every tag push).
"""
from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "install-block.md"

# Match (and capture) everything between ``<!-- install:start -->`` and
# ``<!-- install:end -->`` inclusive. Multi-line, non-greedy.
_BLOCK_RE = re.compile(
    r"<!-- install:start -->.*?<!-- install:end -->",
    re.DOTALL,
)


def extract_install_block(markdown: str) -> str:
    """Return the install block from ``markdown`` including the markers.

    Raises :class:`ValueError` if the markers are missing or unbalanced.
    """
    match = _BLOCK_RE.search(markdown)
    if match is None:
        raise ValueError(
            "install block markers not found — README.md must contain "
            "<!-- install:start --> and <!-- install:end --> on their own lines"
        )
    return match.group(0).strip()


def main() -> int:
    """Compare README install block to fixture; print diff and exit 1 on drift."""
    readme_text = README.read_text(encoding="utf-8")
    fixture_text = FIXTURE.read_text(encoding="utf-8").strip()
    extracted = extract_install_block(readme_text)
    if extracted == fixture_text:
        print("install block matches fixture — no drift.")
        return 0
    diff = difflib.unified_diff(
        fixture_text.splitlines(keepends=True),
        extracted.splitlines(keepends=True),
        fromfile="tests/fixtures/install-block.md",
        tofile="README.md (extracted)",
    )
    sys.stdout.writelines(diff)
    print(
        "\n!! install block drift detected. Update either the README or the "
        "fixture so both match, then re-run.",
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
