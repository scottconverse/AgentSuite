"""Unit tests for scripts.check_install_block_drift.

Imports the script as a module so its extractor can be tested without
shelling out. The module-level constants (``REPO_ROOT``, ``README``,
``FIXTURE``) point at the real repo on disk; tests that exercise full
``main()`` rely on the actual on-disk files matching, which is the
property the script exists to enforce.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "check_install_block_drift.py"
)


def _load_module():
    """Load the script as a module without registering it in sys.modules globally."""
    spec = importlib.util.spec_from_file_location("_drift_check", _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_extract_install_block_returns_marked_section():
    mod = _load_module()
    sample = (
        "# Title\n\n"
        "## Install\n\n"
        "<!-- install:start -->\n"
        "```bash\npip install x\n```\n"
        "<!-- install:end -->\n\n"
        "## More\n"
    )
    extracted = mod.extract_install_block(sample)
    assert extracted.startswith("<!-- install:start -->")
    assert extracted.endswith("<!-- install:end -->")
    assert "pip install x" in extracted


def test_extract_install_block_raises_when_markers_missing():
    mod = _load_module()
    with pytest.raises(ValueError, match="install block markers not found"):
        mod.extract_install_block("no markers here\n```bash\npip install x\n```")


def test_main_returns_zero_when_readme_matches_fixture():
    """Smoke: the script exits 0 against the actual on-disk repo state."""
    mod = _load_module()
    # Reload guard: the module reads files at call time, so any drift
    # between README and fixture during this run would be a real failure.
    rc = mod.main()
    assert rc == 0


def test_main_returns_one_when_readme_diverges_from_fixture(tmp_path, monkeypatch):
    """Pointing the script at a divergent README + fixture surfaces drift."""
    mod = _load_module()
    fake_readme = tmp_path / "README.md"
    fake_fixture = tmp_path / "fixture.md"
    fake_readme.write_text(
        "<!-- install:start -->\npip install A\n<!-- install:end -->\n",
        encoding="utf-8",
    )
    fake_fixture.write_text(
        "<!-- install:start -->\npip install B\n<!-- install:end -->\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "README", fake_readme)
    monkeypatch.setattr(mod, "FIXTURE", fake_fixture)
    assert mod.main() == 1


# Cleanup: the loader didn't register in sys.modules but be defensive.
def teardown_module(_module: object) -> None:
    sys.modules.pop("_drift_check", None)
