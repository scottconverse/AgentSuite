"""Input schema for the Engineering Agent."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field

from agentsuite.kernel.schema import AgentRequest


class EngineeringAgentInput(AgentRequest):
    system_name: str                          # name of the system being designed/documented
    problem_domain: str = Field(min_length=1)  # what problem does this system solve
    tech_stack: str                           # e.g. "Python + FastAPI + PostgreSQL + Redis"
    scale_requirements: str                   # e.g. "10k RPM, 99.9% uptime, <200ms p99"
    inputs_dir: Optional[Path] = None         # existing docs, ADRs, runbooks, code samples
    existing_codebase_docs: list[Path] = []   # architecture docs, READMEs, design docs
    adr_history: list[Path] = []              # existing Architecture Decision Records
    incident_history: list[Path] = []         # past incident reports / postmortems
    security_requirements: str = ""           # e.g. "SOC2 Type II, OWASP Top 10"
    team_size: str = ""                       # e.g. "3 engineers, 1 SRE"
