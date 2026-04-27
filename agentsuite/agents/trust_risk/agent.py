"""TrustRiskAgent — wires the kernel BaseAgent to trust/risk stage handlers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC
from agentsuite.agents.trust_risk.stages.execute import execute_stage
from agentsuite.agents.trust_risk.stages.extract import extract_stage
from agentsuite.agents.trust_risk.stages.intake import intake_stage
from agentsuite.agents.trust_risk.stages.qa import qa_stage
from agentsuite.agents.trust_risk.stages.spec import spec_stage
from agentsuite.kernel.base_agent import BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class TrustRiskAgent(BaseAgent):
    """Concrete agent that produces trust and risk assessment artifacts.

    Subclasses BaseAgent. Wires the 5 trust/risk stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "trust_risk"
    qa_rubric = TRUST_RISK_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see TrustRiskAgentInput-specific fields.
        """
        from agentsuite.agents.trust_risk.input_schema import TrustRiskAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, TrustRiskAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as product_name. Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, TrustRiskAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    elif isinstance(typed_inputs, dict):
                        state = state.model_copy(update={
                            "inputs": TrustRiskAgentInput(**typed_inputs)
                        })
                    else:
                        state = state.model_copy(update={
                            "inputs": TrustRiskAgentInput.model_validate(state.inputs.model_dump())
                        })
                return handler(state, ctx)
            return runner

        return {
            "intake": _wrap(intake_stage),
            "extract": _wrap(extract_stage),
            "spec": _wrap(spec_stage),
            "execute": _wrap(execute_stage),
            "qa": _wrap(qa_stage),
        }
