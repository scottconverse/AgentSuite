"""QA rubric for the CIO Agent."""
from __future__ import annotations

from agentsuite.kernel.qa import QARubric, RubricDimension


CIO_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="strategic_alignment",
            question="Does the technology strategy explicitly connect to business objectives, with named initiatives mapped to measurable outcomes — not a generic 'IT supports the business' statement?",
        ),
        RubricDimension(
            name="technology_debt_awareness",
            question="Are technical debt obligations quantified and prioritized, with explicit remediation timelines, cost estimates, and risk exposure if left unaddressed?",
        ),
        RubricDimension(
            name="vendor_discipline",
            question="Are vendor relationships managed with defined SLAs, exit criteria, concentration risk limits, and regular performance reviews — rather than informal relationships with single-source dependencies?",
        ),
        RubricDimension(
            name="digital_readiness",
            question="Is the organization's digital maturity assessed against a recognized framework, with capability gaps identified and a concrete roadmap for closing them?",
        ),
        RubricDimension(
            name="governance_maturity",
            question="Are IT governance structures documented with clear decision rights, escalation paths, and accountability for technology investments — not ad-hoc decision-making?",
        ),
        RubricDimension(
            name="budget_realism",
            question="Does the technology budget reflect actual operational costs, debt remediation, and strategic investments — with variance tracking and a realistic forecast, not a wish list?",
        ),
        RubricDimension(
            name="workforce_capability",
            question="Is the technology workforce assessed for current skills gaps and future capability needs, with hiring, training, and retention plans that are funded and time-bound?",
        ),
        RubricDimension(
            name="risk_tolerance_clarity",
            question="Is the organization's technology risk appetite explicitly stated, with risk acceptance decisions documented, named owners assigned, and review dates set?",
        ),
        RubricDimension(
            name="innovation_balance",
            question="Is there a deliberate balance between run-the-business stability and innovation investment, with a portfolio view that tracks both operational reliability and emerging capability bets?",
        ),
    ],
    pass_threshold=7.0,
)
