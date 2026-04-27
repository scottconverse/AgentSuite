"""Input schema for the Product Agent."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from agentsuite.kernel.schema import AgentRequest


class ProductAgentInput(AgentRequest):
    """Inputs for the Product Agent. Extends AgentRequest."""

    product_name: str
    target_users: str  # who the product is for
    core_problem: str  # the problem being solved
    inputs_dir: Optional[Path] = None  # research docs, competitive teardowns, etc.
    research_docs: list[Path] = []  # user interviews, surveys, personas
    competitor_docs: list[Path] = []  # competitive teardowns, market maps
    technical_constraints: str = ""  # known technical limitations / platform constraints
    timeline_constraint: str = ""  # e.g. "MVP in 6 weeks"
    success_metric_goals: str = ""  # e.g. "10% DAU increase within 30 days"
