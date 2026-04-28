"""Unit tests for the agentsuite CLI."""

import json
from unittest.mock import MagicMock, patch

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


# ---------------------------------------------------------------------------
# D2 — --debug flag: traceback vs clean error message
# ---------------------------------------------------------------------------

def test_approve_error_without_debug_shows_clean_message(tmp_path, monkeypatch):
    """Without --debug, a failing approve prints 'Error: ...' without traceback."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    # First create a run so state exists
    _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "D2 test",
        "--project-slug", "d2proj",
        "--run-id", "d2r1",
    ])
    # Patch approve to raise so we can observe error handling
    with patch("agentsuite.agents.founder.agent.FounderAgent.approve", side_effect=RuntimeError("boom")):
        result = _runner().invoke(app, [
            "founder", "approve",
            "--run-id", "d2r1",
            "--approver", "tester",
            "--project-slug", "d2proj",
        ])
    assert result.exit_code == 1
    assert "Error: boom" in result.output
    assert "Traceback" not in result.output


def test_approve_error_with_debug_shows_traceback(tmp_path, monkeypatch):
    """With --debug, a failing approve includes a traceback."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "D2 debug test",
        "--project-slug", "d2proj",
        "--run-id", "d2r2",
    ])
    with patch("agentsuite.agents.founder.agent.FounderAgent.approve", side_effect=RuntimeError("kaboom")):
        result = _runner().invoke(app, [
            "--debug",
            "founder", "approve",
            "--run-id", "d2r2",
            "--approver", "tester",
            "--project-slug", "d2proj",
        ], catch_exceptions=False)
    assert result.exit_code == 1
    assert "Traceback" in result.output


# ---------------------------------------------------------------------------
# D3 — --latest flag on approve
# ---------------------------------------------------------------------------

def test_approve_latest_approves_most_recent_run(tmp_path, monkeypatch):
    """--latest resolves the most recently created run and approves it."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    # Create two runs — r_latest is created second
    for run_id in ["r_older", "r_latest"]:
        _runner().invoke(app, [
            "founder", "run",
            "--business-goal", "D3 test",
            "--project-slug", "d3proj",
            "--run-id", run_id,
        ])
    result = _runner().invoke(app, [
        "founder", "approve",
        "--latest",
        "--approver", "tester",
        "--project-slug", "d3proj",
    ])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out["run_id"] == "r_latest"
    assert (tmp_path / "_kernel" / "d3proj" / "brand-system.md").exists()


def test_approve_latest_errors_when_no_runs(tmp_path, monkeypatch):
    """--latest exits 1 with a clean error when no runs exist."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "founder", "approve",
        "--latest",
        "--approver", "tester",
        "--project-slug", "noproj",
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_approve_no_run_id_no_latest_exits_error(tmp_path, monkeypatch):
    """Omitting both --run-id and --latest exits 1 with a helpful message."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    result = _runner().invoke(app, [
        "founder", "approve",
        "--approver", "tester",
        "--project-slug", "noproj",
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


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
