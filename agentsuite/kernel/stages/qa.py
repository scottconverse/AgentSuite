"""Kernel QA stage helper — shared orchestration for all agents' qa_stage.

Each agent's ``stages/qa.py`` becomes a thin wrapper that builds a
``QAStageConfig`` with its agent-specific parameters and delegates here.

Agent-specific parts injected via config:
  - ``build_prompt_fn``: builds the qa_score prompt from artifact bodies + state
  - ``system_msg``: the LLM system message (e.g. "scoring 9 founder-agent artifacts")
  - ``rubric``: the agent's QARubric instance
  - ``write_qa_report``: whether to write ``qa_report.md`` (CIO skips this)
  - ``artifact_key_fn``: how to key artifact bodies (most agents use ``f"{stem}.md"``;
    CIO uses ``stem`` without the extension)
  - ``artifact_truncate``: if set, truncate artifact content to this many chars
    before including in the prompt (CIO uses 500; others pass ``None`` for full)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.qa import QARubric
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMRequest
from agentsuite.llm.json_extract import extract_json


@dataclass
class QAStageConfig:
    """All agent-specific parameters for the shared QA stage orchestration.

    Parameters
    ----------
    rubric:
        The agent's QARubric instance used to score dimension scores and
        determine pass/fail.
    build_prompt_fn:
        Callable ``(artifact_bodies: dict[str, str], state: RunState) -> str``
        that constructs the qa_score prompt using agent-specific template vars
        and the agent's own ``render_prompt``.
    system_msg:
        System message sent to the LLM (e.g. "scoring 9 founder-agent artifacts").
    write_qa_report:
        If ``True`` (default), write ``qa_report.md`` from ``report.to_markdown()``.
        The CIO agent sets this to ``False`` (it writes only ``qa_scores.json``).
    artifact_key_fn:
        Callable ``(stem: str) -> str`` that produces the key for each artifact
        in the dict passed to ``build_prompt_fn``.  Default: ``f"{stem}.md"``.
        CIO passes ``lambda stem: stem`` (no extension).
    artifact_truncate:
        If set, truncate each artifact's content to this many characters before
        including it in the prompt.  ``None`` (default) = full content.
    spec_artifacts:
        The agent's ``SPEC_ARTIFACTS`` list — stems of files to read from the
        run directory.
    """

    rubric: QARubric
    build_prompt_fn: Callable[[dict[str, str], RunState], str]
    system_msg: str
    spec_artifacts: list[str]
    write_qa_report: bool = True
    artifact_key_fn: Callable[[str], str] | None = None
    artifact_truncate: int | None = None


def kernel_qa_stage(config: QAStageConfig, state: RunState, ctx: StageContext) -> RunState:
    """Shared QA stage orchestration kernel.

    Reads spec artifacts from disk, calls the LLM to score rubric dimensions,
    parses the response, runs it through the rubric, optionally writes
    ``qa_report.md``, always writes ``qa_scores.json``, and advances stage
    to ``"approval"``.

    Raises ``ValueError`` if the LLM response isn't valid JSON.
    """
    llm = ctx.edits["llm"]
    key_fn = config.artifact_key_fn if config.artifact_key_fn is not None else (lambda s: f"{s}.md")

    artifact_bodies: dict[str, str] = {}
    for stem in config.spec_artifacts:
        path = ctx.writer.run_dir / f"{stem}.md"
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if config.artifact_truncate is not None:
                content = content[: config.artifact_truncate]
            artifact_bodies[key_fn(stem)] = content

    prompt = config.build_prompt_fn(artifact_bodies, state)
    response = llm.complete(LLMRequest(
        prompt=prompt,
        system=config.system_msg,
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        usd=response.usd,
        model=response.model,
    ))

    try:
        parsed = extract_json(response.text)
    except ValueError as exc:
        raise ValueError(f"qa stage produced invalid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        parsed = {}
    raw_scores = parsed.get("scores")
    if not isinstance(raw_scores, dict):
        raw_scores = {}
    raw_revisions = parsed.get("revision_instructions")
    if not isinstance(raw_revisions, list):
        raw_revisions = []

    report = config.rubric.score(scores=raw_scores, revision_instructions=raw_revisions)

    if config.write_qa_report:
        ctx.writer.write("qa_report.md", report.to_markdown(), kind="qa_report", stage="qa")
    ctx.writer.write_json("qa_scores.json", report.model_dump(), kind="data", stage="qa")

    return state.model_copy(update={
        "stage": "approval",
        "requires_revision": report.requires_revision,
    })
