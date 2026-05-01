"""Unit tests for trust_risk.mcp_tools — security (ENG-001) and happy-path coverage."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentsuite.agents.trust_risk.mcp_tools import SPEC_ARTIFACTS, register_tools


class _StubServer:
    def __init__(self) -> None:
        self.tools: dict = {}

    def add_tool(self, name: str, fn) -> None:
        self.tools[name] = fn

    def tool_names(self) -> list[str]:
        return list(self.tools.keys())


def _make_server(tmp_path: Path) -> _StubServer:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: None,  # agent not needed for artifact/template tools
        output_root_fn=lambda: tmp_path,
        expose_stages=False,
    )
    return server


# ---------------------------------------------------------------------------
# ENG-001: path traversal guard — artifact_name
# ---------------------------------------------------------------------------

def test_get_artifact_rejects_path_traversal(tmp_path: Path) -> None:
    """get_artifact must return an error dict (not file contents) for ../../.env."""
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_get_artifact"](
        run_id="run-safe-001", artifact_name="../../.env"
    )
    assert "error" in result
    assert ".env" not in result.get("content", "")


def test_get_artifact_rejects_unknown_artifact(tmp_path: Path) -> None:
    """get_artifact must return an error dict for an artifact name not in the allowlist."""
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_get_artifact"](
        run_id="run-safe-001", artifact_name="secret-data"
    )
    assert "error" in result
    assert "Unknown artifact" in result["error"]


def test_get_artifact_returns_content_for_valid_name(tmp_path: Path) -> None:
    """get_artifact must return file content when artifact_name is valid and file exists."""
    run_id = "run-tr-test"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    artifact_name = SPEC_ARTIFACTS[0]  # "threat-model"
    (run_dir / f"{artifact_name}.md").write_text("# Threat Model\nContent.", encoding="utf-8")

    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_get_artifact"](
        run_id=run_id, artifact_name=artifact_name
    )
    assert "error" not in result
    assert result["artifact_name"] == artifact_name
    assert "Threat Model" in result["content"]


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_tools_adds_ten_default_tools(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    expected = {
        "agentsuite_trust_risk_run",
        "agentsuite_trust_risk_approve",
        "agentsuite_trust_risk_list_runs",
        "agentsuite_trust_risk_get_artifact",
        "agentsuite_trust_risk_list_artifacts",
        "agentsuite_trust_risk_get_qa_scores",
        "agentsuite_trust_risk_get_brief_template",
        "agentsuite_trust_risk_list_brief_templates",
        "agentsuite_trust_risk_get_revision_instructions",
        "agentsuite_trust_risk_get_run_status",
    }
    assert expected == set(server.tool_names())


def test_register_tools_expose_stages_adds_fifteen_tools(tmp_path: Path) -> None:
    server = _StubServer()
    register_tools(
        server,
        agent_class=lambda: None,
        output_root_fn=lambda: tmp_path,
        expose_stages=True,
    )
    assert len(server.tools) == 15
    for stage_tool in (
        "agentsuite_trust_risk_stage_intake",
        "agentsuite_trust_risk_stage_extract",
        "agentsuite_trust_risk_stage_spec",
        "agentsuite_trust_risk_stage_execute",
        "agentsuite_trust_risk_stage_qa",
    ):
        assert stage_tool in server.tool_names()


# ---------------------------------------------------------------------------
# list_brief_templates smoke test
# ---------------------------------------------------------------------------

def test_list_brief_templates_returns_all_template_names(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_list_brief_templates"]()
    assert "templates" in result
    assert len(result["templates"]) == 8


def test_get_brief_template_rejects_unknown_name(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_get_brief_template"](template_name="../../hack")
    assert "error" in result


def test_list_runs_empty_when_no_runs(tmp_path: Path) -> None:
    server = _make_server(tmp_path)
    runs = server.tools["agentsuite_trust_risk_list_runs"]()
    assert runs == []


# ---------------------------------------------------------------------------
# UX-006 — trust_risk_list_runs filters by project_slug
# ---------------------------------------------------------------------------

def test_trust_risk_list_runs_filters_by_project_slug(tmp_path: Path) -> None:
    """agentsuite_trust_risk_list_runs(project_slug='x') must return only matching runs."""
    from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
    from agentsuite.kernel.schema import RunState, Cost
    from agentsuite.kernel.state_store import StateStore

    def _make_run(run_id: str, project_slug: str | None) -> None:
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        inp = TrustRiskAgentInput(
            agent_name="trust_risk",
            role_domain="trust-risk-ops",
            user_request="test",
            product_name="AcmePlatform",
            risk_domain="cloud infra",
            stakeholder_context="Engineering leads",
            project_slug=project_slug,
        )
        state = RunState(
            run_id=run_id,
            agent="trust_risk",
            stage="approval",
            inputs=inp,
            cost_so_far=Cost(),
        )
        StateStore(run_dir=run_dir).save(state)

    _make_run("tr-slug-a", "slug-a")
    _make_run("tr-slug-b", "slug-b")
    _make_run("tr-no-slug", None)

    server = _make_server(tmp_path)

    runs = server.tools["agentsuite_trust_risk_list_runs"](project_slug="slug-a")
    assert len(runs) == 1, f"Expected 1, got {len(runs)}: {[r.run_id for r in runs]}"
    assert runs[0].run_id == "tr-slug-a"

    runs = server.tools["agentsuite_trust_risk_list_runs"](project_slug="slug-b")
    assert len(runs) == 1
    assert runs[0].run_id == "tr-slug-b"

    runs = server.tools["agentsuite_trust_risk_list_runs"](project_slug=None)
    assert len(runs) == 3


# ---------------------------------------------------------------------------
# TEST-003: list_runs returns correct structure when runs exist
# ---------------------------------------------------------------------------

def test_list_runs_returns_run_summary_after_run(tmp_path: Path) -> None:
    """list_runs must return a RunSummary entry for each trust_risk run in the output dir."""
    from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
    from agentsuite.kernel.state_store import StateStore

    run_id = "r-tr-list-001"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    state = RunState(
        run_id=run_id,
        agent="trust_risk",
        stage="approval",
        inputs=AgentRequest(
            agent_name="trust_risk",
            role_domain="trust-risk-ops",
            user_request="test",
            constraints=Constraints(),
        ),
    )
    StateStore(run_dir=run_dir).save(state)

    server = _make_server(tmp_path)
    runs = server.tools["agentsuite_trust_risk_list_runs"]()
    assert len(runs) == 1
    assert runs[0].run_id == run_id
    assert runs[0].agent == "trust_risk"


def test_list_runs_excludes_other_agent_runs(tmp_path: Path) -> None:
    """list_runs must NOT return runs belonging to a different agent."""
    from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
    from agentsuite.kernel.state_store import StateStore

    for run_id, agent_name in [
        ("r-tr-mine", "trust_risk"),
        ("r-eng-other", "engineering"),
    ]:
        run_dir = tmp_path / "runs" / run_id
        run_dir.mkdir(parents=True)
        StateStore(run_dir=run_dir).save(RunState(
            run_id=run_id,
            agent=agent_name,
            stage="approval",
            inputs=AgentRequest(
                agent_name=agent_name,
                role_domain="ops",
                user_request="test",
                constraints=Constraints(),
            ),
        ))

    server = _make_server(tmp_path)
    runs = server.tools["agentsuite_trust_risk_list_runs"]()
    assert all(r.agent == "trust_risk" for r in runs)
    assert len(runs) == 1


# ---------------------------------------------------------------------------
# TEST-003: get_run_status round-trip
# ---------------------------------------------------------------------------

def test_trust_risk_get_run_status_returns_expected_fields(tmp_path: Path) -> None:
    """get_run_status must return a RunState with the correct run_id, agent, and stage."""
    from agentsuite.kernel.schema import AgentRequest, Constraints, RunState
    from agentsuite.kernel.state_store import StateStore

    run_id = "r-tr-status"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    StateStore(run_dir=run_dir).save(RunState(
        run_id=run_id,
        agent="trust_risk",
        stage="approval",
        inputs=AgentRequest(
            agent_name="trust_risk",
            role_domain="trust-risk-ops",
            user_request="test",
            constraints=Constraints(),
        ),
    ))

    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_get_run_status"](run_id)

    assert result.run_id == run_id
    assert result.agent == "trust_risk"
    assert result.stage == "approval"


def test_trust_risk_get_run_status_raises_on_missing_run(tmp_path: Path) -> None:
    """get_run_status must raise FileNotFoundError for an unknown run_id."""
    server = _make_server(tmp_path)
    with pytest.raises(FileNotFoundError):
        server.tools["agentsuite_trust_risk_get_run_status"]("nonexistent-run")


# ---------------------------------------------------------------------------
# TEST-001: parametrized encoded traversal variants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("malicious_name", [
    "../../.env",
    "..%2F..%2F.env",
    "..%252F.env",
    "..%2F../.env",
    "spec_brief\x00.md",
    "/etc/passwd",
    "../../../etc/passwd",
])
def test_get_artifact_rejects_all_traversal_variants(tmp_path: Path, malicious_name: str) -> None:
    """get_artifact must return an error dict for every encoded/raw traversal variant."""
    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_get_artifact"](
        run_id="run-safe-001", artifact_name=malicious_name
    )
    assert "error" in result, f"Expected error for {malicious_name!r}, got {result!r}"


@pytest.mark.parametrize("artifact_name", SPEC_ARTIFACTS)
def test_get_artifact_accepts_all_valid_names(tmp_path: Path, artifact_name: str) -> None:
    """get_artifact must accept every name in SPEC_ARTIFACTS when the file exists."""
    run_id = "run-tr-valid"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / f"{artifact_name}.md").write_text(f"# {artifact_name}\nContent.", encoding="utf-8")

    server = _make_server(tmp_path)
    result = server.tools["agentsuite_trust_risk_get_artifact"](
        run_id=run_id, artifact_name=artifact_name
    )
    assert "error" not in result, f"Unexpected error for {artifact_name!r}: {result.get('error')}"
    assert result["artifact_name"] == artifact_name
