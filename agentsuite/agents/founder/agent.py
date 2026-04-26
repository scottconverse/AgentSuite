"""FounderAgent — wires the kernel BaseAgent to founder stage handlers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
from agentsuite.agents.founder.stages.execute import execute_stage
from agentsuite.agents.founder.stages.extract import extract_stage
from agentsuite.agents.founder.stages.intake import intake_stage
from agentsuite.agents.founder.stages.qa import qa_stage
from agentsuite.agents.founder.stages.spec import spec_stage
from agentsuite.kernel.base_agent import BaseAgent, StageHandler
from agentsuite.kernel.schema import RunState


class FounderAgent(BaseAgent):
    """Concrete agent that builds reusable creative-ops artifacts for founders.

    Subclasses BaseAgent. Wires the 5 founder stage handlers into the kernel's
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "founder"
    qa_rubric = FOUNDER_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider

            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-cast inputs.

        After JSON round-trip on resume, state.inputs may be an AgentRequest instance
        lacking FounderAgentInput-specific fields. Re-validate from its dump so handlers
        see the correct shape.
        """
        from agentsuite.agents.founder.input_schema import FounderAgentInput

        def _wrap(handler):  # type: ignore[no-untyped-def]
            def runner(state: RunState, ctx) -> RunState:  # type: ignore[no-untyped-def]
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, FounderAgentInput):
                    state = state.model_copy(update={
                        "inputs": FounderAgentInput.model_validate(state.inputs.model_dump())
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
