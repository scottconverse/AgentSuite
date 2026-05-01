"""Unit tests for design.input_schema."""
import pytest
from pydantic import ValidationError

from agentsuite.agents.design.input_schema import DesignAgentInput


def test_minimal_inputs_construct():
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="create a landing page hero",
        target_audience="solo founders building SaaS",
        campaign_goal="drive sign-ups",
    )
    assert inp.target_audience == "solo founders building SaaS"
    assert inp.campaign_goal == "drive sign-ups"


def test_default_channel_is_web():
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="awareness",
    )
    assert inp.channel == "web"


def test_channel_rejects_unknown_value():
    with pytest.raises(ValidationError):
        DesignAgentInput(
            agent_name="design",
            role_domain="creative-ops",
            user_request="x",
            target_audience="developers",
            campaign_goal="awareness",
            channel="hologram",
        )


def test_lists_default_to_empty():
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="awareness",
    )
    assert inp.brand_docs == []
    assert inp.reference_assets == []
    assert inp.anti_examples == []
    assert inp.accessibility_requirements == []


def test_inputs_dir_accepts_path_or_none():
    from pathlib import Path

    inp_none = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="awareness",
    )
    assert inp_none.inputs_dir is None

    inp_path = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="awareness",
        inputs_dir=Path("/tmp/brand"),
    )
    assert inp_path.inputs_dir == Path("/tmp/brand")


def test_promote_from_kernel_optional():
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="awareness",
    )
    assert inp.promote_from_kernel is None

    inp2 = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="awareness",
        promote_from_kernel="my-project",
    )
    assert inp2.promote_from_kernel == "my-project"


def test_campaign_goal_empty_string_rejected():
    with pytest.raises(ValidationError):
        DesignAgentInput(
            agent_name="design",
            role_domain="creative-ops",
            user_request="create a hero section",
            target_audience="developers",
            campaign_goal="",
        )


def test_extra_fields_allowed_for_round_trip():
    inp = DesignAgentInput(
        agent_name="design",
        role_domain="creative-ops",
        user_request="x",
        target_audience="developers",
        campaign_goal="awareness",
        custom_metadata="round-trip-value",
    )
    # extra="allow" means the field is accepted and accessible
    assert inp.model_extra is not None
    assert inp.model_extra.get("custom_metadata") == "round-trip-value"
