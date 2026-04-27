# Changelog

All notable changes to AgentSuite will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.5.0] - 2026-04-26

### Added
- **Marketing Agent** — 5-stage pipeline (intake → extract → spec → execute → qa) producing 9 marketing spec artifacts: Campaign Brief, Target Audience Profile, Messaging Framework, Content Calendar, Channel Strategy, SEO Keyword Plan, Competitive Positioning, Launch Plan, and Measurement Framework.
- **Marketing brief templates** — 8 ready-to-fill templates: ad copy brief, blog post brief, email campaign, influencer brief, landing page brief, press release, quarterly report, and social post series.
- **Marketing rubric** — 9-dimension QA rubric (audience_clarity, message_resonance, channel_fit, metric_specificity, budget_realism, anti_vanity_metrics, content_depth, competitive_awareness, launch_sequencing) with pass threshold 7.0/10.
- **MCP tools** — 10 tools for the Marketing agent (`marketing_run`, `marketing_approve`, `marketing_list_runs`, `marketing_get_artifact`, `marketing_get_qa_scores`, plus 5 stage-level tools).
- **CLI subcommand** — `agentsuite marketing run` and `agentsuite marketing approve`.
- **Skill manifest** — `claude/skills/marketing-agent/SKILL.md` with MCP snippet and install-skills.sh integration.

## [0.4.0] - 2026-04-26

### Added
- **Engineering Agent** — 5-stage pipeline (intake → extract → spec → execute → qa) producing 9 engineering spec artifacts: Architecture Decision Record, System Design, API Spec, Data Model, Security Review, Deployment Plan, Runbook, Tech Debt Register, and Performance Requirements.
- **Engineering brief templates** — 8 ready-to-fill templates: sprint ticket, code review checklist, incident report, capacity plan, on-call handoff, release checklist, postmortem, and vendor evaluation.
- **Engineering rubric** — 9-dimension QA rubric (implementation_specificity, testability, security_posture, scalability_awareness, dependency_hygiene, anti_overengineering, operational_completeness, decision_traceability, api_contract_clarity) with pass threshold 7.0/10.
- **MCP tools** — 10 tools for the Engineering agent (`engineering_run`, `engineering_approve`, `engineering_list_runs`, `engineering_get_artifact`, `engineering_get_qa_scores`, plus 5 stage-level tools).
- **CLI subcommand** — `agentsuite engineering run` and `agentsuite engineering approve`.
- **Skill manifest** — `claude/skills/engineering-agent/SKILL.md` with MCP snippet and install-skills.sh integration.

## [0.3.0] — 2026-04-26

### Added
- **Product Agent** (`agentsuite product run / approve`) — five-stage pipeline generating 9 specification artifacts and 8 brief templates
  - Stage 1 — Intake: classifies uploaded research docs and competitor teardowns; produces `inputs_manifest.json`
  - Stage 2 — Extract: LLM extracts user pain points, competitor gaps, market signals, technical constraints, assumed non-goals, and open questions into `extracted_context.json`
  - Stage 3 — Spec: generates 9 PM artifacts — PRD, user story map, feature prioritization, success metrics, competitive analysis, user personas, acceptance criteria, product roadmap, risk register — plus a cross-artifact consistency check
  - Stage 4 — Execute: renders 8 brief templates (sprint planning, stakeholder update, launch announcement, feature spec, user interview guide, A/B test plan, demo script, investor update) into `brief-template-library/`
  - Stage 5 — QA: scores against a 9-dimension `PRODUCT_RUBRIC` (problem_clarity, user_grounding, scope_discipline, metric_specificity, feasibility_awareness, anti_feature_creep, acceptance_completeness, stakeholder_clarity, roadmap_sequencing); pass threshold 7.0
- **MCP tools**: `product_run`, `product_resume`, `product_approve`, `product_get_status`, `product_list_runs` + 5 stage tools
- **Skill**: `product-agent` skill with `/product-agent` slash command
- **Golden test**: `tests/golden/test_product_acme_app.py` with frozen `acme-app` fixture
- **Integration tests**: full pipeline, approval promotion, and resume-from-spec E2E tests

## [0.2.0] — 2026-04-26

### Added

