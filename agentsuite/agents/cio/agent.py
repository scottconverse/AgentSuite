"""CIOAgent — wires the kernel BaseAgent to CIO stage handlers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentsuite.agents.cio.rubric import CIO_RUBRIC
from agentsuite.agents.cio.stages.execute import execute_stage
from agentsuite.agents.cio.stages.extract import extract_stage
from agentsuite.agents.cio.stages.intake import intake_stage
from agentsuite.agents.cio.stages.qa import qa_stage
from agentsuite.agents.cio.stages.spec import spec_stage
from agentsuite.kernel.base_agent import BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class CIOAgent(BaseAgent):
    """Concrete agent that produces CIO strategy and IT roadmap artifacts.

    Subclasses BaseAgent. Wires the 5 CIO stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "cio"
    qa_rubric = CIO_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see CIOAgentInput-specific fields.
        """
        from agentsuite.agents.cio.input_schema import CIOAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, CIOAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as organization_name. Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, CIOAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    elif isinstance(typed_inputs, dict):
                        state = state.model_copy(update={
                            "inputs": CIOAgentInput(**typed_inputs)
                        })
                    else:
                        state = state.model_copy(update={
                            "inputs": CIOAgentInput.model_validate(state.inputs.model_dump())
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
