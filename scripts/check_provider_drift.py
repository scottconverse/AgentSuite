"""Provider price/deprecation drift checker.

Fetches the live ``/models`` endpoint for each LLM provider configured in
:mod:`agentsuite.llm.pricing` and asserts that every model name listed in the
pricing tables is still returned by the provider. Writes a JSON drift report
to ``provider-drift-report.json`` and exits non-zero on any drift detected.

Designed to run from the ``provider-drift`` GitHub workflow on a weekly cron.
Providers without an API key in env are skipped (logged), not failed — the
workflow surfaces missing-secret state as a separate alert.

Endpoints (as of 2026-04-28):

* Anthropic — ``GET https://api.anthropic.com/v1/models`` (header ``x-api-key``,
  ``anthropic-version: 2023-06-01``)
* OpenAI — ``GET https://api.openai.com/v1/models`` (header ``Authorization:
  Bearer <key>``)
* Gemini — ``GET https://generativelanguage.googleapis.com/v1beta/models?key=<key>``

Ollama is intentionally absent — local daemon, no pricing surface.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import httpx

from agentsuite.llm.pricing import (
    ANTHROPIC_PRICING,
    GEMINI_PRICING,
    OPENAI_PRICING,
)


def _fetch_anthropic_models() -> list[str]:
    """Return the list of model IDs returned by Anthropic's /models endpoint."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return []
    r = httpx.get(
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        timeout=30.0,
    )
    r.raise_for_status()
    return [m["id"] for m in r.json().get("data", [])]


def _fetch_openai_models() -> list[str]:
    """Return the list of model IDs returned by OpenAI's /models endpoint."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return []
    r = httpx.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30.0,
    )
    r.raise_for_status()
    return [m["id"] for m in r.json().get("data", [])]


def _fetch_gemini_models() -> list[str]:
    """Return the list of model IDs returned by Gemini's /models endpoint."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return []
    r = httpx.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
        timeout=30.0,
    )
    r.raise_for_status()
    # Gemini returns "models/<id>" — strip the prefix.
    return [m["name"].removeprefix("models/") for m in r.json().get("models", [])]


PROVIDERS: dict[str, tuple[dict[str, dict[str, float]], Any]] = {
    "anthropic": (ANTHROPIC_PRICING, _fetch_anthropic_models),
    "openai":    (OPENAI_PRICING,    _fetch_openai_models),
    "gemini":    (GEMINI_PRICING,    _fetch_gemini_models),
}


def main() -> int:
    """Run the drift check and write a JSON report.

    Returns 0 if all listed models are still present (or all providers were
    skipped due to missing keys), 1 if any model is missing from a fetched
    endpoint.
    """
    report: dict[str, Any] = {"providers": {}, "drift_found": False}
    drift = False

    for name, (table, fetcher) in PROVIDERS.items():
        try:
            live = fetcher()
        except Exception as e:  # noqa: BLE001 — workflow surfaces detail
            report["providers"][name] = {"status": "fetch_error", "error": str(e)}
            drift = True
            continue
        if not live:
            report["providers"][name] = {"status": "skipped_no_key"}
            continue

        listed = set(table.keys())
        missing = sorted(listed - set(live))
        report["providers"][name] = {
            "status": "drift" if missing else "ok",
            "listed_count": len(listed),
            "live_count": len(live),
            "missing_from_live": missing,
        }
        if missing:
            drift = True

    report["drift_found"] = drift
    with open("provider-drift-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
