"""Deterministic mock LLM provider for tests."""
from __future__ import annotations

from agentsuite.llm.base import LLMRequest, LLMResponse


class NoMockResponseConfigured(RuntimeError):
    """Raised when MockLLMProvider has no canned response matching the prompt."""


class MockLLMProvider:
    """Test stub that returns canned responses keyed by prompt substrings."""
    name = "mock"

    def __init__(
        self,
        responses: dict[str, str],
        *,
        default_model: str = "mock-1",
        name: str | None = None,
    ) -> None:
        self.responses = responses
        self._default_model = default_model
        self.calls: list[LLMRequest] = []
        if name is not None:
            self.name = name  # instance attr shadows class attr

    def default_model(self) -> str:
        return self._default_model

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        for keyword, text in self.responses.items():
            if keyword in request.prompt or keyword in request.system:
                return LLMResponse(
                    text=text,
                    model=request.model or self._default_model,
                    input_tokens=max(len(request.prompt.split()), 1),
                    output_tokens=max(len(text.split()), 1),
                    usd=0.0,
                )
        raise NoMockResponseConfigured(
            f"No canned response for prompt: {request.prompt[:80]!r}. "
            f"Configured keywords: {list(self.responses.keys())}"
        )


def _default_mock_for_cli(provider_name: str | None = None) -> "MockLLMProvider":
    """Default mock provider used by tests + CLI smoke-runs when no real provider is configured.

    ``provider_name`` lets a caller simulate any concrete provider's identity
    (anthropic / openai / gemini / ollama) on the returned mock — useful for
    tests that gate behavior on ``provider.name``.
    """
    import json as _json

    from agentsuite.agents.founder.rubric import FOUNDER_RUBRIC
    from agentsuite.agents.founder.stages.spec import SPEC_ARTIFACTS
    from agentsuite.agents.design.rubric import DESIGN_RUBRIC
    from agentsuite.agents.design.stages.spec import SPEC_ARTIFACTS as _DESIGN_SPEC_ARTIFACTS
    from agentsuite.agents.product.stages.spec import SPEC_ARTIFACTS as _PRODUCT_SPEC_ARTIFACTS
    from agentsuite.agents.engineering.rubric import ENGINEERING_RUBRIC
    from agentsuite.agents.engineering.stages.spec import SPEC_ARTIFACTS as _ENGINEERING_SPEC_ARTIFACTS
    from agentsuite.agents.marketing.stages.spec import SPEC_ARTIFACTS as _MARKETING_SPEC_ARTIFACTS
    from agentsuite.agents.trust_risk.rubric import TRUST_RISK_RUBRIC
    from agentsuite.agents.trust_risk.stages.spec import SPEC_ARTIFACTS as _TRUST_RISK_SPEC_ARTIFACTS

    extracted = {
        # Founder extract fields
        "mission": "x",
        "audience": {"primary_persona": "y", "secondary_personas": []},
        "positioning": "z",
        "tone_signals": ["practical"],
        "visual_signals": [],
        "recurring_claims": [],
        "recurring_vocabulary": [],
        "prohibited_language": [],
        "gaps": [],
        # Design extract fields (extra keys silently ignored by Founder parser)
        "audience_profile": {"primary_persona": "target user"},
        "brand_voice": {"tone_words": ["confident"], "writing_style": "terse", "forbidden_tones": []},
        "typography_signals": {"heading_style": "sans-serif"},
        "color_palette_observed": [],
        "craft_anti_patterns": [],
    }
    responses = {
        "extracting": _json.dumps(extracted),
        "checking 9 artifacts": _json.dumps({"mismatches": []}),
        "scoring 9 founder": _json.dumps({
            "scores": {d.name: 8.0 for d in FOUNDER_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
        "scoring 9 design-agent": _json.dumps({
            "scores": {d.name: 8.0 for d in DESIGN_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
        # Product pipeline responses
        "extracting structured product context": _json.dumps({
            "user_pain_points": ["Users spend too long on manual specification tasks"],
            "competitor_gaps": ["Competitor A lacks automated PRD generation"],
            "market_signals": ["Growing demand for AI-assisted product management"],
            "technical_constraints": ["Must integrate with existing issue trackers"],
            "assumed_non_goals": ["Mobile app", "Offline mode"],
            "open_questions": ["What is the target launch date?", "Who owns the roadmap?"],
        }),
        "checking 9 product-agent artifacts": _json.dumps({
            "checks": [
                {"dimension": "persona_consistency", "status": "ok", "severity": "ok", "detail": "Personas consistent across PRD and story map"},
                {"dimension": "feature_roadmap_alignment", "status": "ok", "severity": "ok", "detail": "Features in prioritization match roadmap"},
            ]
        }),
        "scoring 9 product-agent": _json.dumps({
            "scores": {
                "problem_clarity": 8.0,
                "user_grounding": 7.5,
                "scope_discipline": 8.0,
                "metric_specificity": 7.0,
                "feasibility_awareness": 8.0,
                "anti_feature_creep": 7.5,
                "acceptance_completeness": 8.0,
                "stakeholder_clarity": 7.0,
                "roadmap_sequencing": 8.0,
            },
            "revision_instructions": ["Clarify the success metrics timeframe"],
        }),
        # Engineering pipeline responses
        "extracting structured engineering context": _json.dumps({
            "existing_patterns": ["Repository pattern for data access", "Event-driven messaging via queues"],
            "known_bottlenecks": ["Database connection pool exhaustion under peak load"],
            "security_risks": ["Unvalidated input in public API endpoints"],
            "tech_debt_items": ["Legacy synchronous HTTP client blocking async event loop"],
            "integration_points": ["Payment gateway", "Identity provider (OIDC)"],
            "open_questions": ["What is the target SLA for batch jobs?", "Is multi-region deployment required?"],
        }),
        "checking 9 engineering-agent artifacts": _json.dumps({
            "consistent": True,
            "findings": [],
            "severity": "none",
        }),
        "scoring 9 engineering-agent": _json.dumps({
            "scores": {d.name: 8.0 for d in ENGINEERING_RUBRIC.dimensions},
            "revision_instructions": [],
        }),
        # Marketing pipeline responses
        "You are extracting structured marketing context from brand and competitor documents. Return ONLY valid JSON.": _json.dumps({
            "audience_insights": ["SMBs"],
            "competitor_gaps": ["pricing"],
            "brand_signals": ["innovative"],
            "channel_signals": ["email"],
            "budget_signals": ["$10k"],
            "open_questions": [],
        }),
        "You are checking 9 marketing-agent artifacts for consistency. Return ONLY JSON.": _json.dumps({
            "consistent": True,
            "findings": [],
            "severity": "none",
        }),
        "You are scoring 9 marketing-agent artifacts. Return ONLY JSON.": _json.dumps({
            "scores": {
                "audience_clarity": 8.0,
                "message_resonance": 8.0,
                "channel_fit": 8.0,
                "metric_specificity": 8.0,
                "budget_realism": 8.0,
                "anti_vanity_metrics": 8.0,
                "content_depth": 8.0,
                "competitive_awareness": 8.0,
                "launch_sequencing": 8.0,
            },
            "revision_instructions": [],
        }),
        # Trust/Risk pipeline responses
        "extracting structured trust and risk context": _json.dumps({
            "threat_indicators": ["SQL injection vectors in API endpoints", "Weak credential policies"],
            "control_gaps": ["No MFA enforced", "Unpatched third-party libraries"],
            "regulatory_signals": ["GDPR Article 32 applies", "SOC 2 CC6.1 relevant"],
            "incident_patterns": ["Phishing attempt Q1 2026", "Unauthorized access attempt Q4 2025"],
            "open_questions": ["Is penetration testing scheduled?", "Who owns vendor risk reviews?"],
        }),
        "You are checking 9 trust-risk-agent artifacts for consistency. Return ONLY JSON.": _json.dumps({
            "passed": True,
            "issues": [],
        }),
        "You are scoring 9 trust-risk-agent artifacts. Return ONLY JSON.": _json.dumps({
            "scores": {d.name: 8.0 for d in TRUST_RISK_RUBRIC.dimensions},
            "revision_instructions": {},
            "requires_revision": False,
        }),
    }
    for stem in SPEC_ARTIFACTS:
        responses[f"writing {stem}.md"] = f"# {stem}\nMocked content."
    for stem in _DESIGN_SPEC_ARTIFACTS:
        key = f"writing {stem}.md"
        if key not in responses:
            responses[key] = f"# {stem}\n\nContent."
    for stem in _PRODUCT_SPEC_ARTIFACTS:
        key = f"writing {stem}.md for a product manager"
        if key not in responses:
            responses[key] = f"# {stem.replace('-', ' ').title()}\n\nThis is the {stem} artifact for the product."
    for stem in _ENGINEERING_SPEC_ARTIFACTS:
        key = f"writing {stem}.md for an engineering team"
        if key not in responses:
            responses[key] = f"# {stem}\n\nMock engineering content."
    for stem in _MARKETING_SPEC_ARTIFACTS:
        key = f"writing {stem}.md for a marketing team"
        if key not in responses:
            responses[key] = f"# {stem.replace('-', ' ').title()}\n\nMock marketing content."
    for stem in _TRUST_RISK_SPEC_ARTIFACTS:
        key = f"writing {stem}.md for a trust and risk team"
        if key not in responses:
            responses[key] = f"# {stem.replace('-', ' ').title()}\n\nMock trust/risk content."
    return MockLLMProvider(responses=responses, name=provider_name or "mock")
