"""QA rubric for the Design Agent."""
from __future__ import annotations

from agentsuite.kernel.qa import QARubric, RubricDimension


DESIGN_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="spec_completeness",
            question="Are all required sections present and substantively filled? No placeholder text, no TBD sections.",
        ),
        RubricDimension(
            name="brand_fidelity",
            question="Do visual choices faithfully reflect the extracted brand system? Are colors, typography, and voice consistent?",
        ),
        RubricDimension(
            name="audience_fit",
            question="Does the creative direction speak to the target audience's actual visual sophistication and preferences?",
        ),
        RubricDimension(
            name="craft_specificity",
            question="Are directions specific enough for a designer to execute without asking follow-up questions?",
        ),
        RubricDimension(
            name="accessibility_rigor",
            question="Are WCAG AA requirements explicitly addressed in the QA and audit documents?",
        ),
        RubricDimension(
            name="anti_genericity",
            question="Are generic design clichés absent? Penalize 'clean and modern', 'bold and beautiful', 'minimalist yet impactful'.",
        ),
        RubricDimension(
            name="revision_actionability",
            question="Are revision instructions and QA findings specific, numbered, and executable without interpretation?",
        ),
        RubricDimension(
            name="consistency",
            question="Do typography hierarchy, color palette, and audience description match across all artifacts?",
        ),
        RubricDimension(
            name="image_prompt_precision",
            question="Does the image generation prompt specify layout, hierarchy, and technical parameters — not just mood?",
        ),
    ],
    pass_threshold=7.0,
)
