"""Design Agent input schema."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field

from agentsuite.kernel.schema import AgentRequest


class DesignAgentInput(AgentRequest):
    """Inputs for the Design Agent. Extends AgentRequest."""

    model_config = ConfigDict(extra="allow")

    # Required design-specific
    target_audience: str
    campaign_goal: str = Field(min_length=1)

    # Channel — narrows downstream brief shape
    channel: Literal["web", "social", "email", "print", "video", "deck", "other"] = "web"

    # Optional inputs
    inputs_dir: Path | None = None
    brand_docs: list[Path] = Field(default_factory=list)
    reference_assets: list[Path] = Field(default_factory=list)
    anti_examples: list[Path] = Field(default_factory=list)
    accessibility_requirements: list[str] = Field(default_factory=list)
    project_slug: str | None = None
    promote_from_kernel: str | None = None
