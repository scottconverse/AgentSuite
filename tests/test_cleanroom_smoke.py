"""Marker-gated cleanroom smoke test. Invoked via `pytest -m cleanroom`."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.cleanroom


REPO_ROOT = Path(__file__).parent.parent


@pytest.mark.skipif(
    shutil.which("bash") is None,
    reason="bash not available; cleanroom requires bash (Git for Windows or WSL)",
)
def test_cleanroom_script_exits_zero():
    """Run scripts/run-cleanroom.sh in mocked mode and assert exit code 0."""
    # Pass full environment so python is available in bash subprocess
    env = os.environ.copy()
    result = subprocess.run(
        "bash scripts/run-cleanroom.sh",
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        shell=True,
        env=env,
    )
    assert result.returncode == 0, (
        f"cleanroom failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "CLEANROOM PASS" in result.stdout
