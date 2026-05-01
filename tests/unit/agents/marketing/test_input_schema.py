"""Unit tests for marketing.input_schema."""
import pytest
from pydantic import ValidationError

from agentsuite.agents.marketing.input_schema import MarketingAgentInput


def test_minimal_inputs_construct():
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="create a campaign for our new product",
        brand_name="Acme Corp",
        campaign_goal="increase brand awareness among millennials",
        target_market="US millennials aged 25-35 interested in fitness",
    )
    assert inp.brand_name == "Acme Corp"
    assert inp.campaign_goal == "increase brand awareness among millennials"
    assert inp.target_market == "US millennials aged 25-35 interested in fitness"


def test_brand_name_required():
    with pytest.raises(ValidationError):
        MarketingAgentInput(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request="x",
            campaign_goal="increase awareness",
            target_market="millennials",
        )


def test_campaign_goal_required():
    with pytest.raises(ValidationError):
        MarketingAgentInput(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request="x",
            brand_name="Acme Corp",
            target_market="millennials",
        )


def test_target_market_required():
    with pytest.raises(ValidationError):
        MarketingAgentInput(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request="x",
            brand_name="Acme Corp",
            campaign_goal="increase awareness",
        )


def test_agent_name_defaults_to_marketing():
    inp = MarketingAgentInput(
        user_request="x",
        brand_name="Acme Corp",
        campaign_goal="increase awareness",
        target_market="millennials",
    )
    assert inp.agent_name == "marketing"


def test_inputs_dir_defaults_to_none():
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="x",
        brand_name="Acme Corp",
        campaign_goal="increase awareness",
        target_market="millennials",
    )
    assert inp.inputs_dir is None


def test_existing_brand_docs_defaults_to_empty():
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="x",
        brand_name="Acme Corp",
        campaign_goal="increase awareness",
        target_market="millennials",
    )
    assert inp.existing_brand_docs == []


def test_competitor_docs_defaults_to_empty():
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="x",
        brand_name="Acme Corp",
        campaign_goal="increase awareness",
        target_market="millennials",
    )
    assert inp.competitor_docs == []


def test_budget_range_defaults_to_empty_string():
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="x",
        brand_name="Acme Corp",
        campaign_goal="increase awareness",
        target_market="millennials",
    )
    assert inp.budget_range == ""


def test_timeline_defaults_to_empty_string():
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="x",
        brand_name="Acme Corp",
        campaign_goal="increase awareness",
        target_market="millennials",
    )
    assert inp.timeline == ""


def test_campaign_goal_empty_string_rejected():
    with pytest.raises(ValidationError):
        MarketingAgentInput(
            agent_name="marketing",
            role_domain="marketing-ops",
            user_request="create a campaign",
            brand_name="Acme Corp",
            campaign_goal="",
            target_market="millennials",
        )


def test_channels_defaults_to_empty_string():
    inp = MarketingAgentInput(
        agent_name="marketing",
        role_domain="marketing-ops",
        user_request="x",
        brand_name="Acme Corp",
        campaign_goal="increase awareness",
        target_market="millennials",
    )
    assert inp.channels == ""
