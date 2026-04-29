# Sample output -- Founder agent (PatentForgeLocal scenario)

This directory holds a complete Founder run committed to the repo so prospective adopters can browse what AgentSuite produces *without installing anything*.

## What this is, exactly

- **Generated under the deterministic mock LLM** (`agentsuite.llm.mock._default_mock_for_cli`) -- not a live Anthropic / OpenAI / Gemini / Ollama call.
- **Inputs:** `examples/patentforgelocal/` (project brief + voice sample).
- **Reproducible:** Regenerable by running `tests/golden/test_founder_patentforgelocal.py`'s setup against the mock provider.

## What this is *not*

The free-text artifact bodies (markdown specs in `brand-system.md`, `audience-map.md`, `claims-and-proof-library.md`, etc.) are **scaffold strings produced by the mock LLM**, not real-LLM-generated content. The mock prioritizes deterministic test stability over content quality; it returns short placeholder text in those bodies.

What's authentic and worth browsing:

- The **shape** of the output -- file names, JSON structure, directory layout -- is identical to a live run.
- Structural artifacts (`_state.json`, `inputs_manifest.json`, `extracted_context.json`, `consistency_report.json`, `cost_summary.json`, `qa_scores.json`, `qa_report.md`) reflect real kernel behavior.
- The 8 `brief-template-library/*.md` files are real, reusable templates that downstream agents consume.

## Want to see real LLM content?

Pick a provider and run it yourself:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY / GEMINI_API_KEY
agentsuite founder run   --business-goal "Launch PatentForgeLocal v1"   --project-slug pfl   --inputs-dir examples/patentforgelocal/
```

Cost on Anthropic Sonnet at v1.0.1 pricing: roughly $0.20-0.40 for a Founder run.

## v1.0.2 follow-up

Replacing the mock-LLM bodies in this directory with content from a real Anthropic Sonnet run is queued for v1.0.2 (cost ~$0.30, requires maintainer credentials). Tracked in `dev-reports/audit-AgentSuite-2026-04-29/next-sprint-watchlist.md` as the v1.0.1 deferred half of CR-01. The honesty fix above (this README) closes the v1.0.0 audit Blocker that conflated mock output with real run output.
