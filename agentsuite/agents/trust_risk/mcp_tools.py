"""MCP tool wrappers for the Trust/Risk agent."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from agentsuite.agents._common import require_kernel_dir, require_run_dir
from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput
from agentsuite.kernel.schema import RunState, Stage
from agentsuite.kernel.state_store import StateStore
from agentsuite.mcp_models import ApprovalResult, RunResult, RunSummary

SPEC_ARTIFACTS = [
    "threat-model",
    "risk-register",
    "control-framework",
    "incident-response-plan",
    "compliance-matrix",
    "vendor-risk-assessment",
    "security-policy",
    "audit-readiness-report",
    "residual-risk-acceptance",
]

TEMPLATE_NAMES = [
    "breach-notification",
    "executive-risk-summary",
    "penetration-test-brief",
    "remediation-tracker",
    "risk-acceptance-form",
    "security-awareness-brief",
    "tabletop-exercise-scenario",
    "vendor-security-questionnaire",
]


class TrustRiskRunRequest(TrustRiskAgentInput):
    """MCP-facing input for trust_risk_run. Adds optional run_id, supplies sane defaults."""

    run_id: str | None = None
    agent_name: str = "trust_risk"
    role_domain: str = "trust-risk-ops"
    user_request: str = "run trust risk agent"


def _now_id() -> str:
    return "run-" + datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _summary_from_state(state: RunState) -> str:
    parts = [f"agent={state.agent}", f"stage={state.stage}"]
    if state.requires_revision:
        parts.append("revision_required")
    if state.open_questions:
        parts.append(f"{len(state.open_questions)} open questions")
    parts.append(f"cost=${state.cost_so_far.usd:.4f}")
    return "; ".join(parts)


def _result_from_state(state: RunState, run_dir: Path) -> RunResult:
    primary = run_dir / "threat-model.md"
    status = "awaiting_approval"
    if state.stage == "done":
        status = "done"
    elif state.requires_revision:
        status = "needs_revision"
    return RunResult(
        run_id=state.run_id,
        status=status,  # type: ignore[arg-type]
        primary_path=str(primary),
        summary=_summary_from_state(state),
        open_questions=state.open_questions,
        requires_revision=state.requires_revision,
        cost_usd=state.cost_so_far.usd,
    )


def register_tools(
    server: Any,
    agent_class: Callable[[], Any],
    output_root_fn: Callable[[], Path],
    expose_stages: bool,
) -> None:
    """Register the 10 Trust/Risk MCP tools (and 5 stage tools if expose_stages)."""

    def agentsuite_trust_risk_run(request: TrustRiskRunRequest) -> RunResult:
        """Run the trust/risk pipeline for a given product and risk domain."""
        run_id = request.run_id or _now_id()
        agent = agent_class()
        trust_risk_input = TrustRiskAgentInput(**request.model_dump(exclude={"run_id"}))
        state = agent.run(request=trust_risk_input, run_id=run_id)
        run_dir = output_root_fn() / "runs" / run_id
        return _result_from_state(state, run_dir)

    def agentsuite_trust_risk_approve(run_id: str, approver: str, project_slug: str) -> ApprovalResult:
        """Approve a trust/risk run and promote artifacts to the kernel."""
        agent = agent_class()
        state = agent.approve(run_id=run_id, approver=approver, project_slug=project_slug)
        kernel_dir = require_kernel_dir(output_root_fn, project_slug)
        promoted = [
            str(p.relative_to(output_root_fn()))
            for p in kernel_dir.rglob("*")
            if p.is_file()
        ]
        return ApprovalResult(
            run_id=run_id,
            status="done",
            promoted_paths=promoted,
            approved_at=state.approved_at or datetime.now(tz=timezone.utc),
            approved_by=approver,
        )

    def agentsuite_trust_risk_list_runs(project_slug: str | None = None) -> list[RunSummary]:
        """List all trust/risk agent runs."""
        runs_root = output_root_fn() / "runs"
        if not runs_root.exists():
            return []
        out: list[RunSummary] = []
        for d in sorted(runs_root.iterdir()):
            if not d.is_dir():
                continue
            state = StateStore(run_dir=d).load()
            if state is None or state.agent != "trust_risk":
                continue
            out.append(RunSummary(
                run_id=state.run_id,
                agent=state.agent,
                stage=state.stage,
                started_at=state.started_at,
                cost_usd=state.cost_so_far.usd,
            ))
        return out

    def agentsuite_trust_risk_get_artifact(run_id: str, artifact_name: str) -> dict[str, Any]:
        """Get a specific artifact by name from a trust/risk run.

        artifact_name must be one of: threat-model, risk-register, control-framework,
        incident-response-plan, compliance-matrix, vendor-risk-assessment, security-policy,
        audit-readiness-report, residual-risk-acceptance.
        """
        run_dir = require_run_dir(output_root_fn, run_id)
        artifact_path = run_dir / f"{artifact_name}.md"
        if not artifact_path.exists():
            return {"error": f"Artifact '{artifact_name}' not found in run {run_id}", "path": str(artifact_path)}
        return {"run_id": run_id, "artifact_name": artifact_name, "content": artifact_path.read_text(encoding="utf-8"), "path": str(artifact_path)}

    def agentsuite_trust_risk_list_artifacts(run_id: str) -> dict[str, Any]:
        """List all available artifacts for a trust/risk run."""
        run_dir = require_run_dir(output_root_fn, run_id)
        available = [
            name for name in SPEC_ARTIFACTS
            if (run_dir / f"{name}.md").exists()
        ]
        return {"run_id": run_id, "artifacts": available, "all_possible": SPEC_ARTIFACTS}

    def agentsuite_trust_risk_get_qa_scores(run_id: str) -> dict[str, Any]:
        """Get QA scores for a trust/risk run."""
        run_dir = require_run_dir(output_root_fn, run_id)
        state = StateStore(run_dir=run_dir).load()
        if state is None:
            return {"error": f"No state file for run_id={run_id}"}
        qa_path = run_dir / "qa-scores.json"
        if qa_path.exists():
            import json
            return {"run_id": run_id, "scores": json.loads(qa_path.read_text(encoding="utf-8"))}
        return {"run_id": run_id, "scores": None, "note": "QA scores not yet available — run may still be in progress"}

    def agentsuite_trust_risk_get_brief_template(template_name: str) -> dict[str, Any]:
        """Get a brief template by name.

        template_name must be one of: breach-notification, executive-risk-summary,
        penetration-test-brief, remediation-tracker, risk-acceptance-form,
        security-awareness-brief, tabletop-exercise-scenario, vendor-security-questionnaire.
        """
        if template_name not in TEMPLATE_NAMES:
            return {"error": f"Unknown template '{template_name}'. Valid templates: {TEMPLATE_NAMES}"}
        templates_dir = output_root_fn() / "templates" / "trust_risk"
        template_path = templates_dir / f"{template_name}.md"
        if not template_path.exists():
            return {"error": f"Template '{template_name}' not found on disk", "path": str(template_path)}
        return {"template_name": template_name, "content": template_path.read_text(encoding="utf-8"), "path": str(template_path)}

    def agentsuite_trust_risk_list_brief_templates() -> dict[str, Any]:
        """List all available brief templates for trust/risk."""
        return {"templates": TEMPLATE_NAMES}

    def agentsuite_trust_risk_get_revision_instructions(run_id: str) -> dict[str, Any]:
        """Get revision instructions for a trust/risk run that requires revision."""
        run_dir = require_run_dir(output_root_fn, run_id)
        state = StateStore(run_dir=run_dir).load()
        if state is None:
            return {"error": f"No state file for run_id={run_id}"}
        return {
            "run_id": run_id,
            "requires_revision": state.requires_revision,
            "open_questions": state.open_questions,
            "revision_notes": getattr(state, "revision_notes", None),
        }

    def agentsuite_trust_risk_get_run_status(run_id: str) -> RunState:
        """Get the current status of a trust/risk run."""
        run_dir = require_run_dir(output_root_fn, run_id)
        state = StateStore(run_dir=run_dir).load()
        if state is None:
            raise FileNotFoundError(f"No state file for run_id={run_id}")
        return state

    server.add_tool("agentsuite_trust_risk_run", agentsuite_trust_risk_run)
    server.add_tool("agentsuite_trust_risk_approve", agentsuite_trust_risk_approve)
    server.add_tool("agentsuite_trust_risk_list_runs", agentsuite_trust_risk_list_runs)
    server.add_tool("agentsuite_trust_risk_get_artifact", agentsuite_trust_risk_get_artifact)
    server.add_tool("agentsuite_trust_risk_list_artifacts", agentsuite_trust_risk_list_artifacts)
    server.add_tool("agentsuite_trust_risk_get_qa_scores", agentsuite_trust_risk_get_qa_scores)
    server.add_tool("agentsuite_trust_risk_get_brief_template", agentsuite_trust_risk_get_brief_template)
    server.add_tool("agentsuite_trust_risk_list_brief_templates", agentsuite_trust_risk_list_brief_templates)
    server.add_tool("agentsuite_trust_risk_get_revision_instructions", agentsuite_trust_risk_get_revision_instructions)
    server.add_tool("agentsuite_trust_risk_get_run_status", agentsuite_trust_risk_get_run_status)

    if expose_stages:
        def _stage_tool(stage: Stage) -> Any:
            def runner(run_id: str) -> RunResult:
                agent = agent_class()
                state = agent.resume(run_id=run_id, stage=stage, edits={})
                run_dir = require_run_dir(output_root_fn, run_id)
                return _result_from_state(state, run_dir)
            return runner

        server.add_tool("agentsuite_trust_risk_stage_intake", _stage_tool("intake"))
        server.add_tool("agentsuite_trust_risk_stage_extract", _stage_tool("extract"))
        server.add_tool("agentsuite_trust_risk_stage_spec", _stage_tool("spec"))
        server.add_tool("agentsuite_trust_risk_stage_execute", _stage_tool("execute"))
        server.add_tool("agentsuite_trust_risk_stage_qa", _stage_tool("qa"))
