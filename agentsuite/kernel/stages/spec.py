"""Kernel spec stage helper — shared orchestration for all agents' spec_stage.

Each agent's ``stages/spec.py`` becomes a thin wrapper that builds a
``SpecStageConfig`` with its agent-specific parameters and delegates here.

Agent-specific parts injected via config:
  - ``spec_artifacts``: ordered list of artifact stems
  - ``build_artifact_prompt_fn``: builds the per-artifact generation prompt
  - ``artifact_system_msg_fn``: returns the system message for each artifact call
  - ``build_consistency_prompt_fn``: builds the consistency-check prompt
  - ``consistency_system_msg``: system message for the consistency LLM call
  - ``artifact_snippet_truncate``: how many chars to include per artifact in the
    consistency-check prompt (typically 500; CIO uses 200)
  - ``snippet_key_fn``: how to key snippets in the consistency prompt dict

Path confinement
----------------
:func:`check_path_confinement` is the canonical helper for validating that a
user-supplied file path stays within the project directory.  Agent-level stages
that read ``manifest["sources"]`` entries or ``inp.founder_voice_samples`` must
call this before opening any path to prevent directory-traversal attacks.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from agentsuite.kernel.base_agent import StageContext
from agentsuite.kernel.schema import Cost, RunState
from agentsuite.llm.base import LLMRequest
from agentsuite.llm.json_extract import extract_json


def check_path_confinement(path: Path, project_dir: Path) -> None:
    """Raise ``ValueError`` if *path* resolves outside *project_dir*.

    Call this before reading any user-supplied file path (e.g. entries from
    ``manifest["sources"]`` or ``inp.founder_voice_samples``) to prevent
    directory-traversal attacks.

    Parameters
    ----------
    path:
        The user-supplied path to validate.
    project_dir:
        The root directory that all source files must live under.

    Raises
    ------
    ValueError
        With an actionable message when *path* resolves outside *project_dir*.
    """
    resolved = path.resolve()
    if not resolved.is_relative_to(project_dir.resolve()):
        raise ValueError(
            f"File path '{path}' is outside the project directory. "
            f"All source files must be within: {project_dir}"
        )


@dataclass
class SpecStageConfig:
    """All agent-specific parameters for the shared spec stage orchestration.

    Parameters
    ----------
    spec_artifacts:
        Ordered list of artifact stem names (no extension) to generate.
    build_artifact_prompt_fn:
        Callable ``(stem: str, extracted: dict, state: RunState) -> str``
        that returns the generation prompt for one artifact.
    artifact_system_msg_fn:
        Callable ``(stem: str) -> str`` that returns the system message for
        one artifact's LLM call.
    build_consistency_prompt_fn:
        Callable ``(artifact_snippets: dict[str, str], state: RunState) -> str``
        that returns the consistency-check prompt.
    consistency_system_msg:
        System message for the consistency-check LLM call.
    artifact_snippet_truncate:
        Number of chars to include per artifact in the consistency-check prompt.
        Default: 500.  CIO uses 200.
    snippet_key_fn:
        Callable ``(stem: str) -> str`` producing the key for each artifact in
        the snippets dict passed to ``build_consistency_prompt_fn``.
        Default: ``lambda stem: stem`` (bare stem, no extension).
    """

    spec_artifacts: list[str]
    build_artifact_prompt_fn: Callable[[str, dict[str, Any], RunState], str]
    artifact_system_msg_fn: Callable[[str], str]
    build_consistency_prompt_fn: Callable[[dict[str, str], RunState], str]
    consistency_system_msg: str
    artifact_snippet_truncate: int = 500
    snippet_key_fn: Callable[[str], str] | None = None


def kernel_spec_stage(config: SpecStageConfig, state: RunState, ctx: StageContext) -> RunState:
    """Shared spec stage orchestration kernel.

    Reads ``extracted_context.json``, calls the LLM once per artifact in
    ``config.spec_artifacts`` writing each as ``<stem>.md``, then runs a
    consistency-check LLM call, writes ``consistency_report.json``, and
    advances stage to ``"execute"``.

    Raises ``ValueError`` if the consistency-check response isn't valid JSON.
    """
    llm = ctx.edits["llm"]
    key_fn = config.snippet_key_fn if config.snippet_key_fn is not None else (lambda s: s)

    extracted: dict[str, Any] = json.loads(
        (ctx.writer.run_dir / "extracted_context.json").read_text(encoding="utf-8")
    )

    artifact_bodies: dict[str, str] = {}

    for stem in config.spec_artifacts:
        prompt = config.build_artifact_prompt_fn(stem, extracted, state)
        system = config.artifact_system_msg_fn(stem)
        response = llm.complete(LLMRequest(
            prompt=prompt,
            system=system,
            temperature=0.2,
        ))
        ctx.cost_tracker.add(Cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usd=response.usd,
            model=response.model,
        ))
        ctx.writer.write(f"{stem}.md", response.text, kind="spec", stage="spec")
        artifact_bodies[stem] = response.text

    artifact_snippets: dict[str, str] = {
        key_fn(stem): body[: config.artifact_snippet_truncate]
        for stem, body in artifact_bodies.items()
    }

    consistency_prompt = config.build_consistency_prompt_fn(artifact_snippets, state)
    consistency_response = llm.complete(LLMRequest(
        prompt=consistency_prompt,
        system=config.consistency_system_msg,
        temperature=0.0,
    ))
    ctx.cost_tracker.add(Cost(
        input_tokens=consistency_response.input_tokens,
        output_tokens=consistency_response.output_tokens,
        usd=consistency_response.usd,
        model=consistency_response.model,
    ))

    try:
        report = extract_json(consistency_response.text)
    except ValueError as exc:
        raise ValueError(f"consistency check produced invalid JSON: {exc}") from exc

    ctx.writer.write_json("consistency_report.json", report, kind="data", stage="spec")

    mismatches_raw = report.get("mismatches") if isinstance(report, dict) else None
    mismatches = mismatches_raw if isinstance(mismatches_raw, list) else []
    critical = [m for m in mismatches if isinstance(m, dict) and m.get("severity") == "critical"]
    return state.model_copy(update={
        "stage": "execute",
        "requires_revision": bool(critical),
    })
