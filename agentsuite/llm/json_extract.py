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
    # Fallback: forward-scan for the first valid JSON object or array.
    # Uses raw_decode so it correctly handles nesting and ignores curly braces
    # in prose that appear before the real JSON object.
    decoder = json.JSONDecoder()
    for pos, ch in enumerate(stripped):
        if ch not in ("{", "["):
            continue
        try:
            value, _ = decoder.raw_decode(stripped, pos)
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError(
        f"LLM response is not valid JSON even after stripping fences/prose. "
        f"First 200 chars: {text[:200]!r}"
    )
