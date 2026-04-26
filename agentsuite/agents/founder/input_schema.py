"""Inputs accepted by the Founder agent."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import Field

from agentsuite.kernel.schema import AgentRequest


class FounderAgentInput(AgentRequest):
    """Inputs for the Founder agent — extends AgentRequest with founder-specific fields."""

    inputs_dir: Path | None = None
    repo_urls: list[str] = Field(default_factory=list)
    web_urls: list[str] = Field(default_factory=list)
    screenshots: list[Path] = Field(default_factory=list)
    explicit_brand_docs: list[Path] = Field(default_factory=list)
    founder_voice_samples: list[Path] = Field(default_factory=list)
    business_goal: str  # required (overrides AgentRequest's optional)
    project_slug: str | None = None
    current_state: Literal["pre-launch", "launched", "rebrand"] = "pre-launch"


def derive_project_slug(inp: FounderAgentInput) -> str:
    """Return ``inp.project_slug`` if set, otherwise slugify ``business_goal``.

    Slugify rules: lowercase, non-alphanumeric runs collapse to a single hyphen,
    truncate to 40 chars, strip trailing hyphens.
    """
    if inp.project_slug:
        return inp.project_slug
    raw = inp.business_goal.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return cleaned[:40].rstrip("-")
