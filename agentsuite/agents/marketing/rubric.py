"""QA rubric for the Marketing Agent."""
from __future__ import annotations

from agentsuite.kernel.qa import QARubric, RubricDimension


MARKETING_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="audience_clarity",
            question="Is the target audience defined with precision and specificity — demographics, psychographics, behaviors, and pain points — rather than broad generalities?",
        ),
        RubricDimension(
            name="message_resonance",
            question="Is the value proposition compelling, differentiated from competitors, and directly relevant to the target audience's needs and motivations?",
        ),
        RubricDimension(
            name="channel_fit",
            question="Does the channel mix match the audience's actual media behavior and the campaign goals? Are channel choices justified with rationale?",
        ),
        RubricDimension(
            name="metric_specificity",
            question="Are KPIs concrete, measurable, and directly tied to campaign goals? Do they include baselines, targets, and measurement methods?",
        ),
        RubricDimension(
            name="budget_realism",
            question="Are budget allocations realistic for the stated goals and channels? Are cost assumptions explicit and justified?",
        ),
        RubricDimension(
            name="anti_vanity_metrics",
            question="Does the plan avoid unmeasurable or vanity metrics (raw impressions, likes) without attribution? Are all metrics tied to business outcomes?",
        ),
        RubricDimension(
            name="content_depth",
            question="Does the content strategy have editorial substance — themes, formats, cadence, and creative direction — rather than generic content buckets?",
        ),
        RubricDimension(
            name="competitive_awareness",
            question="Does the plan reflect the competitive landscape and clearly differentiate the brand from key competitors in messaging and positioning?",
        ),
        RubricDimension(
            name="launch_sequencing",
            question="Are go-to-market activities ordered logically with dependencies identified? Is there a clear pre-launch, launch, and post-launch structure?",
        ),
    ],
    pass_threshold=7.0,
)
