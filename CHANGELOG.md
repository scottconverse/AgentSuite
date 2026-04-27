# Changelog

All notable changes to AgentSuite will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.8.0] - 2026-04-27

### Added
- **Public API surface** — `from agentsuite import FounderAgent, DesignAgent, ...` now works from the top-level package. All 7 agent classes, kernel types (`BaseAgent`, `AgentRequest`, `RunState`, `ArtifactWriter`), registry (`AgentRegistry`, `default_registry`), and `ProviderNotInstalled` re-exported from `agentsuite/__init__.py`.
- **Registry-driven CLI dispatcher** — `AgentCLISpec` dataclass in `agentsuite.kernel.base_agent`. Each agent module exposes `build_cli_spec() -> AgentCLISpec`. `cli.py` now iterates agent modules and generates Typer subcommands generically — adding a new agent no longer requires touching `cli.py`.
- **Founder rubric expanded to 9 dimensions** — added `constraint_adherence` (strategy respects stated budget, timeline, and resource constraints) and `completeness` (all spec artifacts populated with substantive content). Now consistent with all other agents.
- **Architecture diagram in README** — Mermaid `flowchart LR` diagram of the 5-stage pipeline with QA gate and approval branch.
- **Sample output on landing page** — CLI output example added to `docs/index.html`.

### Changed
- **LLM SDK dependencies are now optional extras** — `pip install agentsuite` installs only the core library (pydantic, typer, httpx, jinja2). Provider SDKs are opt-in: `pip install agentsuite[anthropic]`, `agentsuite[openai]`, `agentsuite[gemini]`, `agentsuite[ollama]`, `agentsuite[mcp]`, `agentsuite[image]`, or `agentsuite[all]`.
- **`approve` commands normalized** — all 7 agents now return `{"run_id", "status", "approved_by"}` JSON. Previously marketing, engineering, product, trust-risk, and cio returned plain text.

## [0.7.1] - 2026-04-27

### Added
- **CI wheel-smoke job** — builds the wheel, installs in a fresh venv (no extras), and verifies all 7 `prompt_loader` imports plus `agentsuite --help` and `agentsuite-mcp --help`. Catches missing package-data and broken entry points before users do.
- **Branch protection on `main`** — all 5 CI checks required: `lint / ruff-mypy`, `test / cleanroom`, `test / unit-integration-golden (3.11)`, `test / unit-integration-golden (3.12)`, `test / wheel-smoke`. Force-push blocked.
- **`AgentRegistry.registered_names()`** — new public method returning sorted list of all registered agent names. Used by `cli.py` and `agentsuite agents` command.
- **QA boundary test** — `test_qa_boundary_exactly_at_threshold_passes` and `test_qa_boundary_just_below_threshold_fails` pin the `>= 7.0` scoring behavior.
- **RunState round-trip test** — documents that subclass-specific fields do not survive JSON round-trip through `RunState.inputs` (typed as `AgentRequest`).
- **`HardCapExceeded` propagation test** — integration test verifying the exception propagates correctly through `_drive()`.
- **Golden test JSON structure assertions** — all 7 agent golden tests now assert `qa_scores.json` has `scores/average/passed/requires_revision` keys and `consistency_report.json` has `mismatches`.
- **`ProviderNotInstalled(ImportError)`** — new exception class in `agentsuite.llm.base`. Raised by all provider constructors when the optional SDK is missing, with a `pip install agentsuite[extra]` hint.

### Fixed
- **Path traversal guard in `ArtifactWriter.write()`** — raises `ValueError` when a relative path escapes the run directory. Prevents `../../etc/passwd`-style writes.
- **Gemini API key precedence** — `GEMINI_API_KEY` now correctly takes priority over `GOOGLE_API_KEY` in both the resolver and the provider constructor.
- **`AgentRegistry.enabled_names()` validation** — only validates against registered agents when the registry is non-empty. Previously raised `UnknownAgent` on empty registries with env vars set.
- **Cost persistence on stage exception** — `_drive()` now saves `cost_so_far` to the state store in the `except` branch, so partial costs are not lost when a stage raises.
- **`mcp_server.py` deferred import** — `FastMCP` import moved inside `build_server()`. Module now imports cleanly without the `mcp` SDK installed; the `ProviderNotInstalled`-style error is only raised when the server is actually started.
- **Mock consistency-check responses** — 4 agent mock responses were returning `consistent`/`findings` keys instead of `mismatches`. Fixed to match the schema all 5-stage agents expect.
- **`dev` extra includes all LLM SDKs** — `pip install agentsuite[dev]` now installs all optional SDK extras, so the full test suite runs on a clean clone without manual extra installation.

