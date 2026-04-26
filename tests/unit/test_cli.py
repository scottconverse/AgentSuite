"""Unit tests for the agentsuite CLI."""
import json
from pathlib import Path

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
