"""Founder agent QA rubric."""
from agentsuite.kernel.qa import QARubric, RubricDimension


FOUNDER_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="reusability",
            question="Can this system be reused next week without restating context?",
        ),
        RubricDimension(
            name="brand_consistency",
            question="Are tone and visual signals consistent across all artifacts?",
        ),
        RubricDimension(
            name="claims_grounded",
            question="Is every claim traceable to source material or marked SPECULATIVE?",
        ),
        RubricDimension(
            name="voice_fit",
            question="Does founder-voice-guide match the supplied voice samples?",
        ),
        RubricDimension(
            name="template_specificity",
            question="Are brief templates concrete enough to produce controlled outputs?",
        ),
        RubricDimension(
            name="goal_alignment",
            question="Are artifacts mapped to the stated business_goal?",
        ),
        RubricDimension(
            name="anti_genericity",
            question="Does this avoid generic SaaS landing-page voice and clichés?",
        ),
        RubricDimension(
            name="constraint_adherence",
            question="Proposed strategy respects stated budget, timeline, and resource constraints without magical thinking?",
        ),
        RubricDimension(
            name="completeness",
            question="All required specification artifacts are populated with substantive, non-placeholder content?",
        ),
    ],
    pass_threshold=7.0,
)
