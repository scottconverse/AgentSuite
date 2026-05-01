"""Input schema for the Marketing Agent."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field

from agentsuite.kernel.schema import AgentRequest


class MarketingAgentInput(AgentRequest):
    brand_name: str                            # name of the brand or product being marketed
    campaign_goal: str = Field(min_length=1)   # what the campaign is trying to achieve
    target_market: str                         # who the campaign is targeting
    inputs_dir: Optional[Path] = None          # existing brand assets, briefs, research docs
    existing_brand_docs: list[Path] = []       # brand guidelines, positioning docs, style guides
    competitor_docs: list[Path] = []           # competitor analysis, market research docs
    budget_range: str = ""                     # e.g. "$50k–$100k over 3 months"
    timeline: str = ""                         # e.g. "Q3 2024, 12-week campaign"
    channels: str = ""                         # e.g. "paid social, email, content marketing"
    agent_name: str = "marketing"
    role_domain: str = "marketing-ops"
