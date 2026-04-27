"""Input schema for the CIO Agent."""
from __future__ import annotations

from pathlib import Path

from agentsuite.kernel.schema import AgentRequest


class CIOAgentInput(AgentRequest):
    organization_name: str                          # name of the organization being assessed
    strategic_priorities: str                       # top IT/digital strategic priorities
    it_maturity_level: str                          # e.g. "Level 1 – Ad hoc", "Level 3 – Defined"
    existing_it_docs: list[Path] = []               # existing IT strategy, roadmap, or architecture docs
    budget_context: str = ""                        # e.g. "flat budget", "$5M annual IT capex"
    digital_initiatives: str = ""                   # active or planned digital transformation programs
    regulatory_environment: str = ""               # e.g. "HIPAA, SOX, FedRAMP"
    agent_name: str = "cio"
    role_domain: str = "cio-ops"
