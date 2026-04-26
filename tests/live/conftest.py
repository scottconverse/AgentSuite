"""Live test gating — skipped unless RUN_LIVE_TESTS=1 (cost gate, not correctness gate)."""
import os
import urllib.error
import urllib.request

import pytest


def _ollama_daemon_running() -> bool:
    """Probe http://localhost:11434/api/tags; True if reachable."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="HEAD")
        with urllib.request.urlopen(req, timeout=0.5) as resp:  # noqa: S310 (fixed URL)
            return bool(resp.status == 200)
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        return False


def pytest_collection_modifyitems(config, items):
    """Skip live tests unless explicitly opted-in via env vars.

    Two gates:
      1. ``@pytest.mark.live`` tests — require ``RUN_LIVE_TESTS=1`` (cloud cost gate).
      2. ``@pytest.mark.live_ollama`` tests — require ``RUN_LIVE_OLLAMA_TESTS=1`` AND
         a running Ollama daemon at localhost:11434 (capability gate, $0 cost).

    Per Hard Rule 4a, skip markers are forbidden EXCEPT for capability/cost gates
    that the user explicitly opts out of.
    """
    cloud_disabled = os.environ.get("RUN_LIVE_TESTS") != "1"
    cloud_skip = pytest.mark.skip(
        reason="Live tier disabled. Set RUN_LIVE_TESTS=1 to enable (uses real LLM, costs money)."
    )

    ollama_opted_in = os.environ.get("RUN_LIVE_OLLAMA_TESTS") == "1"
    daemon_up = ollama_opted_in and _ollama_daemon_running()
    if not ollama_opted_in:
        ollama_skip = pytest.mark.skip(
            reason="Live-Ollama tier disabled. Set RUN_LIVE_OLLAMA_TESTS=1 to enable (zero cost)."
        )
    elif not daemon_up:
        ollama_skip = pytest.mark.skip(
            reason="Ollama daemon not reachable at localhost:11434. Start `ollama serve` and retry."
        )
    else:
        ollama_skip = None

    for item in items:
        if "live_ollama" in item.keywords and ollama_skip is not None:
            item.add_marker(ollama_skip)
        elif "live" in item.keywords and cloud_disabled:
            item.add_marker(cloud_skip)
