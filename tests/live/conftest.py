"""Live test gating — skipped unless RUN_LIVE_TESTS=1 (cost gate, not correctness gate)."""
import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip every test marked ``live`` unless the user opts in via ``RUN_LIVE_TESTS=1``.

    Per CLAUDE.md Hard Rule 4a, skip markers are forbidden EXCEPT for capability/cost
    gates that the user explicitly opts out of. Live tests cost real money; they run
    only at v0.X.0 release boundaries with explicit opt-in.
    """
    if os.environ.get("RUN_LIVE_TESTS") != "1":
        skip_marker = pytest.mark.skip(
            reason="Live tier disabled. Set RUN_LIVE_TESTS=1 to enable (uses real LLM, costs money)."
        )
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_marker)
