"""Token + dollar accounting with cap enforcement."""
from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict

from agentsuite.kernel.schema import Cost


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
        hard = float(raw)
        return cls(soft_warn_usd=hard * 0.2, hard_kill_usd=hard)


class CostTracker:
    """In-memory accumulator that enforces cost caps as costs are added."""

    def __init__(self, cap: CostCap | None = None) -> None:
        self.cap = cap or CostCap.from_env()
        self.total = Cost()
        self.warned = False

    def add(self, cost: Cost) -> Cost:
        new_total = self.total + cost
        if new_total.usd > self.cap.hard_kill_usd:
            raise HardCapExceeded(
                f"Cost ${new_total.usd:.4f} would exceed hard cap "
                f"${self.cap.hard_kill_usd:.2f}"
            )
        self.total = new_total
        if not self.warned and self.total.usd > self.cap.soft_warn_usd:
            self.warned = True
        return self.total
