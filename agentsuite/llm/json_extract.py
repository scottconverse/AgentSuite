"""Robust JSON extraction from LLM responses that may include markdown fences."""
from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Parse JSON from LLM response text, stripping markdown code fences if present.

    Handles:
    - Pure JSON strings
    - Responses wrapped in ```json...``` or ```...``` fences
    - Responses with a leading one-line preamble before the JSON object/array

    Raises ``ValueError`` with a descriptive message if the text cannot be parsed
    as JSON after all stripping attempts.
    """
    stripped = text.strip()
    # Remove outermost markdown code fences: ```json...``` or ```...```
    fence = re.match(r"^```(?:\w+)?\s*\n?(.*?)\n?```\s*$", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1).strip()
    # Fast path: direct parse (common case — clean JSON or already cleaned by fence strip)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    # Fallback: extract first JSON object or array from text (handles leading prose)
    for start_char, end_char in (("{", "}"), ("[", "]")):
        start_idx = stripped.find(start_char)
        if start_idx >= 0:
            end_idx = stripped.rfind(end_char)
            if end_idx > start_idx:
                try:
                    return json.loads(stripped[start_idx:end_idx + 1])
                except json.JSONDecodeError:
                    pass
    raise ValueError(
        f"LLM response is not valid JSON even after stripping fences/prose. "
        f"First 200 chars: {text[:200]!r}"
    )
