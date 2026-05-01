"""Pipeline state schema."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

PipelineStatus = Literal["running", "awaiting_approval", "done", "failed"]
StepStatus = Literal["pending", "running", "awaiting_approval", "done"]


class PipelineStepState(BaseModel):
    agent: str
    run_id: str
    status: StepStatus = "pending"
    cost_usd: float = 0.0


class PipelineState(BaseModel):
    pipeline_id: str
    project_slug: str
    business_goal: str
    agents: list[str]
    steps: list[PipelineStepState]
    current_step_index: int = 0
    auto_approve: bool = False
    status: PipelineStatus = "running"
    total_cost_usd: float = 0.0
    # Persisted so approve() can drive the next step without re-supplying inputs.
    inputs_dir: str | None = None
    agent_extras: dict[str, dict[str, Any]] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
