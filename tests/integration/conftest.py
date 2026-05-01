"""Integration test fixtures.

Note: vcr.py cassette infrastructure was scaffolded in v0.1 but never used — all
integration tests run against MockLLMProvider directly. The cassette fixture and
RECORD_CASSETTES guard are removed as part of TEST-005 dead-code cleanup (v1.0.8+).
The empty ``cassettes/`` directory is intentionally retained as a placeholder for
a potential future real-provider integration path.
"""
from pathlib import Path

CASSETTE_DIR = Path(__file__).parent / "cassettes"
