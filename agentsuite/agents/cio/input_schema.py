"""Input schema for the CIO Agent."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import Field

from agentsuite.kernel.schema import AgentRequest


class CIOAgentInput(AgentRequest):
    organization_name: str                          # name of the organization being assessed
    strategic_priorities: str = Field(min_length=1) # top IT/digital strategic priorities
    it_maturity_level: str                          # e.g. "Level 1 – Ad hoc", "Level 3 – Defined"
    existing_it_docs: list[Path] = []               # existing IT strategy, roadmap, or architecture docs
    budget_context: str = ""                        # e.g. "flat budget", "$5M annual IT capex"
    digital_initiatives: str = ""                   # active or planned digital transformation programs
    regulatory_environment: str = ""               # e.g. "HIPAA, SOX, FedRAMP"
    cio_name: str = "CIO"                              # Name used as author/signatory in generated documents
    # Override "today" for reproducibility (e.g. golden-test fixtures, retro
    # reports). When ``None`` the execute stage uses today's UTC date so
    # quarter / fiscal-year strings reflect the actual run time.
    as_of_date: date | None = None
    agent_name: str = "cio"
    role_domain: str = "cio-ops"
