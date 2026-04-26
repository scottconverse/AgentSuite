"""QA rubric for the Design Agent."""
from __future__ import annotations

from agentsuite.kernel.qa import QARubric, RubricDimension


DESIGN_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="message_clarity",
            question="Does the brief make the value proposition unambiguous in one read?",
        ),
        RubricDimension(
            name="brand_fit",
            question="Does the output match extracted brand voice and visual identity?",
        ),
        RubricDimension(
            name="typography_hierarchy",
            question="Do type scale, weight, and line-height create a clear scan order?",
        ),
        RubricDimension(
            name="accessibility",
            question="Are color contrast, focus states, font size, and alt text all addressed?",
        ),
        RubricDimension(
            name="format_compliance",
            question="Does the output respect channel constraints (dimensions, file format, etc)?",
        ),
        RubricDimension(
            name="production_readiness",
            question="Can the asset be produced without further design rework?",
        ),
        RubricDimension(
            name="anti_genericity",
            question="Does this avoid clichés and SaaS-default treatments, reflecting strategic fit?",
        ),
    ],
    pass_threshold=7.0,
)
