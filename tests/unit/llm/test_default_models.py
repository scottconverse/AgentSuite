"""ENG-003: Each provider's ``default_model()`` must hit the pricing table.

If the default model id falls back to fallback rates, every first-time user
gets a "[ENG-002] cost lookup miss" warning AND silently inaccurate cost
numbers. The defaults are part of the public contract; they must be in the
canonical pricing entries.
"""
from __future__ import annotations

import pytest

from agentsuite.llm.anthropic import AnthropicProvider
from agentsuite.llm.gemini import GeminiProvider
from agentsuite.llm.openai import OpenAIProvider
from agentsuite.llm.pricing import lookup_pricing


def _provider_with_no_sdk(cls, sdk_name):
    """Instantiate the provider without an SDK so default_model() can be called
    without network or credentials. Each provider raises ProviderNotInstalled
    only when it tries to use the real SDK; constructing with a stub client
    bypasses that path."""
    return cls(client=object())


@pytest.mark.parametrize("provider_name,cls", [
    ("anthropic", AnthropicProvider),
    ("openai", OpenAIProvider),
    ("gemini", GeminiProvider),
])
def test_default_model_is_in_pricing_table(provider_name: str, cls) -> None:
    instance = _provider_with_no_sdk(cls, provider_name)
    default = instance.default_model()
    rates, provenance = lookup_pricing(provider_name, default)
    assert provenance == "exact", (
        provider_name + " default_model " + repr(default) + " is not in the "
        "pricing table; first-time users will trigger the ENG-002 fallback "
        "warning on every call. Add it to agentsuite/llm/pricing.py or "
        "change the default to a model that is in the table."
    )
    assert rates["in"] > 0 and rates["out"] > 0