## [0.7.0] - 2026-04-27

### Added
- **CIO Agent** — 5-stage pipeline (intake → extract → spec → execute → qa) producing 9 IT strategy and governance artifacts:
  - `it-strategy.md` — organization-wide IT strategy aligned to business priorities and maturity level (primary artifact)
  - `technology-roadmap.md` — multi-horizon roadmap of technology investments, retirements, and capability milestones
  - `vendor-portfolio.md` — structured inventory of technology vendors with spend, risk rating, and strategic fit assessment
  - `digital-transformation-plan.md` — sequenced plan for digitizing processes, platforms, and operating models
  - `it-governance-framework.md` — decision rights, escalation paths, and IT steering committee charter
  - `enterprise-architecture.md` — current-state and target-state architecture across applications, data, infrastructure, and integration layers
  - `budget-allocation-model.md` — IT budget breakdown across run/grow/transform categories with justification
  - `workforce-development-plan.md` — skills gap analysis, training roadmap, and hiring plan for the IT organization
  - `it-risk-appetite-statement.md` — formal statement of the organization's tolerance for IT and technology risk
- **CIO brief templates** — 8 ready-to-fill templates: board-technology-briefing, it-steering-committee-agenda, vendor-review-summary, project-portfolio-status, digital-initiative-proposal, it-investment-case, technology-modernization-pitch, and quarterly-it-review.
- **MCP tools** — 10 tools for the CIO agent (`agentsuite_cio_run`, `agentsuite_cio_approve`, `agentsuite_cio_list_runs`, `agentsuite_cio_get_artifact`, `agentsuite_cio_get_qa_scores`, plus 5 stage-level tools).
- **CLI subcommand** — `agentsuite cio run` and `agentsuite cio approve`.
- **Skill manifest** — `claude/skills/cio-agent/SKILL.md` with MCP snippet and install-skills.sh integration.

## [0.6.0] - 2026-04-27

### Added
- **Trust/Risk Agent** — 5-stage pipeline (intake → extract → spec → execute → qa) producing 9 trust and risk spec artifacts:
  - `threat-model.md` — structured threat model mapping assets, threat actors, attack vectors, and mitigations
  - `risk-register.md` — prioritized registry of identified risks with likelihood, impact, and owner
  - `control-framework.md` — security and compliance controls mapped to threats and regulatory requirements
  - `incident-response-plan.md` — step-by-step playbook for detecting, containing, and recovering from incidents
  - `compliance-matrix.md` — requirements traceability across applicable regulatory frameworks
  - `vendor-risk-assessment.md` — structured evaluation of third-party vendor security posture
  - `security-policy.md` — organizational security policy covering access, data handling, and acceptable use
  - `audit-readiness-report.md` — evidence summary and gap analysis for upcoming audits
  - `residual-risk-acceptance.md` — formal acceptance documentation for risks not fully mitigated
- **Trust/Risk brief templates** — 8 ready-to-fill templates: breach-notification, executive-risk-summary, penetration-test-brief, remediation-tracker, risk-acceptance-form, security-awareness-brief, tabletop-exercise-scenario, and vendor-security-questionnaire.
- **MCP tools** — 10 tools for the Trust/Risk agent (`agentsuite_trust_risk_run`, `agentsuite_trust_risk_approve`, `agentsuite_trust_risk_list_runs`, `agentsuite_trust_risk_get_artifact`, `agentsuite_trust_risk_get_qa_scores`, plus 5 stage-level tools).
- **CLI subcommand** — `agentsuite trust-risk run` and `agentsuite trust-risk approve`.
- **Skill manifest** — `claude/skills/trust-risk-agent/SKILL.md` with MCP snippet and install-skills.sh integration.

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

[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/scottconverse/AgentSuite/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/scottconverse/AgentSuite/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/scottconverse/AgentSuite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/scottconverse/AgentSuite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/scottconverse/AgentSuite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/scottconverse/AgentSuite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottconverse/AgentSuite/releases/tag/v0.1.0
