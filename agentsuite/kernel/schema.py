"""Pydantic models for the AgentSuite kernel."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SourceKind = Literal[
    "brand-doc",
    "product-doc",
    "social",
    "repo",
    "listing",
    "screenshot",
    "voice-sample",
    "other",
]

ArtifactKind = Literal["spec", "brief", "prompt", "qa_report", "template", "data"]

Stage = Literal[
    "intake",
    "extract",
    "spec",
    "execute",
    "qa",
    "approval",
    "done",
]


class SourceMaterial(BaseModel):
    """A single source artifact (file, URL, screenshot) supplied to an agent."""
    model_config = ConfigDict(extra="forbid")
    kind: SourceKind
    path: Path
    url: str | None = None
    note: str | None = None


class Constraints(BaseModel):
    """Operational constraints that scope how an agent may act."""
    model_config = ConfigDict(extra="forbid")
    brand: list[str] = Field(default_factory=list)
    legal: list[str] = Field(default_factory=list)
    technical: list[str] = Field(default_factory=list)
    format: list[str] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    budget: list[str] = Field(default_factory=list)


class AgentRequest(BaseModel):
    """Inputs to a single agent invocation — the request the agent processes."""
    model_config = ConfigDict(extra="allow")
    agent_name: str
    role_domain: str
    user_request: str
    business_goal: str | None = None
    target_audience: str | None = None
    source_materials: list[SourceMaterial] = Field(default_factory=list)
    constraints: Constraints = Field(default_factory=Constraints)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class Cost(BaseModel):
    """Aggregable token + dollar cost record for one or more LLM calls."""
    model_config = ConfigDict(extra="forbid")
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0

    def __add__(self, other: Cost) -> Cost:
        return Cost(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            usd=self.usd + other.usd,
        )


class ArtifactRef(BaseModel):
    """Reference to a single artifact written during a run, with content hash."""
    model_config = ConfigDict(extra="forbid")
    path: Path
    kind: ArtifactKind
    stage: Stage
    sha256: str = Field(min_length=64, max_length=64)

    @field_validator("sha256")
    @classmethod
    def _hex_only(cls, v: str) -> str:
        int(v, 16)  # raises if not hex
        return v.lower()


class RunState(BaseModel):
    """Persisted state for an in-flight or completed agent run."""
    model_config = ConfigDict(extra="forbid")
    run_id: str
    agent: str
    stage: Stage = "intake"
    inputs: AgentRequest
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    cost_so_far: Cost = Field(default_factory=Cost)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    requires_revision: bool = False
    approved_at: datetime | None = None
    approved_by: str | None = None
