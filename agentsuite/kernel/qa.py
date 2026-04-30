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
    ) -> QAReport:
        """Score the rubric against ``scores`` (dimension name → 0..10).

        Raises ``ValueError`` if ``scores`` contains unknown dimensions.
        Missing dimensions are assigned 0.0 and a revision instruction is
        appended so the run completes and the low score flags it for revision.
        """
        expected = {d.name for d in self.dimensions}
        provided = set(scores.keys())
        if provided - expected:
            raise ValueError(f"Unknown dimensions: {provided - expected}")
        missing = expected - provided
        scores = dict(scores)  # mutable copy — do not mutate the caller's dict
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
