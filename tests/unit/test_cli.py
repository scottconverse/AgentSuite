"""Unit tests for the agentsuite CLI."""

import pytest
from typer.testing import CliRunner

from agentsuite.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_cli_help_lists_subcommands():
    result = _runner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "founder" in result.stdout
    assert "list-runs" in result.stdout


def test_cli_founder_run_with_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "Launch PFL",
        "--project-slug", "pfl",
        "--run-id", "r1",
    ])
    assert result.exit_code == 0
    assert "awaiting_approval" in result.stdout
    assert (tmp_path / "runs" / "r1" / "brand-system.md").exists()


def test_cli_list_runs_after_run(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "Launch PFL",
        "--project-slug", "pfl",
        "--run-id", "r1",
    ])
    result = _runner().invoke(app, ["list-runs"])
    assert result.exit_code == 0
    assert "r1" in result.stdout


def test_cli_approve_promotes(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "Launch PFL",
        "--project-slug", "pfl",
        "--run-id", "r1",
    ])
    result = _runner().invoke(app, [
        "founder", "approve",
        "--run-id", "r1",
        "--approver", "scott",
        "--project-slug", "pfl",
    ])
    assert result.exit_code == 0
    assert (tmp_path / "_kernel" / "pfl" / "brand-system.md").exists()


def test_cli_help_lists_design_subcommand():
    result = _runner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "design" in result.stdout


def test_cli_design_run_with_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "design", "run",
        "--target-audience", "developers",
        "--campaign-goal", "drive signups",
        "--run-id", "d1",
    ])
    assert result.exit_code == 0, result.stdout
    assert "awaiting_approval" in result.stdout
    assert (tmp_path / "runs" / "d1" / "visual-direction.md").exists()


def test_cli_design_approve_promotes(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    _runner().invoke(app, [
        "design", "run",
        "--target-audience", "developers",
        "--campaign-goal", "drive signups",
        "--run-id", "d1",
    ])
    result = _runner().invoke(app, [
        "design", "approve",
        "--run-id", "d1",
        "--approver", "scott",
        "--project-slug", "acme",
    ])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "_kernel" / "acme" / "visual-direction.md").exists()


# ---------------------------------------------------------------------------
# P10 — --help tests for the 5 remaining agents
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent_cmd", ["product", "engineering", "marketing", "trust-risk", "cio"])
def test_agent_run_help_exits_zero(agent_cmd):
    """Each agent's run --help should exit 0 and show Usage."""
    result = _runner().invoke(app, [agent_cmd, "run", "--help"])
    assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
    assert "Usage" in result.output


@pytest.mark.parametrize("agent_cmd", ["product", "engineering", "marketing", "trust-risk", "cio"])
def test_agent_approve_help_exits_zero(agent_cmd):
    """Each agent with an approve command should show --help without error."""
    result = _runner().invoke(app, [agent_cmd, "approve", "--help"])
    assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
    assert "Usage" in result.output


# ---------------------------------------------------------------------------
# P10 — full run tests for the 5 remaining agents
# ---------------------------------------------------------------------------

def test_cli_product_run_with_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "product", "run",
        "--product-name", "TestProduct",
        "--target-users", "QA engineers",
        "--core-problem", "too much manual work",
        "--project-slug", "testproduct",
        "--run-id", "p1",
    ])
    assert result.exit_code == 0, result.output
    assert "awaiting_approval" in result.output
    assert (tmp_path / "runs" / "p1" / "product-requirements-doc.md").exists()


def test_cli_engineering_run_with_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "engineering", "run",
        "--system-name", "TestSystem",
        "--problem-domain", "Web API",
        "--tech-stack", "Python FastAPI",
        "--scale-requirements", "1k RPS",
        "--run-id", "e1",
    ])
    assert result.exit_code == 0, result.output
    assert "awaiting_approval" in result.output
    assert (tmp_path / "runs" / "e1" / "architecture-decision-record.md").exists()


def test_cli_marketing_run_with_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "marketing", "run",
        "--brand-name", "TestBrand",
        "--campaign-goal", "Drive signups",
        "--target-market", "SMBs",
        "--run-id", "m1",
    ])
    assert result.exit_code == 0, result.output
    assert "awaiting_approval" in result.output
    assert (tmp_path / "runs" / "m1" / "campaign-brief.md").exists()


def test_cli_trust_risk_run_with_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "trust-risk", "run",
        "--product-name", "SecureApp",
        "--risk-domain", "cloud infrastructure",
        "--stakeholder-context", "CISO and risk team",
        "--run-id", "tr1",
    ])
    assert result.exit_code == 0, result.output
    assert "awaiting_approval" in result.output
    assert (tmp_path / "runs" / "tr1" / "threat-model.md").exists()


def test_cli_cio_run_with_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "cio", "run",
        "--organization-name", "TechCorp",
        "--strategic-priorities", "cloud-first, AI adoption",
        "--it-maturity-level", "Level 3 - Defined",
        "--run-id", "cio1",
    ])
    assert result.exit_code == 0, result.output
    assert "awaiting_approval" in result.output
    assert (tmp_path / "runs" / "cio1" / "it-strategy.md").exists()
