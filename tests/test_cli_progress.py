"""Tests for UX-006 / QA-005 fix: per-stage progress on stderr.

Pre-v1.0.1 the CLI was silent for the entire LLM-bound duration of a run.
On a real Anthropic call (~10-30s per stage) users saw zero output and
assumed the process had hung. Fix: ``base_agent._emit_stage_progress``
writes one line per completed stage to stderr; format ``[OK] <stage>
complete  (Xs, $Y.YYYY)``. JSON stdout is unaffected.

Gate: ``AGENTSUITE_QUIET=1`` silences the emitter (CLI ``--quiet`` flag
sets this).
"""
from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

import pytest

from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.founder.input_schema import FounderAgentInput
from agentsuite.kernel.base_agent import _emit_stage_progress
from agentsuite.kernel.schema import Constraints
from agentsuite.llm.mock import _default_mock_for_cli


REPO_ROOT = Path(__file__).resolve().parents[1]
PFL_FIXTURE = REPO_ROOT / "examples" / "patentforgelocal"


def _capture_stderr_during_founder_run() -> str:
    err = io.StringIO()
    sys.stderr = err
    try:
        with tempfile.TemporaryDirectory() as td:
            agent = FounderAgent(output_root=Path(td), llm=_default_mock_for_cli())
            request = FounderAgentInput(
                agent_name="founder",
                role_domain="creative-ops",
                user_request="probe",
                business_goal="Probe",
                project_slug="probe",
                inputs_dir=PFL_FIXTURE,
                founder_voice_samples=[PFL_FIXTURE / "voice-sample.txt"],
                constraints=Constraints(),
            )
            agent.run(request=request, run_id="probe-r1")
    finally:
        sys.stderr = sys.__stderr__
    return err.getvalue()


def test_progress_lines_emitted_for_every_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTSUITE_QUIET", raising=False)
    out = _capture_stderr_during_founder_run()
    for stage in ("intake", "extract", "spec", "execute", "qa"):
        assert stage + " complete" in out, (
            "Stage " + stage + " missing from stderr progress output: " + repr(out)
        )


def test_progress_lines_use_ascii_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """ASCII-only output keeps Windows cp1252 consoles (QA-001) safe even if
    stdout/stderr reconfigure regresses."""
    monkeypatch.delenv("AGENTSUITE_QUIET", raising=False)
    out = _capture_stderr_during_founder_run()
    non_ascii = [c for c in out if ord(c) > 127]
    assert not non_ascii, (
        "Progress emitter produced non-ASCII characters: " + repr(non_ascii)
    )


def test_quiet_env_silences_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSUITE_QUIET", "1")
    out = _capture_stderr_during_founder_run()
    # Allow other stderr noise, but no progress lines.
    assert "complete" not in out, (
        "AGENTSUITE_QUIET=1 should suppress stage-progress lines, got: " + repr(out)
    )


def test_emitter_is_resilient_to_stderr_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """A broken stderr (closed pipe) must not crash the agent."""
    class Boom:
        def write(self, _: str) -> int:
            raise RuntimeError("pipe closed")
        def flush(self) -> None:
            raise RuntimeError("pipe closed")
    monkeypatch.setattr(sys, "stderr", Boom())
    monkeypatch.delenv("AGENTSUITE_QUIET", raising=False)
    # Should not raise.
    _emit_stage_progress("intake", 1.0, 0.0123)


def test_quiet_truthy_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    """``true`` and ``yes`` (case-insensitive) also silence the emitter."""
    err = io.StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    for value in ("1", "true", "TRUE", "yes", "Yes"):
        err.truncate(0)
        err.seek(0)
        monkeypatch.setenv("AGENTSUITE_QUIET", value)
        _emit_stage_progress("intake", 1.0, 0.0)
        assert err.getvalue() == "", value + " did not silence emitter"
