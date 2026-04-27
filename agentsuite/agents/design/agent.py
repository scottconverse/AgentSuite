"""DesignAgent — wires the kernel BaseAgent to design stage handlers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentsuite.agents.design.rubric import DESIGN_RUBRIC
from agentsuite.agents.design.stages.execute import execute_stage
from agentsuite.agents.design.stages.extract import extract_stage
from agentsuite.agents.design.stages.intake import intake_stage
from agentsuite.agents.design.stages.qa import qa_stage
from agentsuite.agents.design.stages.spec import spec_stage
from agentsuite.kernel.base_agent import BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class DesignAgent(BaseAgent):
    """Concrete agent that produces design specification artifacts and asset briefs.

    Subclasses BaseAgent. Wires the 5 design stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "design"
    qa_rubric = DESIGN_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see DesignAgentInput-specific fields.
        """
        from agentsuite.agents.design.input_schema import DesignAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, DesignAgentInput):
                    state = state.model_copy(update={
                        "inputs": DesignAgentInput.model_validate(state.inputs.model_dump())
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
