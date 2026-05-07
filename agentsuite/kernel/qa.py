"""Rubric-based QA scoring framework."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RubricDimension(BaseModel):
    """A single scored dimension within a QA rubric."""
    model_config = ConfigDict(extra="forbid")

    name: str
    question: str
    weight: float = 1.0


class QAReport(BaseModel):
    """Outcome of running a rubric against a set of scores."""
    model_config = ConfigDict(extra="forbid")

    scores: dict[str, float]
    average: float
    passed: bool
    revision_instructions: list[str] = Field(default_factory=list)
    requires_revision: bool = False

    def to_markdown(self) -> str:
        """Render the report as a human-readable markdown document."""
        lines = [
            "# QA Report",
            "",
            f"Average score: {self.average:.2f}",
            f"Passed: {self.passed}",
            "",
            "| Dimension | Score |",
            "|---|---|",
        ]
        for name, score in self.scores.items():
            lines.append(f"| {name} | {score:.2f} |")
        if self.revision_instructions:
            lines.extend(["", "## Revision instructions", ""])
            for r in self.revision_instructions:
                lines.append(f"- {r}")
        return "\n".join(lines) + "\n"


class QARubric(BaseModel):
    """A weighted rubric used to score one or more agent artifacts."""
    model_config = ConfigDict(extra="forbid")

    dimensions: list[RubricDimension]
    pass_threshold: float = 7.0

    def score(
        self,
        scores: dict[str, float],
        *,
        revision_instructions: list[str],
        strict_dimensions: bool = True,
    ) -> QAReport:
        """Score the rubric against ``scores`` (dimension name → 0..10).

        ``strict_dimensions`` (default ``True``) preserves the original
        contract: unknown dimensions raise ``ValueError``. Set this to
        ``False`` when the score dict comes from an LLM (which may invent
        non-canonical dimensions like ``"clarity"`` or ``"actionability"``);
        unknown dimensions are then dropped, a revision instruction is
        appended, and the run completes with the recognized dimensions only.

        Missing dimensions are always assigned 0.0 with a revision instruction
        appended so the run completes and the low score flags it for revision.
        """
        expected = {d.name for d in self.dimensions}
        provided = set(scores.keys())
        extra = provided - expected
        if extra:
            if strict_dimensions:
                raise ValueError(f"Unknown dimensions: {extra}")
            # Soft mode: drop unknown dimensions, leave a trail in the report.
            # AgentSuiteLocal v0.9 sprint-2-punchlist Variant 2: real LLMs
            # (gemma4:e4b observed) produce dimension names like 'clarity' or
            # 'actionability' that aren't in the agent's canonical rubric.
            # Erroring on this puts the entire run into status="error" and
            # leaves the user with no path forward; soft-skipping degrades to
            # qa_score=None at the consumer (handled by the approval gate UX).
            scores = {k: v for k, v in scores.items() if k not in extra}
            revision_instructions = list(revision_instructions) + [
                f"QA output contained dimensions not in the rubric "
                f"({sorted(extra)}); they were dropped. Canonical rubric "
                f"dimensions: {sorted(expected)}."
            ]
        missing = expected - provided
        scores = dict(scores)  # mutable copy — do not mutate the caller's dict
        # Coerce score values to float: real LLMs may return strings or nulls.
        coerced: dict[str, float] = {}
        for k, v in scores.items():
            try:
                coerced[k] = float(v) if v is not None else 0.0
            except (TypeError, ValueError):
                coerced[k] = 0.0
        scores = coerced
        revision_instructions = list(revision_instructions)  # copy before appending
        if missing:
            for dim in missing:
                scores[dim] = 0.0
            revision_instructions.append(
                f"QA scoring incomplete: LLM did not score {sorted(missing)}."
                " Assigned 0.0 — re-run QA or review manually."
            )
        weights = {d.name: d.weight for d in self.dimensions}
        weighted = sum(scores[d.name] * weights[d.name] for d in self.dimensions)
        total_weight = sum(weights.values())
        average = weighted / total_weight
        passed = average >= self.pass_threshold
        return QAReport(
            scores=scores,
            average=average,
            passed=passed,
            revision_instructions=revision_instructions,
            requires_revision=not passed,
        )
