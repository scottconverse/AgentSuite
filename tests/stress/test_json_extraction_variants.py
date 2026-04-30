"""Stress tests for extract_json() — format variants that real LLMs produce."""
from __future__ import annotations

import pytest

from agentsuite.llm.json_extract import extract_json


@pytest.mark.parametrize("text,expected", [
    # Pure JSON — objects and arrays
    ('{"k": "v"}', {"k": "v"}),
    ('[1, 2, 3]', [1, 2, 3]),
    ('{}', {}),
    ('[]', []),
    # Markdown fences with various lang tags
    ('```json\n{"k": "v"}\n```', {"k": "v"}),
    ('```\n{"k": "v"}\n```', {"k": "v"}),
    ('```JSON\n{"k": "v"}\n```', {"k": "v"}),
    ('```json\n[1, 2]\n```', [1, 2]),
    # Leading prose (preamble before JSON)
    ('Here is the result:\n{"k": "v"}', {"k": "v"}),
    ('Sure! Here\'s the JSON output:\n{"k": "v"}', {"k": "v"}),
    ('I\'ve analyzed the artifacts. Result:\n{"mismatches": []}', {"mismatches": []}),
    # Trailing prose (postamble after JSON)
    ('{"k": "v"}\n\nLet me know if you need more!', {"k": "v"}),
    ('{"k": "v"}\nHappy to help further.', {"k": "v"}),
    # Fenced AND trailing prose
    ('```json\n{"k": "v"}\n```\nHappy to help!', {"k": "v"}),
    ('```json\n{"k": "v"}\n```\n\nLet me know if you need anything else.', {"k": "v"}),
    # Whitespace variations
    ('  \n  {"k": "v"}  \n  ', {"k": "v"}),
    ('\t{"k": "v"}\t', {"k": "v"}),
    # Consistency check shapes — the exact shapes spec stage parses
    ('{"mismatches": []}', {"mismatches": []}),
    ('```json\n{"mismatches": []}\n```', {"mismatches": []}),
    ('{"mismatches": [{"dimension": "tone", "severity": "critical", "detail": "x"}]}',
     {"mismatches": [{"dimension": "tone", "severity": "critical", "detail": "x"}]}),
    # QA score shapes — the exact shapes qa stage parses
    ('{"scores": {"dim": 8.0}, "revision_instructions": []}',
     {"scores": {"dim": 8.0}, "revision_instructions": []}),
    ('```json\n{"scores": {"dim": 8.0}, "revision_instructions": []}\n```',
     {"scores": {"dim": 8.0}, "revision_instructions": []}),
    # Nested JSON
    ('{"a": {"b": {"c": 1}}}', {"a": {"b": {"c": 1}}}),
    # Numbers, booleans, null at various positions
    ('{"score": 8.0, "passed": true, "label": null}',
     {"score": 8.0, "passed": True, "label": None}),
])
def test_extract_json_accepts(text: str, expected: object) -> None:
    assert extract_json(text) == expected


@pytest.mark.parametrize("text", [
    # Empty or whitespace-only
    "",
    "   ",
    "\n\n\n",
    "\t\t",
    # Refusal / non-JSON text
    "I cannot help with that.",
    "Here is your answer:\n\nSorry, I cannot assist.",
    "As an AI language model, I must decline.",
    # Truncated / malformed JSON
    '{"key": "value"',
    '{"key": }',
    '{"key": "value", }',
    '{key: "value"}',
    # Code fence with non-JSON content
    "```json\nnot valid json\n```",
    "```\nnot valid json\n```",
    # Entirely unrelated content
    "not json at all @@@@",
    "SELECT * FROM users;",
])
def test_extract_json_raises_on_unparseable(text: str) -> None:
    with pytest.raises(ValueError):
        extract_json(text)
