"""Token + dollar accounting with cap enforcement and per-stage telemetry."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, get_args

from pydantic import BaseModel, ConfigDict

from agentsuite.kernel.schema import Cost, Stage


class HardCapExceeded(RuntimeError):
    """Raised when accumulated cost would exceed the hard kill cap."""


class CostCap(BaseModel):
    """Soft-warn and hard-kill cost limits applied to a single agent run."""
    model_config = ConfigDict(extra="forbid")

    soft_warn_usd: float = 1.0
    hard_kill_usd: float = 5.0

    @classmethod
    def from_env(cls) -> CostCap:
        raw = os.environ.get("AGENTSUITE_COST_CAP_USD")
        if raw is None:
            return cls()
        try:
            hard = float(raw)
        except ValueError:
            raise ValueError(
                f"AGENTSUITE_COST_CAP_USD={raw!r} is not a valid dollar amount. "
                "Set it to a number like '5.00'."
            )
        if hard <= 0:
            raise ValueError(
                f"AGENTSUITE_COST_CAP_USD must be a positive number greater than 0, "
                f"got {hard!r}. Example: AGENTSUITE_COST_CAP_USD=10.00"
            )
        return cls(soft_warn_usd=hard * 0.2, hard_kill_usd=hard)


class CostTracker:
    """In-memory accumulator that enforces cost caps as costs are added.

    Boundary semantics: caps are exclusive — costs equal to ``hard_kill_usd``
    are accepted, only costs strictly greater raise ``HardCapExceeded``.
    Same for ``soft_warn_usd``: warning latches when total strictly exceeds.

    The tracker also keeps a per-stage breakdown when ``current_stage`` is
    set by the pipeline driver. This drives the ``cost_summary.json`` report
    written to each run directory so operators can see which stage cost what
    before approving the run.
    """

    def __init__(
        self,
        cap: CostCap | None = None,
        *,
        run_id: str | None = None,
        agent: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.cap = cap or CostCap.from_env()
        self.total = Cost()
        self.warned = False
        # Per-stage breakdown, populated when the pipeline driver sets
        # ``current_stage`` before invoking each stage handler.
        self.per_stage: dict[Stage, Cost] = {}
        self.current_stage: Stage | None = None
        # Identity fields surfaced in cost_summary.json. May be set after
        # construction (the pipeline driver knows run_id/agent; the agent's
        # first LLM call provides provider/model).
        self.run_id: str | None = run_id
        self.agent: str | None = agent
        self.provider: str | None = provider

    def add(self, cost: Cost) -> Cost:
        new_total = self.total + cost
        if new_total.usd > self.cap.hard_kill_usd:
            raise HardCapExceeded(
                f"Cost ${new_total.usd:.4f} would exceed hard cap "
                f"${self.cap.hard_kill_usd:.2f}"
            )
        self.total = new_total
        if self.current_stage is not None:
            existing = self.per_stage.get(self.current_stage, Cost())
            self.per_stage[self.current_stage] = existing + cost
        if not self.warned and self.total.usd > self.cap.soft_warn_usd:
            self.warned = True
        return self.total

    def summary(self) -> dict[str, Any]:
        """Return a JSON-serializable summary of token + dollar usage.

        Schema (frozen for v0.9.0):

        ``run_id, agent, provider, model``: identity fields. ``model`` is
        the latest model recorded under ``self.total.model``; ``None`` if
        no LLM call recorded one.

        ``stages``: list of ``{"stage", "input_tokens", "output_tokens",
        "cost_usd", "model"}`` ordered by ``Stage`` enum order.

        ``total_input_tokens, total_output_tokens, total_cost_usd``: scalars.

        ``cap_usd, cap_remaining_usd, cap_warned``: caller can present these
        to the operator as a budget signal before approving the run.
        """
        # Order stages by the canonical pipeline order so consumers don't
        # have to sort them themselves.
        canonical_order: tuple[Stage, ...] = get_args(Stage)
        stages_in_order = [s for s in canonical_order if s in self.per_stage]
        return {
            "run_id": self.run_id,
            "agent": self.agent,
            "provider": self.provider,
            "model": self.total.model,
            "stages": [
                {
                    "stage": s,
                    "input_tokens": self.per_stage[s].input_tokens,
                    "output_tokens": self.per_stage[s].output_tokens,
                    "cost_usd": round(self.per_stage[s].usd, 6),
                    "model": self.per_stage[s].model,
                }
                for s in stages_in_order
            ],
            "total_input_tokens": self.total.input_tokens,
            "total_output_tokens": self.total.output_tokens,
            "total_cost_usd": round(self.total.usd, 6),
            "cap_usd": self.cap.hard_kill_usd,
            "cap_remaining_usd": round(
                max(0.0, self.cap.hard_kill_usd - self.total.usd), 6
            ),
            "cap_warned": self.warned,
        }

    def save_summary(self, path: Path) -> None:
        """Write :meth:`summary` to ``path`` as JSON, parents created if needed."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.summary(), f, indent=2)
