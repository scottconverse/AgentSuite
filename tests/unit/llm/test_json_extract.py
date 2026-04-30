"""Unit tests for agentsuite.llm.json_extract.extract_json."""
import pytest

from agentsuite.llm.json_extract import extract_json


def test_pure_json_object():
    result = extract_json('{"key": "value", "n": 42}')
    assert result == {"key": "value", "n": 42}


def test_pure_json_array():
    result = extract_json('[1, 2, 3]')
    assert result == [1, 2, 3]


def test_fenced_json_with_lang_tag():
    result = extract_json('```json\n{"key": "val"}\n```')
    assert result == {"key": "val"}


def test_fenced_json_without_lang_tag():
    result = extract_json('```\n{"key": "val"}\n```')
    assert result == {"key": "val"}


def test_fenced_json_with_leading_prose():
    result = extract_json('Here is the JSON:\n```json\n{"key": "val"}\n```')
    # Fence regex won't match because of leading prose; fallback to JSON extraction
    assert result == {"key": "val"}


def test_leading_prose_no_fences():
    result = extract_json('Here is the extracted context:\n{"key": "val"}')
    assert result == {"key": "val"}


def test_whitespace_padded():
    result = extract_json('  \n  {"key": "val"}  \n  ')
    assert result == {"key": "val"}


def test_nested_json_object():
    data = '{"outer": {"inner": [1, 2, 3]}, "flag": true}'
    result = extract_json(data)
    assert result["outer"]["inner"] == [1, 2, 3]


def test_malformed_raises_value_error():
    with pytest.raises(ValueError, match="not valid JSON"):
        extract_json("this is not json at all")


def test_empty_string_raises_value_error():
    with pytest.raises(ValueError, match="not valid JSON"):
        extract_json("")
