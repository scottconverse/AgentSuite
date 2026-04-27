"""QA rubric for the Trust/Risk Agent."""
from __future__ import annotations

from agentsuite.kernel.qa import QARubric, RubricDimension


TRUST_RISK_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="threat_coverage",
            question="Does the assessment comprehensively identify threats across all relevant attack surfaces — network, application, identity, physical, and supply chain — rather than focusing on a narrow subset?",
        ),
        RubricDimension(
            name="control_specificity",
            question="Are security controls concrete and implementable with specific technologies, configurations, and owners named — not vague policy statements like 'enforce least privilege'?",
        ),
        RubricDimension(
            name="risk_quantification",
            question="Do risks have explicit likelihood and impact scores or a clear prioritization rationale? Are high-priority risks distinguishable from low-priority ones by more than intuition?",
        ),
        RubricDimension(
            name="regulatory_alignment",
            question="Do the artifacts explicitly address applicable regulatory and compliance requirements, mapping controls to specific framework clauses or regulatory citations?",
        ),
        RubricDimension(
            name="incident_readiness",
            question="Are incident response procedures actionable with defined roles, escalation paths, communication templates, and evidence-preservation steps — and have they been tested or tabletop-exercised?",
        ),
        RubricDimension(
            name="zero_trust_posture",
            question="Are least-privilege and zero-trust principles applied throughout — with explicit verification steps, micro-segmentation, and no implicit trust granted based on network location or identity alone?",
        ),
        RubricDimension(
            name="vendor_risk_awareness",
            question="Are third-party and supply chain risks explicitly identified, with vendor assessment criteria, contractual obligations, and monitoring processes defined?",
        ),
        RubricDimension(
            name="audit_traceability",
            question="Are security decisions and controls traceable to specific requirements, evidence, or threat scenarios? Can an auditor follow the chain from threat to control to validation?",
        ),
        RubricDimension(
            name="residual_risk_acceptance",
            question="Are remaining risks after controls explicitly acknowledged, with named risk owners, documented acceptance rationale, and planned review dates?",
        ),
    ],
    pass_threshold=7.0,
)
