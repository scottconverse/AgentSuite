"""Persisted state for in-flight agent runs."""
from __future__ import annotations

import importlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from agentsuite.kernel.schema import AgentRequest, RunState

# Bumped whenever the on-disk shape of _state.json changes in a way that
# requires re-running rather than a silent migration. v0.9.0 introduces
# subclass-aware ``inputs`` serialization so subclass-specific fields
# (DesignAgentInput.campaign_goal etc.) survive save/load round-trip.
SCHEMA_VERSION = 2

# Lazy registry mapping ``state.agent`` to the dotted ``module:Class`` path
# of the agent's input subclass. Loaded via importlib at load time so the
# kernel never has to import the agent packages at import time (avoiding
# the circular-import that motivated v0.9.0's design choice).
_INPUTS_BY_AGENT: dict[str, str] = {
    "founder":    "agentsuite.agents.founder.input_schema:FounderAgentInput",
    "design":     "agentsuite.agents.design.input_schema:DesignAgentInput",
    "product":    "agentsuite.agents.product.input_schema:ProductAgentInput",
    "engineering":"agentsuite.agents.engineering.input_schema:EngineeringAgentInput",
    "marketing":  "agentsuite.agents.marketing.input_schema:MarketingAgentInput",
    "trust_risk": "agentsuite.agents.trust_risk.input_schema:TrustRiskAgentInput",
    "cio":        "agentsuite.agents.cio.input_schema:CIOAgentInput",
}


def _resolve_inputs_cls(agent: str) -> type[AgentRequest]:
    """Resolve an agent name to its input subclass via lazy import.

    Falls back to :class:`AgentRequest` for unknown agents (e.g. test
    fixtures registering a custom agent name). Pydantic ``extra="allow"``
    on the base class still preserves subclass fields as extras in that
    case, so the fallback is a strict superset of the legacy behavior.
    """
    spec = _INPUTS_BY_AGENT.get(agent)
    if spec is None:
        return AgentRequest
    mod_path, cls_name = spec.rsplit(":", 1)
    mod = importlib.import_module(mod_path)
    cls: type = getattr(mod, cls_name)
    if not issubclass(cls, AgentRequest):  # defensive — registry typo
        raise TypeError(f"{spec} is not an AgentRequest subclass")
    return cls


class RunStateSchemaVersionError(RuntimeError):
    """Raised when an _state.json file's ``schema_version`` is missing or older
    than :data:`SCHEMA_VERSION`.

    No automatic migration is shipped: pre-v0.9 state files used the legacy
    base-typed serialization that silently dropped subclass fields, and
    AgentSuite has no known persisted-run consumers outside the local
    workspace. The error message tells the operator to delete the
    offending run directory and re-run; the alternative — a fragile
    one-shot migrator that would have to be maintained forever — earns
    its complexity only when there's a real installed base to protect.
    """


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

        ``inputs`` is dumped using the runtime instance's schema (i.e. the
        agent's input subclass), not the declared ``RunState.inputs:
        AgentRequest`` field type, so subclass-specific fields like
        ``DesignAgentInput.campaign_goal`` survive the round-trip. The
        on-disk envelope adds a ``schema_version`` field tracked by
        :data:`SCHEMA_VERSION`; bump it when the persisted shape changes
        in a way that requires re-running rather than silent migration.
        """
        state.updated_at = datetime.now(tz=timezone.utc)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        envelope = state.model_dump(mode="json", exclude={"inputs"})
        envelope["inputs"] = state.inputs.model_dump(mode="json")
        envelope["schema_version"] = SCHEMA_VERSION
        data = json.dumps(envelope, indent=2)
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
        """Return the persisted RunState, or ``None`` if no state file exists.

        Validates ``inputs`` against the agent's input subclass (resolved
        via :func:`_resolve_inputs_cls`) so subclass-specific fields
        survive on the loaded instance. Raises
        :class:`RunStateSchemaVersionError` when the on-disk
        ``schema_version`` is missing or older than :data:`SCHEMA_VERSION`.
        """
        if not self.path.exists():
            return None
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        on_disk_version = raw.get("schema_version")
        if on_disk_version is None or on_disk_version < SCHEMA_VERSION:
            raise RunStateSchemaVersionError(
                f"_state.json at {self.path} has schema_version="
                f"{on_disk_version!r}; expected {SCHEMA_VERSION}. Pre-v0.9 "
                f"state files are not supported. Delete "
                f"{self.run_dir} and re-run."
            )
        raw.pop("schema_version", None)
        agent_name = raw.get("agent", "")
        inputs_cls = _resolve_inputs_cls(agent_name)
        raw_inputs = raw.get("inputs", {})
        try:
            typed_inputs: AgentRequest = inputs_cls.model_validate(raw_inputs)
        except ValidationError:
            # Fallback for state files written from bare AgentRequest (legacy
            # tests, custom agent fixtures, or hand-crafted state). Subclass
            # required-field violations don't break load — extra="allow" on
            # the base preserves all stored fields as extras.
            typed_inputs = AgentRequest.model_validate(raw_inputs)
        # Validate the envelope against RunState (its declared
        # ``inputs: AgentRequest`` field accepts the subclass instance).
        # Substitute the typed instance after validation so callers see
        # the true subclass type, not the base.
        raw["inputs"] = typed_inputs.model_dump(mode="json")
        state = RunState.model_validate(raw)
        state.inputs = typed_inputs
        return state
