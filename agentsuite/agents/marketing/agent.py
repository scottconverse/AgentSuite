"""MarketingAgent — wires the kernel BaseAgent to marketing stage handlers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentsuite.agents.marketing.rubric import MARKETING_RUBRIC
from agentsuite.agents.marketing.stages.execute import execute_stage
from agentsuite.agents.marketing.stages.extract import extract_stage
from agentsuite.agents.marketing.stages.intake import intake_stage
from agentsuite.agents.marketing.stages.qa import qa_stage
from agentsuite.agents.marketing.stages.spec import spec_stage
from agentsuite.kernel.base_agent import BaseAgent, StageContext, StageHandler
from agentsuite.kernel.schema import RunState


class MarketingAgent(BaseAgent):
    """Concrete agent that produces marketing campaign artifacts.

    Subclasses BaseAgent. Wires the 5 marketing stage handlers into the kernel
    pipeline driver. Holds an LLMProvider on the instance; injects it into the
    StageContext.edits dict before each handler runs.
    """

    name = "marketing"
    qa_rubric = MARKETING_RUBRIC

    def __init__(self, output_root: Path, llm: Any | None = None) -> None:
        super().__init__(output_root=output_root)
        if llm is None:
            from agentsuite.llm.resolver import resolve_provider
            llm = resolve_provider()
        self.llm = llm

    def stage_handlers(self) -> dict[str, StageHandler]:
        """Return the 5 stage handlers wrapped to inject LLM and re-validate inputs.

        After JSON round-trip on resume, state.inputs may be a bare AgentRequest.
        Re-validate so handlers see MarketingAgentInput-specific fields.
        """
        from agentsuite.agents.marketing.input_schema import MarketingAgentInput

        def _wrap(handler: StageHandler) -> StageHandler:
            def runner(state: RunState, ctx: StageContext) -> RunState:
                ctx.edits.setdefault("llm", self.llm)
                if not isinstance(state.inputs, MarketingAgentInput):
                    # On resume, the caller may supply the original typed input
                    # via edits["inputs"] because RunState serialises inputs as
                    # the base AgentRequest, dropping subclass-only fields such
                    # as brand_name.  Prefer the edits value when present.
                    typed_inputs = ctx.edits.get("inputs")
                    if isinstance(typed_inputs, MarketingAgentInput):
                        state = state.model_copy(update={"inputs": typed_inputs})
                    else:
                        state = state.model_copy(update={
                            "inputs": MarketingAgentInput.model_validate(state.inputs.model_dump())
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
