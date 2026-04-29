"""Regression: ``agentsuite --help`` must not crash on a Windows cp1252 console.

v1.0.0 GA shipped a Typer help string containing U+2014 (em-dash) and U+2192
(right arrow). On default Windows installs, ``sys.stdout.encoding`` is cp1252,
which cannot encode either glyph; ``agentsuite --help`` raised
``UnicodeEncodeError`` on the first command (QA-001).

The fix is two-layered: (1) help text uses ASCII fallbacks; (2) ``cli.py``
calls ``sys.stdout.reconfigure(encoding="utf-8")`` early, so even if a future
help string regresses, the cp1252 console is reconfigured before Typer
formats output.

This test asserts both layers by spawning a subprocess with
``PYTHONIOENCODING=cp1252`` (forcing the failing condition), invoking
``agentsuite --help``, and requiring exit 0 with non-empty output.
"""
from __future__ import annotations

import os
import subprocess
import sys


def test_help_does_not_crash_under_cp1252() -> None:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"
    result = subprocess.run(
        [sys.executable, "-m", "agentsuite.cli", "--help"],
        capture_output=True,
        env=env,
        timeout=30,
    )
    # Exit 0 is the load-bearing assertion: pre-fix, this raised
    # UnicodeEncodeError and the process exited non-zero.
    assert result.returncode == 0, (
        "agentsuite --help crashed under cp1252. "
        "stdout(cp1252): "
        + repr(result.stdout.decode("cp1252", errors="replace"))
        + " stderr(cp1252): "
        + repr(result.stderr.decode("cp1252", errors="replace"))
    )
    # Output must contain the usage prefix; any non-empty output proves the
    # help string was formatted and emitted without a UnicodeEncodeError.
    assert len(result.stdout) > 0, (
        "agentsuite --help exited 0 but produced no stdout. "
        "The help text was likely silently dropped."
    )


def test_help_text_is_ascii_safe() -> None:
    """Belt-and-suspenders: the literal Typer help string must be ASCII.

    Even with the runtime stdout reconfigure, defense in depth: the help
    string itself should stay ASCII so a malformed environment cannot
    re-introduce QA-001.
    """
    from agentsuite.cli import app

    help_text = app.info.help or ""
    non_ascii = [c for c in help_text if ord(c) > 127]
    assert not non_ascii, (
        "agentsuite Typer help text contains non-ASCII characters: "
        + repr(non_ascii)
        + " in "
        + repr(help_text)
        + ". Use ASCII fallbacks (e.g. -- for em-dash, -> for arrow)."
    )
