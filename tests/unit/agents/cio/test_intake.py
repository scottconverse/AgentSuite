"""Unit tests for agentsuite.agents.cio.stages.intake."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from agentsuite.agents.cio.input_schema import CIOAgentInput
from agentsuite.agents.cio.stages.intake import intake_stage
from agentsuite.kernel.artifacts import ArtifactWriter
from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.cost import CostTracker
from agentsuite.kernel.schema import RunState


def _make_state(tmp_path: Path, **overrides: object) -> RunState:
    defaults: dict[str, object] = {
        "agent_name": "cio",
        "role_domain": "cio-ops",
        "user_request": "build an IT strategy for our organization",
        "organization_name": "Acme Corp",
        "strategic_priorities": "cloud migration, AI adoption, cybersecurity hardening",
        "it_maturity_level": "Level 2 – Repeatable",
    }
    defaults.update(overrides)
    inp = CIOAgentInput(**defaults)  # type: ignore[arg-type]
    return RunState(run_id="r1", agent="cio", inputs=inp)


def _make_ctx(tmp_path: Path, llm: object = None) -> StageContext:
    writer = ArtifactWriter(output_root=tmp_path, run_id="r1")
    edits: dict[str, object] = {}
    if llm is not None:
        edits["llm"] = llm
    return StageContext(writer=writer, cost_tracker=CostTracker(), edits=edits)


def _manifest_path(tmp_path: Path) -> Path:
    return tmp_path / "runs" / "r1" / "inputs_manifest.json"


def test_intake_writes_manifest(tmp_path: Path) -> None:
    """intake_stage writes inputs_manifest.json to the run dir."""
    doc = tmp_path / "it-strategy.pdf"
    doc.write_text("IT strategy document")
    state = _make_state(tmp_path, existing_it_docs=[doc])
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    assert _manifest_path(tmp_path).exists()
    data = json.loads(_manifest_path(tmp_path).read_text())
    assert "sources" in data
    assert "source_count" in data


def test_intake_advances_stage(tmp_path: Path) -> None:
    """intake_stage returns state with stage == 'extract'."""
    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path)
    result = intake_stage(state, ctx)
    assert result.stage == "extract"


def test_intake_with_no_docs(tmp_path: Path) -> None:
    """intake_stage succeeds with empty existing_it_docs."""
    state = _make_state(tmp_path, existing_it_docs=[])
    ctx = _make_ctx(tmp_path)
    result = intake_stage(state, ctx)
    assert result.stage == "extract"
    data = json.loads(_manifest_path(tmp_path).read_text())
    assert data["sources"] == []
    assert data["source_count"] == 0


def test_intake_source_count_matches(tmp_path: Path) -> None:
    """source_count in manifest matches len(existing_it_docs)."""
    docs = []
    for name in ("roadmap.pdf", "architecture.docx", "governance-policy.md"):
        p = tmp_path / name
        p.write_text(f"content of {name}")
        docs.append(p)
    state = _make_state(tmp_path, existing_it_docs=docs)
    ctx = _make_ctx(tmp_path)
    intake_stage(state, ctx)
    data = json.loads(_manifest_path(tmp_path).read_text())
    assert data["source_count"] == len(docs)
    assert len(data["sources"]) == len(docs)


def test_intake_renders_prompt(tmp_path: Path) -> None:
    """intake_stage calls LLM with a prompt containing organization_name."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.input_tokens = 10
    mock_response.output_tokens = 20
    mock_response.usd = 0.001
    mock_llm.complete.return_value = mock_response

    state = _make_state(tmp_path)
    ctx = _make_ctx(tmp_path, llm=mock_llm)
    intake_stage(state, ctx)

    assert mock_llm.complete.called
    call_args = mock_llm.complete.call_args
    request = call_args[0][0]
    assert "Acme Corp" in request.prompt
