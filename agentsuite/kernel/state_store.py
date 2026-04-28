"""Persisted state for in-flight agent runs."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from agentsuite.kernel.schema import RunState


class StateStore:
    """JSON-backed store for the RunState of a single in-flight run."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / "_state.json"

    def save(self, state: RunState) -> None:
        """Atomically write the state to ``_state.json``, refreshing ``updated_at``.

        Writes to a temp file in the same directory, fsyncs, then uses
        ``os.replace()`` (atomic on POSIX; best-effort on Windows) to swap
        it into place. A partial write never corrupts the existing state file.
        """
        state.updated_at = datetime.now(tz=timezone.utc)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        data = state.model_dump_json(indent=2)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=self.run_dir, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, self.path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def load(self) -> RunState | None:
        """Return the persisted RunState, or ``None`` if no state file exists."""
        if not self.path.exists():
            return None
        return RunState.model_validate_json(self.path.read_text(encoding="utf-8"))
