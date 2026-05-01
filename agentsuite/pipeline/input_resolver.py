"""Maps common pipeline inputs to per-agent input schema kwargs."""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

_INPUT_CLASSES: dict[str, str] = {
    "founder":     "agentsuite.agents.founder.input_schema:FounderAgentInput",
    "design":      "agentsuite.agents.design.input_schema:DesignAgentInput",
    "product":     "agentsuite.agents.product.input_schema:ProductAgentInput",
    "engineering": "agentsuite.agents.engineering.input_schema:EngineeringAgentInput",
    "marketing":   "agentsuite.agents.marketing.input_schema:MarketingAgentInput",
    "trust_risk":  "agentsuite.agents.trust_risk.input_schema:TrustRiskAgentInput",
    "cio":         "agentsuite.agents.cio.input_schema:CIOAgentInput",
}

# Fields each agent requires beyond the common pipeline inputs.
_AGENT_REQUIRED_EXTRAS: dict[str, list[str]] = {
    "engineering": ["tech_stack", "scale_requirements"],
    "trust_risk":  ["risk_domain", "stakeholder_context"],
    "cio":         ["it_maturity_level"],
}

_EXAMPLE_EXTRAS: dict[str, str] = {
    "engineering": (
        '{"engineering": {"tech_stack": "Python + FastAPI", '
        '"scale_requirements": "1k RPM, 99.9% uptime"}}'
    ),
    "trust_risk": (
        '{"trust_risk": {"risk_domain": "SaaS application", '
        '"stakeholder_context": "enterprise customers with high compliance requirements"}}'
    ),
    "cio": (
        '{"cio": {"it_maturity_level": "Level 2 - Repeatable", '
        '"strategic_priorities": "cloud-first, cost reduction"}}'
    ),
}


def get_input_class(agent_name: str) -> type:
    """Return the AgentRequest subclass for *agent_name*."""
    ref = _INPUT_CLASSES.get(agent_name)
    if ref is None:
        raise ValueError(f"Unknown agent: {agent_name!r}")
    module_path, class_name = ref.split(":")
    return cast(type, getattr(importlib.import_module(module_path), class_name))


def resolve_agent_input(
    agent_name: str,
    *,
    business_goal: str,
    project_slug: str,
    inputs_dir: Path | None,
    agent_extras: dict[str, Any],
) -> dict[str, Any]:
    """Return a kwargs dict suitable for the agent's input class constructor.

    Raises ValueError with a clear message if required extras are missing.
    """
    required = _AGENT_REQUIRED_EXTRAS.get(agent_name, [])
    missing = [f for f in required if f not in agent_extras]
    if missing:
        example = _EXAMPLE_EXTRAS.get(agent_name, "")
        raise ValueError(
            f"Agent {agent_name!r} requires {missing} in --agent-inputs.\n"
            f"Example: {example}"
        )

    base: dict[str, Any] = {
        "agent_name": agent_name,
        "role_domain": agent_name.replace("_", "-") + "-ops",
        "user_request": f"Pipeline run for {project_slug}: {business_goal}",
        "business_goal": business_goal,
        "project_slug": project_slug,
    }
    if inputs_dir is not None:
        base["inputs_dir"] = inputs_dir

    if agent_name == "founder":
        return {**base, **agent_extras}

    if agent_name == "design":
        return {
            **base,
            "target_audience": agent_extras.get("target_audience", business_goal),
            "campaign_goal": agent_extras.get("campaign_goal", business_goal),
            **{k: v for k, v in agent_extras.items()
               if k not in ("target_audience", "campaign_goal")},
        }

    if agent_name == "product":
        return {
            **base,
            "product_name": agent_extras.get("product_name", project_slug),
            "target_users": agent_extras.get("target_users", business_goal),
            "core_problem": agent_extras.get("core_problem", business_goal),
            **{k: v for k, v in agent_extras.items()
               if k not in ("product_name", "target_users", "core_problem")},
        }

    if agent_name == "marketing":
        return {
            **base,
            "brand_name": agent_extras.get("brand_name", project_slug),
            "campaign_goal": agent_extras.get("campaign_goal", business_goal),
            "target_market": agent_extras.get("target_market", business_goal),
            **{k: v for k, v in agent_extras.items()
               if k not in ("brand_name", "campaign_goal", "target_market")},
        }

    if agent_name == "engineering":
        return {
            **base,
            "system_name": agent_extras.get("system_name", project_slug),
            "problem_domain": agent_extras.get("problem_domain", business_goal),
            "tech_stack": agent_extras["tech_stack"],
            "scale_requirements": agent_extras["scale_requirements"],
            **{k: v for k, v in agent_extras.items()
               if k not in ("system_name", "problem_domain", "tech_stack", "scale_requirements")},
        }

    if agent_name == "trust_risk":
        return {
            **base,
            "product_name": agent_extras.get("product_name", project_slug),
            "risk_domain": agent_extras["risk_domain"],
            "stakeholder_context": agent_extras["stakeholder_context"],
            **{k: v for k, v in agent_extras.items()
               if k not in ("product_name", "risk_domain", "stakeholder_context")},
        }

    if agent_name == "cio":
        return {
            **base,
            "organization_name": agent_extras.get("organization_name", project_slug),
            "strategic_priorities": agent_extras.get("strategic_priorities", business_goal),
            "it_maturity_level": agent_extras["it_maturity_level"],
            **{k: v for k, v in agent_extras.items()
               if k not in ("organization_name", "strategic_priorities", "it_maturity_level")},
        }

    raise ValueError(f"Unknown agent: {agent_name!r}")
