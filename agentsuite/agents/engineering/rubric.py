"""QA rubric for the Engineering Agent."""
from __future__ import annotations

from agentsuite.kernel.qa import QARubric, RubricDimension


ENGINEERING_RUBRIC = QARubric(
    dimensions=[
        RubricDimension(
            name="implementation_specificity",
            question="Are implementation details specific enough for an engineer to act without asking follow-up questions? Penalize hand-wavy architecture.",
        ),
        RubricDimension(
            name="testability",
            question="Are components designed with testability in mind? Are test strategies and coverage expectations explicit?",
        ),
        RubricDimension(
            name="security_posture",
            question="Are security requirements explicitly addressed — authentication, authorization, data encryption, input validation, OWASP concerns?",
        ),
        RubricDimension(
            name="scalability_awareness",
            question="Does the design address the stated scale requirements? Are bottlenecks identified and mitigation strategies specified?",
        ),
        RubricDimension(
            name="dependency_hygiene",
            question="Are all external dependencies explicitly named, versioned, and justified? Are transitive risks acknowledged?",
        ),
        RubricDimension(
            name="anti_overengineering",
            question="Is the design appropriately simple for the stated scale? Penalize premature optimization and unnecessary abstraction layers.",
        ),
        RubricDimension(
            name="operational_completeness",
            question="Are deployment, monitoring, alerting, runbook, and incident response procedures explicitly documented?",
        ),
        RubricDimension(
            name="decision_traceability",
            question="Are architectural decisions documented with rationale and alternatives considered? Can future engineers understand WHY, not just WHAT?",
        ),
        RubricDimension(
            name="api_contract_clarity",
            question="Are API contracts (endpoints, request/response schemas, error codes, versioning strategy) explicit and complete?",
        ),
    ],
    pass_threshold=7.0,
)
