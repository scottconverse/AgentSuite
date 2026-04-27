"""QA rubric for the Product Agent."""
from __future__ import annotations

from agentsuite.kernel.qa import QARubric, RubricDimension


PRODUCT_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="problem_clarity",
            question="Is the user problem specific, observable, and tied to real evidence? Penalize vague problem statements.",
        ),
        RubricDimension(
            name="user_grounding",
            question="Are solutions grounded in explicit user needs, not assumptions? Are personas backed by research signals?",
        ),
        RubricDimension(
            name="scope_discipline",
            question="Is scope explicitly bounded? Are nice-to-haves excluded from MVP? Is what is NOT in scope stated?",
        ),
        RubricDimension(
            name="metric_specificity",
            question="Are success metrics measurable, time-bound, and traceable to the core problem?",
        ),
        RubricDimension(
            name="feasibility_awareness",
            question="Does the spec acknowledge technical constraints and flag high-risk assumptions?",
        ),
        RubricDimension(
            name="anti_feature_creep",
            question="Are requirements lean and intentional? Penalize over-specified nice-to-haves and premature optimizations.",
        ),
        RubricDimension(
            name="acceptance_completeness",
            question="Are acceptance criteria testable, unambiguous, and written from the user's perspective?",
        ),
        RubricDimension(
            name="stakeholder_clarity",
            question="Are decision-makers, approvers, and affected teams explicitly named?",
        ),
        RubricDimension(
            name="roadmap_sequencing",
            question="Is the roadmap sequenced logically with stated rationale for ordering?",
        ),
    ],
    pass_threshold=7.0,
)
