"""Unit tests for kernel.schema."""
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from agentsuite.kernel.schema import (
    AgentRequest,
    ArtifactRef,
    Constraints,
    Cost,
    RunState,
    SourceMaterial,
)


def test_source_material_requires_kind_and_path():
    sm = SourceMaterial(kind="brand-doc", path=Path("brand.md"))
    assert sm.kind == "brand-doc"
    assert sm.path == Path("brand.md")


def test_source_material_rejects_unknown_kind():
    with pytest.raises(ValidationError):
        SourceMaterial(kind="unknown-thing", path=Path("x"))


def test_constraints_defaults_to_empty_lists():
    c = Constraints()
    assert c.brand == []
    assert c.legal == []
    assert c.technical == []
    assert c.format == []
    assert c.timeline == []
    assert c.budget == []


def test_agent_request_minimum_fields():
    req = AgentRequest(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="Build me a brand system",
        constraints=Constraints(),
    )
    assert req.business_goal is None
    assert req.source_materials == []


def test_cost_addition_aggregates_tokens_and_dollars():
    a = Cost(input_tokens=100, output_tokens=50, usd=0.01)
    b = Cost(input_tokens=200, output_tokens=80, usd=0.02)
    total = a + b
    assert total.input_tokens == 300
    assert total.output_tokens == 130
    assert total.usd == pytest.approx(0.03)


def test_artifact_ref_requires_sha256():
    ref = ArtifactRef(
        path=Path("brand-system.md"),
        kind="spec",
        stage="spec",
        sha256="a" * 64,
    )
    assert ref.sha256 == "a" * 64


def test_artifact_ref_rejects_short_sha():
    with pytest.raises(ValidationError):
        ArtifactRef(path=Path("x"), kind="spec", stage="spec", sha256="abc")


def test_artifact_ref_rejects_non_hex_sha():
    with pytest.raises(ValidationError):
        ArtifactRef(path=Path("x"), kind="spec", stage="spec", sha256="g" * 64)


def test_run_state_initial_stage_is_intake():
    req = AgentRequest(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        constraints=Constraints(),
    )
    state = RunState(
        run_id="2026-04-26-test",
        agent="founder",
        stage="intake",
        inputs=req,
    )
    assert state.stage == "intake"
    assert state.artifacts == []
    assert state.open_questions == []
    assert state.cost_so_far.usd == 0.0
    assert isinstance(state.started_at, datetime)


def test_run_state_serializes_to_json_round_trip():
    req = AgentRequest(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="x",
        constraints=Constraints(),
    )
    state = RunState(run_id="r1", agent="founder", stage="intake", inputs=req)
    payload = state.model_dump_json()
    restored = RunState.model_validate_json(payload)
    assert restored.run_id == "r1"
    assert restored.stage == "intake"


def test_agent_request_json_round_trip_all_base_fields():
    """All AgentRequest base fields must survive a model_dump_json / model_validate_json cycle."""
    original = AgentRequest(
        agent_name="founder",
        role_domain="creative-ops",
        user_request="Build a brand system for PatentForgeLocal",
        business_goal="Reach 1,000 paying customers by Q4",
        target_audience="Solo inventors and patent attorneys",
        source_materials=[SourceMaterial(kind="brand-doc", path=Path("brand.md"))],
        constraints=Constraints(
            brand=["Use Inter font"],
            legal=["No medical claims"],
        ),
        assumptions=["The user has an Anthropic API key"],
        missing_information=["Pricing tier details"],
    )
    payload = original.model_dump_json()
    restored = AgentRequest.model_validate_json(payload)

    assert restored.agent_name == "founder"
    assert restored.role_domain == "creative-ops"
    assert restored.user_request == "Build a brand system for PatentForgeLocal"
    assert restored.business_goal == "Reach 1,000 paying customers by Q4"
    assert restored.target_audience == "Solo inventors and patent attorneys"
    assert len(restored.source_materials) == 1
    assert restored.source_materials[0].kind == "brand-doc"
    assert restored.constraints.brand == ["Use Inter font"]
    assert restored.constraints.legal == ["No medical claims"]
    assert restored.assumptions == ["The user has an Anthropic API key"]
    assert restored.missing_information == ["Pricing tier details"]


def test_agent_request_json_round_trip_extra_fields_preserved():
    """Extra fields (extra='allow') must survive round-trip — subclass pattern relies on this."""
    original = AgentRequest(
        agent_name="trust_risk",
        role_domain="trust-risk-ops",
        user_request="Assess cloud infra risk",
        constraints=Constraints(),
        product_name="SecureVault",   # extra field
        risk_domain="cloud-infra",    # extra field
    )
    payload = original.model_dump_json()
    restored = AgentRequest.model_validate_json(payload)

    assert restored.model_extra is not None
    assert restored.model_extra.get("product_name") == "SecureVault"
    assert restored.model_extra.get("risk_domain") == "cloud-infra"
