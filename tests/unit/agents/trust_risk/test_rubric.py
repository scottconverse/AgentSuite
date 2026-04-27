"""Unit tests for trust_risk.rubric."""
from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC


def test_rubric_is_trust_risk():
    from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC as _rubric
    assert _rubric is TRUST_RISK_RUBRIC


def test_rubric_has_nine_dimensions():
    assert len(TRUST_RISK_RUBRIC.dimensions) == 9


def test_rubric_pass_threshold_is_7_0():
    assert TRUST_RISK_RUBRIC.pass_threshold == 7.0


def test_rubric_dimensions_include_all_nine():
    names = [d.name for d in TRUST_RISK_RUBRIC.dimensions]
    assert "threat_coverage" in names
    assert "control_specificity" in names
    assert "risk_quantification" in names
    assert "regulatory_alignment" in names
    assert "incident_readiness" in names
    assert "zero_trust_posture" in names
    assert "vendor_risk_awareness" in names
    assert "audit_traceability" in names
    assert "residual_risk_acceptance" in names
