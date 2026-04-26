"""Persisted state for in-flight agent runs."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agentsuite.kernel.schema import RunState


class StateStore:
    """JSON-backed store for the RunState of a single in-flight run."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / "_state.json"

    def save(self, state: RunState) -> None:
        """Write the state to ``_state.json``, refreshing ``updated_at``."""
        state.updated_at = datetime.now(tz=timezone.utc)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def load(self) -> RunState | None:
        """Return the persisted RunState, or ``None`` if no state file exists."""
        if not self.path.exists():
            return None
        return RunState.model_validate_json(self.path.read_text(encoding="utf-8"))
