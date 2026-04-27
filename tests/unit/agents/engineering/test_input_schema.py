"""Unit tests for engineering.input_schema."""
import pytest
from pydantic import ValidationError

from agentsuite.agents.engineering.input_schema import EngineeringAgentInput


def test_minimal_inputs_construct():
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering-ops",
        user_request="design the auth service",
        system_name="Auth Service",
        problem_domain="user authentication and authorization",
        tech_stack="Python + FastAPI + PostgreSQL + Redis",
        scale_requirements="10k RPM, 99.9% uptime, <200ms p99",
    )
    assert inp.system_name == "Auth Service"
    assert inp.problem_domain == "user authentication and authorization"
    assert inp.tech_stack == "Python + FastAPI + PostgreSQL + Redis"
    assert inp.scale_requirements == "10k RPM, 99.9% uptime, <200ms p99"


def test_system_name_required():
    with pytest.raises(ValidationError):
        EngineeringAgentInput(
            agent_name="engineering",
            role_domain="engineering-ops",
            user_request="x",
            problem_domain="auth",
            tech_stack="Python",
            scale_requirements="10k RPM",
        )


def test_problem_domain_required():
    with pytest.raises(ValidationError):
        EngineeringAgentInput(
            agent_name="engineering",
            role_domain="engineering-ops",
            user_request="x",
            system_name="Auth Service",
            tech_stack="Python",
            scale_requirements="10k RPM",
        )


def test_tech_stack_required():
    with pytest.raises(ValidationError):
        EngineeringAgentInput(
            agent_name="engineering",
            role_domain="engineering-ops",
            user_request="x",
            system_name="Auth Service",
            problem_domain="auth",
            scale_requirements="10k RPM",
        )


def test_scale_requirements_required():
    with pytest.raises(ValidationError):
        EngineeringAgentInput(
            agent_name="engineering",
            role_domain="engineering-ops",
            user_request="x",
            system_name="Auth Service",
            problem_domain="auth",
            tech_stack="Python",
        )


def test_inputs_dir_defaults_to_none():
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering-ops",
        user_request="x",
        system_name="Auth Service",
        problem_domain="auth",
        tech_stack="Python",
        scale_requirements="10k RPM",
    )
    assert inp.inputs_dir is None


def test_existing_codebase_docs_defaults_to_empty():
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering-ops",
        user_request="x",
        system_name="Auth Service",
        problem_domain="auth",
        tech_stack="Python",
        scale_requirements="10k RPM",
    )
    assert inp.existing_codebase_docs == []


def test_security_requirements_defaults_to_empty_string():
    inp = EngineeringAgentInput(
        agent_name="engineering",
        role_domain="engineering-ops",
        user_request="x",
        system_name="Auth Service",
        problem_domain="auth",
        tech_stack="Python",
        scale_requirements="10k RPM",
    )
    assert inp.security_requirements == ""
