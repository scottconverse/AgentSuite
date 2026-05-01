"""Unit tests for founder.input_schema."""
import pytest
from pydantic import ValidationError

from agentsuite.agents.founder.input_schema import FounderAgentInput, derive_project_slug


def test_business_goal_required():
    with pytest.raises(ValidationError):
        FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="x",
        )


def test_minimum_input_works():
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="build me a brand system",
        business_goal="launch a municipal records SaaS",
    )
    assert inp.business_goal == "launch a municipal records SaaS"
    assert inp.repo_urls == []
    assert inp.current_state == "pre-launch"


def test_project_slug_optional_and_auto_derived_when_missing():
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="Launch PatentForgeLocal v1",
    )
    assert inp.project_slug is None
    assert derive_project_slug(inp) == "launch-patentforgelocal-v1"


def test_project_slug_explicit_overrides_derivation():
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="Launch PatentForgeLocal v1",
        project_slug="pfl",
    )
    assert derive_project_slug(inp) == "pfl"


def test_slug_truncates_to_40_chars():
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="A " * 50,
    )
    slug = derive_project_slug(inp)
    assert len(slug) <= 40


def test_business_goal_empty_string_rejected():
    with pytest.raises(ValidationError):
        FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="build me a brand system",
            business_goal="",
        )


def test_slug_is_alphanumeric_hyphen_only():
    inp = FounderAgentInput(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        business_goal="Launch! @ ProductX (v1.0)",
    )
    slug = derive_project_slug(inp)
    assert all(c.isalnum() or c == "-" for c in slug)
