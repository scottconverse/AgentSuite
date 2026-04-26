"""Integration test fixtures — vcr.py cassette mode (scaffold for v0.2)."""
from pathlib import Path

import pytest
import vcr


CASSETTE_DIR = Path(__file__).parent / "cassettes"


@pytest.fixture
def cassette(request):
    """Provide a vcr.use_cassette context bound to the current test name."""
    name = request.node.name + ".yaml"
    return vcr.use_cassette(
        str(CASSETTE_DIR / name),
        record_mode="new_episodes" if _record_mode() else "none",
        filter_headers=["authorization", "x-api-key"],
        match_on=["method", "scheme", "host", "port", "path", "query"],
    )


def _record_mode() -> bool:
    import os

    return os.environ.get("RECORD_CASSETTES", "").lower() in {"1", "true", "yes"}
