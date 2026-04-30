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
    assert "approval" in result.stdout
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
    assert "approval" in result.stdout
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
    assert "approval" in result.output
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
    assert "approval" in result.output
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
    assert "approval" in result.output
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
    assert "approval" in result.output
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
    assert "approval" in result.output
    assert (tmp_path / "runs" / "cio1" / "it-strategy.md").exists()


# ---------------------------------------------------------------------------
# B1 — unique run_id default
# ---------------------------------------------------------------------------

def test_run_id_defaults_to_unique_value(tmp_path, monkeypatch):
    """Two runs without explicit run_id should produce distinct IDs."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    r1 = _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "Test uniqueness run 1",
    ])
    r2 = _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "Test uniqueness run 2",
    ])
    assert r1.exit_code == 0, r1.output
    assert r2.exit_code == 0, r2.output
    import json

    def _extract_json(output: str) -> dict:
        """Extract the first JSON object from output that may include progress/hint lines."""
        idx = output.index("{")
        obj, _ = json.JSONDecoder().raw_decode(output, idx)
        return obj

    id1 = _extract_json(r1.output)["run_id"]
    id2 = _extract_json(r2.output)["run_id"]
    assert id1 != id2, f"Expected unique IDs but got {id1!r} twice"
    assert id1.startswith("run-"), f"Expected 'run-...' prefix, got {id1!r}"
    assert id2.startswith("run-"), f"Expected 'run-...' prefix, got {id2!r}"


# ---------------------------------------------------------------------------
# B2 — --force flag
# ---------------------------------------------------------------------------

def test_force_flag_blocks_existing_run(tmp_path, monkeypatch):
    """Running again with the same explicit run_id (no --force) should exit 1."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    # First run — creates the directory
    r1 = _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "Force test",
        "--run-id", "force-test-run",
    ])
    assert r1.exit_code == 0, r1.output
    assert (tmp_path / "runs" / "force-test-run").exists()

    # Second run — same ID, no --force → should be blocked
    r2 = _runner().invoke(app, [
        "founder", "run",
        "--business-goal", "Force test again",
        "--run-id", "force-test-run",
    ])
    assert r2.exit_code == 1
    assert "already exists" in (r2.output + (r2.stderr or ""))


def test_force_flag_allows_existing_run(tmp_path, monkeypatch):
    """Running again with --force should succeed even if the run directory exists."""
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("AGENTSUITE_LLM_PROVIDER_FACTORY", "agentsuite.llm.mock:_default_mock_for_cli")
    base_args = [
        "founder", "run",
        "--business-goal", "Force overwrite test",
        "--run-id", "force-overwrite-run",
    ]
    # First run
    r1 = _runner().invoke(app, base_args)
    assert r1.exit_code == 0, r1.output

    # Second run with --force — should succeed
    r2 = _runner().invoke(app, base_args + ["--force"])
    assert r2.exit_code == 0, r2.output
    assert "approval" in r2.output


# ---------------------------------------------------------------------------
# UX-201 — approve --latest catches RunStateSchemaVersionError cleanly
# ---------------------------------------------------------------------------

def test_approve_latest_handles_schema_version_error(tmp_path, monkeypatch):
    """approve --latest must not produce a raw traceback on RunStateSchemaVersionError."""
    import json

    # Create a run dir with an old-schema state file
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True)
    bad_run = runs_dir / "run-old"
    bad_run.mkdir()
    state_file = bad_run / "_state.json"
    state_file.write_text(json.dumps({
        "schema_version": 1,
        "run_id": "run-old",
        "agent": "founder",
        "stage": "done",
    }), encoding="utf-8")

    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["founder", "approve", "--latest", "--approver", "test", "--project-slug", "proj"],
    )
    # Should exit non-zero but NOT produce a raw traceback
    assert result.exit_code != 0
    assert "Traceback" not in (result.output or "")
    assert "RunStateSchemaVersionError" not in (result.output or "")


# ---------------------------------------------------------------------------
# QA-301 — list-runs commands skip pre-v0.9 schema dirs cleanly
# ---------------------------------------------------------------------------

def _write_pre_v09_state(tmp_path, run_name="run-old", agent="founder"):
    """Helper: create a runs/<run_name>/_state.json with schema_version=1."""
    import json

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    bad_run = runs_dir / run_name
    bad_run.mkdir()
    (bad_run / "_state.json").write_text(
        json.dumps({
            "schema_version": 1,
            "run_id": run_name,
            "agent": agent,
            "stage": "done",
        }),
        encoding="utf-8",
    )
    return bad_run


def test_cli_list_runs_skips_schema_version_mismatch_dirs(tmp_path, monkeypatch):
    """Global `list-runs` must exit 0 and not include a pre-v0.9 run."""
    _write_pre_v09_state(tmp_path, run_name="run-old", agent="founder")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    result = _runner().invoke(app, ["list-runs"])
    assert result.exit_code == 0
    assert "run-old" not in result.stdout
    # Must not surface a raw traceback
    assert "Traceback" not in (result.output or "")
    assert "RunStateSchemaVersionError" not in (result.output or "")


def test_cli_founder_list_runs_skips_schema_version_mismatch_dirs(tmp_path, monkeypatch):
    """Per-agent `<agent> list-runs` must exit 0 and not include a pre-v0.9 run.

    Founder doesn't expose a per-agent list-runs subcommand (has_list_runs=False);
    cio and trust_risk do. We exercise the CIO per-agent list-runs path here since
    that is the helper produced by ``_make_list_runs_fn`` in cli.py.
    """
    _write_pre_v09_state(tmp_path, run_name="run-old", agent="cio")
    monkeypatch.setenv("AGENTSUITE_OUTPUT_DIR", str(tmp_path))
    result = _runner().invoke(app, ["cio", "list-runs"])
    assert result.exit_code == 0, result.output
    assert "run-old" not in result.stdout
    assert "Traceback" not in (result.output or "")
    assert "RunStateSchemaVersionError" not in (result.output or "")
