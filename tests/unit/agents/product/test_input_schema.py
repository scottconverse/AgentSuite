"""Unit tests for product.input_schema."""
import pytest
from pydantic import ValidationError

from agentsuite.agents.product.input_schema import ProductAgentInput


def test_minimal_inputs_construct():
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product-ops",
        user_request="create a PRD for checkout flow",
        product_name="Checkout Flow v2",
        target_users="e-commerce shoppers on mobile",
        core_problem="cart abandonment at payment step",
    )
    assert inp.product_name == "Checkout Flow v2"
    assert inp.target_users == "e-commerce shoppers on mobile"
    assert inp.core_problem == "cart abandonment at payment step"


def test_product_name_required():
    with pytest.raises(ValidationError):
        ProductAgentInput(
            agent_name="product",
            role_domain="product-ops",
            user_request="x",
            target_users="shoppers",
            core_problem="pain",
        )


def test_target_users_required():
    with pytest.raises(ValidationError):
        ProductAgentInput(
            agent_name="product",
            role_domain="product-ops",
            user_request="x",
            product_name="MyProduct",
            core_problem="pain",
        )


def test_core_problem_required():
    with pytest.raises(ValidationError):
        ProductAgentInput(
            agent_name="product",
            role_domain="product-ops",
            user_request="x",
            product_name="MyProduct",
            target_users="shoppers",
        )


def test_inputs_dir_defaults_to_none():
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product-ops",
        user_request="x",
        product_name="MyProduct",
        target_users="shoppers",
        core_problem="pain",
    )
    assert inp.inputs_dir is None


def test_research_docs_defaults_to_empty():
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product-ops",
        user_request="x",
        product_name="MyProduct",
        target_users="shoppers",
        core_problem="pain",
    )
    assert inp.research_docs == []


def test_competitor_docs_defaults_to_empty():
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product-ops",
        user_request="x",
        product_name="MyProduct",
        target_users="shoppers",
        core_problem="pain",
    )
    assert inp.competitor_docs == []


def test_technical_constraints_defaults_to_empty_string():
    inp = ProductAgentInput(
        agent_name="product",
        role_domain="product-ops",
        user_request="x",
        product_name="MyProduct",
        target_users="shoppers",
        core_problem="pain",
    )
    assert inp.technical_constraints == ""
