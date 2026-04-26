"""MCP tool input/output models."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RunResult(BaseModel):
    """Result envelope returned by founder_run / founder_resume / founder_get_status."""
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: Literal["awaiting_approval", "done", "timeout", "needs_revision"]
    primary_path: str
    summary: str
    open_questions: list[str] = Field(default_factory=list)
    requires_revision: bool = False
    cost_usd: float = 0.0


class ApprovalResult(BaseModel):
    """Result envelope returned by founder_approve."""
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: Literal["done"]
    promoted_paths: list[str]
    approved_at: datetime
    approved_by: str


class RunSummary(BaseModel):
    """Result envelope returned by founder_list_runs / agentsuite_cost_report."""
    model_config = ConfigDict(extra="forbid")

    run_id: str
    agent: str
    stage: str
    started_at: datetime
    cost_usd: float