- **Gemini provider** — `agentsuite/llm/gemini.py` exposes `GeminiProvider` conforming to `LLMProvider` Protocol. Supports `gemini-2.5-pro`, `gemini-2.5-flash` (default), and `gemini-2.5-flash-lite` with v0.x-pinned pricing. Auto-detected by resolver after Anthropic and OpenAI; accepts `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
- **Centralized pricing module** — `agentsuite/llm/pricing.py` consolidates `ANTHROPIC_PRICING`, `OPENAI_PRICING`, and `GEMINI_PRICING` so each provider imports its slice instead of holding a local table.
- **Ollama provider** — `agentsuite/llm/ollama.py` exposes `OllamaProvider` for local LLMs (zero cost). Default `gemma4:e4b`; user-overridable per request. Auto-detected by the resolver as a last-resort fallback (probes `localhost:11434/api/tags`). Three install-time model choices documented: `gemma4:e2b` (~3 GB), `gemma4:e4b` (~5 GB, recommended), `gemma4:26b-moe` (~15 GB).
- **`live_ollama` test tier** — `tests/live/test_ollama_live.py` runs the full Founder pipeline against a real local Ollama daemon at $0 cost. Gated by `RUN_LIVE_OLLAMA_TESTS=1` env var plus a daemon-presence check.
- **Mock identity override** — `MockLLMProvider(name=...)` and `_default_mock_for_cli(provider_name=...)` let tests simulate any provider's identity.
- **Design Agent** (`agentsuite/agents/design/`) — second concrete agent. Five-stage pipeline (intake → extract → spec → execute → qa → approval) produces 17 output artifacts: `inputs_manifest.json`, `extracted_context.json`, 9 design spec markdown files (`visual-direction.md`, `design-brief.md`, `mood-board-spec.md`, `brand-rules-extracted.md`, `image-generation-prompt.md`, `revision-instructions.md`, `design-qa-report.md`, `accessibility-audit-template.md`, `final-asset-acceptance-checklist.md`), `consistency_report.json`, 8 brief templates in `brief-template-library/` (banner-ad, email-header, social-graphic, landing-hero, deck-slide, print-flyer, video-thumbnail, icon-set), `export-manifest-template.json`, `qa_report.md`, `qa_scores.json`, plus `_state.json`. QA uses the nine-dimension `DESIGN_RUBRIC` (spec_completeness, brand_fidelity, audience_fit, craft_specificity, accessibility_rigor, anti_genericity, revision_actionability, consistency, image_prompt_precision) with a 7.0 pass threshold. Input parameters: `target_audience`, `campaign_goal`, `channel` (web/social/email/print/video/deck/other), `brand_docs`, `reference_assets`, `anti_examples`, `accessibility_requirements`.
- **Design MCP tools** — `design_run`, `design_resume`, `design_approve`, `design_get_status`, `design_list_runs`. Enabled when `AGENTSUITE_ENABLED_AGENTS=founder,design`.
- **Design CLI subcommand** — `agentsuite design run --target-audience ... --campaign-goal ...` and `agentsuite design approve`.
- **Design skill wrappers** (Claude only) — `~/.claude/skills/design-agent/SKILL.md` + `~/.claude/commands/design-agent.md` installed via updated `scripts/install-skills.sh`.

### Changed

- Resolver auto-detect order: anthropic → openai → gemini → ollama (was: anthropic → openai).
- `pip install` now pulls `google-generativeai>=0.8` and `ollama>=0.4` as transitive dependencies.
- Agent registry `_bootstrap_default_registry` now pre-registers `DesignAgent` in addition to `FounderAgent` (opt-in via `AGENTSUITE_ENABLED_AGENTS=founder,design`).
- `_default_mock_for_cli` extended to cover both Founder and Design pipeline keywords for CLI smoke tests.

### Fixed

- `scripts/run-cleanroom.sh` cross-platform venv activation — was hardcoded to Windows `.venv/Scripts/`; now detects `Scripts` vs `bin` at runtime.
- `DesignAgent._wrap` resume correctness — on JSON round-trip, `RunState` serialised `DesignAgentInput` as the base `AgentRequest`, dropping `campaign_goal` and `target_audience`. The wrapper now accepts a pre-validated `DesignAgentInput` via `edits["inputs"]`.

## [0.1.0] — 2026-04-26

Initial release.

### Added

- **Specification Kernel** — pydantic schema (`AgentRequest`, `RunState`, `Cost`, `ArtifactRef`), abstract `BaseAgent` with persisted six-stage pipeline (intake → extract → spec → execute → qa → approval), `ArtifactWriter` with SHA-tracked idempotent writes and `_kernel/` promotion, `QARubric` framework with markdown scoring, `ApprovalGate` with state transitions, `CostTracker` with soft warn ($1) / hard kill ($5) caps configurable via `AGENTSUITE_COST_CAP_USD`, `StateStore` for JSON-persisted run state.
- **LLM provider layer** — `LLMProvider` Protocol with `LLMRequest`/`LLMResponse` models, concrete `AnthropicProvider` and `OpenAIProvider` with v0.1.0-pinned pricing tables, `MockLLMProvider` for tests, and `resolve_provider()` with explicit > env > auto-detect precedence.
- **Founder Agent** — first concrete agent. Five stages produce 26 artifacts: `inputs_manifest.json`, `extracted_context.json`, 9 spec markdown files (`brand-system.md`, `founder-voice-guide.md`, `product-positioning.md`, `audience-map.md`, `claims-and-proof-library.md`, `visual-style-guide.md`, `campaign-production-workflow.md`, `asset-qa-checklist.md`, `reusable-prompt-library.md`), `consistency_report.json`, 11 brief templates in `brief-template-library/`, `export-manifest-template.json`, `qa_report.md`, `qa_scores.json`, plus `_state.json`/`_meta.json`. QA uses the seven-dimension `FOUNDER_RUBRIC` (reusability, brand_consistency, claims_grounded, voice_fit, template_specificity, goal_alignment, anti_genericity) with a 7.0 pass threshold. Cross-artifact consistency check runs at end of stage 3 and fails on critical mismatches.
- **MCP server** (`agentsuite-mcp`) — stdio transport for Codex, Claude Code, and Cowork. Default 5 founder tools (`founder_run`, `founder_resume`, `founder_approve`, `founder_get_status`, `founder_list_runs`) plus 3 cross-agent tools (`agentsuite_list_agents`, `agentsuite_kernel_artifacts`, `agentsuite_cost_report`). Optional 5 stage-scoped tools gated behind `AGENTSUITE_EXPOSE_STAGES=true`.
- **CLI** (`agentsuite`) — `founder run`, `founder approve`, `list-runs`, `agents`. Uses Typer.
- **Cleanroom E2E** — `scripts/run-cleanroom.sh` builds a fresh venv, installs from pyproject, and runs the full Founder pipeline against the `examples/patentforgelocal/` fixture. Default uses mocked LLM ($0); `--live` flag runs against real provider with $5 cap.
- **Test tiers** — unit (`tests/unit/`, mocked, deterministic), integration (`tests/integration/`, mocked LLM end-to-end pipeline), golden (`tests/golden/`, frozen patentforgelocal fixture with structure + critical-phrase blocklist snapshots), live (`tests/live/`, gated by `RUN_LIVE_TESTS=1`, capped at $3/test, runs only at v0.X.0 boundaries).
- **Documentation** — README.md, README-FULL.pdf with Mermaid architecture diagrams, USER-MANUAL.md, CONTRIBUTING.md, docs/index.html GitHub Pages landing.
- **Skill wrappers** (Claude only) — `~/.claude/skills/founder-agent/SKILL.md` + `~/.claude/commands/founder-agent.md` installed via `scripts/install-skills.sh`.
- **CI** — GitHub Actions for test (PR), lint (PR), release (tag).
- **Build artifacts** — wheel + sdist produced via `python -m build`; PyPI publishing intentionally not enabled (per maintainer decision).

### Locked architectural decisions for v0.1.0

- Provider-agnostic LLM with Anthropic/OpenAI; SQLite state storage deferred to v0.2.
- Hard-coded 11 brief templates; user-extensible registry deferred to v0.2.
- LLM-only voice extraction; computed style metrics deferred to v0.2.
- Stdio MCP transport only; SSE/HTTP deferred.
- Per-run cost cap only; per-day cap deferred.
- Single MCP server with env-gated agent enablement (no per-agent server topology).

[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/scottconverse/AgentSuite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/scottconverse/AgentSuite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/scottconverse/AgentSuite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/scottconverse/AgentSuite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottconverse/AgentSuite/releases/tag/v0.1.0
