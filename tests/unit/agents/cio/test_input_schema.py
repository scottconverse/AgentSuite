"""Unit tests for cio.input_schema."""
import pytest
from pathlib import Path
from pydantic import ValidationError

from agentsuite.agents.cio.input_schema import CIOAgentInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal(**overrides) -> dict:
    base = dict(
        user_request="develop an IT strategy for our organization",
        organization_name="Acme Corp",
        strategic_priorities="cloud migration, cybersecurity, data analytics",
        it_maturity_level="Level 2 – Repeatable",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Required fields present
# ---------------------------------------------------------------------------

def test_required_fields_present():
    inp = CIOAgentInput(**_minimal())
    assert inp.organization_name == "Acme Corp"
    assert inp.strategic_priorities == "cloud migration, cybersecurity, data analytics"
    assert inp.it_maturity_level == "Level 2 – Repeatable"
    assert inp.user_request == "develop an IT strategy for our organization"


# ---------------------------------------------------------------------------
# 2. Optional fields defaults
# ---------------------------------------------------------------------------

def test_optional_fields_defaults():
    inp = CIOAgentInput(**_minimal())
    assert inp.existing_it_docs == []
    assert inp.budget_context == ""
    assert inp.digital_initiatives == ""
    assert inp.regulatory_environment == ""


# ---------------------------------------------------------------------------
# 3. agent_name default
# ---------------------------------------------------------------------------

def test_agent_name_default():
    inp = CIOAgentInput(**_minimal())
    assert inp.agent_name == "cio"


# ---------------------------------------------------------------------------
# 4. role_domain default
# ---------------------------------------------------------------------------

def test_role_domain_default():
    inp = CIOAgentInput(**_minimal())
    assert inp.role_domain == "cio-ops"


# ---------------------------------------------------------------------------
# 5. Invalid — missing required field (organization_name)
# ---------------------------------------------------------------------------

def test_invalid_missing_required():
    kwargs = _minimal()
    del kwargs["organization_name"]
    with pytest.raises(ValidationError):
        CIOAgentInput(**kwargs)


# ---------------------------------------------------------------------------
# 6. user_request is required (from AgentRequest base)
# ---------------------------------------------------------------------------

def test_user_request_required():
    kwargs = _minimal()
    del kwargs["user_request"]
    with pytest.raises(ValidationError):
        CIOAgentInput(**kwargs)


# ---------------------------------------------------------------------------
# 7. existing_it_docs accepts Path objects
# ---------------------------------------------------------------------------

def test_existing_it_docs_accepts_paths():
    paths = [Path("/docs/it_strategy.pdf"), Path("/docs/roadmap.pptx")]
    inp = CIOAgentInput(**_minimal(existing_it_docs=paths))
    assert inp.existing_it_docs == paths
    assert all(isinstance(p, Path) for p in inp.existing_it_docs)
