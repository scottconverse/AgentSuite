# Changelog

All notable changes to AgentSuite will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Roadmap

- **v1.0.0** — General availability after rc1 dogfood bake (5–7 days, real-project run, friction triage, CHANGELOG promotion, public launch posts).

## [1.0.0rc1] - 2026-04-29

Release candidate for v1.0.0. Compatibility freeze begins here. The seven-agent surface (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO), the kernel pipeline, the MCP tool naming, and the persisted `_state.json` schema are locked. Any breaking change post-rc1 requires explicit acknowledgement.

### Added

- **PEP 561 `py.typed` marker** at `agentsuite/py.typed` and registered in `pyproject.toml` package-data. Downstream consumers' mypy now follows AgentSuite's typed source through the installed wheel.
- **Downstream-consumer typing test** at `tests/integration/test_downstream_consumer.py`. Synthesizes a small package using AgentSuite's public API and runs `mypy --strict` against it; fails the suite on any typing regression that would surface to downstream users. Covers the editable-install case via `MYPYPATH`; the wheel-install case is verified by the existing release-workflow `clean-install-check` job.
- **Community-launch drafts** at `docs/community/discussions-seeds.md` and `docs/community/good-first-issues.md`. Discussions seed content (Welcome, 3 Q&A, 2 Ideas, General pointers) and 3 good-first-issue ticket drafts (`--quiet` flag, Marketing-agent USER-MANUAL example, `AGENTSUITE_OUTPUT_DIR` test). Drafts only — to be reviewed and posted by the maintainer once Discussions is enabled and rc1 is tagged.

### Changed

- **README hook** sharpened. The pre-install paragraph now leads with "Why AgentSuite" (target user + 30-second pitch + what makes it different) replacing the previous "Why this exists" framing. Same anchor position, tighter copy.
- **`docs/test-coverage.md` audit-honesty pass.** Documented the existing conditional `@pytest.mark.skipif` in `test_founder_pipeline.py` (cassette-recording path); explained why it is not a Hard Rule 4a violation. Updated default-run test count (689 of 692).

### Compatibility

The following are locked from rc1 onward; breaking changes require an explicit major-version bump or a documented deprecation cycle:

- **Public API surface:** `agentsuite.agents.<agent>.agent.<Agent>Agent`, `agentsuite.agents.<agent>.input_schema.<Agent>AgentInput`, `agentsuite.kernel.schema.{Constraints, RunState, ArtifactRef, Cost, Stage}`, `agentsuite.kernel.qa.{QARubric, RubricDimension}`, `agentsuite.llm.base.LLMProvider`, `agentsuite.llm.mock.MockLLMProvider`.
- **`_state.json` schema:** `schema_version: 2`. Any future shape change ships a migrator or raises `RunStateSchemaVersionError` with a documented remediation path (per ADR-0002 + ADR-0007).
- **MCP tool naming:** `<agent>_run`, `<agent>_resume`, `<agent>_approve` (per ADR-0004). Tool names are part of the public contract.
- **Kernel pipeline:** six stages (`intake → extract → spec → execute → qa → approval`). Stage names are part of the public contract; reordering or splitting requires the same deprecation discipline as an API change.

### Known limitations (intentional, deferred to v1.0.x or later)

- No multi-tenancy / API server mode (CLI + library + MCP server only).
- No web UI.
- No additional agents beyond the seven shipped.
- Per-run cost cap only (no per-day cap; tracked in Discussions).
- Single MCP server topology with env-gated agent enablement (no per-agent server).
- AgentSuite is local-first; no cloud-hosted offering.

## [0.9.3] - 2026-04-29

P4 — visual + sample-output release. Replaces the text-only landing
experience with rendered terminal SVGs and a committed sample run.
No code changes; documentation and assets only.

### Added

- **5 SVG screenshots** under `docs/screenshots/` rendered programmatically via `rich.Console.save_svg()`: `cli-founder-run.svg`, `runs-tree.svg`, `brand-system-rendered.svg`, `qa-report-rendered.svg`, `kernel-tree.svg`. Reproducible from the sample-output and `scripts/_v093_wire.py` invocation in the v0.9.3 dev report.
- **`examples/sample-output/founder/`** — a complete, browsable Founder run committed to the repo (29 files: state + inputs + extracted context + cost + QA + 7 spec artifacts + 8 brief templates + TREE.txt). Generated under the deterministic mock LLM so adopters can preview real output without installing AgentSuite.
- **Hero screenshot** in `README.md` above the install block, plus a "Screenshots and sample output" section linking the rendered SVGs and the committed sample run.
- **`docs/index.html`** sample section now embeds the cli, runs-tree, brand-system, qa-report, and kernel-tree SVGs in place of the text-only mock output.

### Deferred

- The 6th planned screenshot — `mcp-tool-list-claude-code.png` showing AgentSuite tools surfaced inside Claude Code — needs a real Claude Code session and is left for a hand capture in the next minor.

## [0.9.2] - 2026-04-28

Sprint 3 cleanup release — rubric audit + content-aware golden roll-out
+ test-coverage documentation. No user-facing behavior changes; this
release tightens the QA surface that protects v1.0.

> **Scope note:** The rubric audit + skip/deselect cleanup were originally
> planned for v0.9.1, but v0.9.1 was cut as a narrow hotfix that re-installed
> the `[mcp]` extra in the release smoke step (the v0.9.0 tag run had failed
> there). Sprint 3 cleanup work moved to v0.9.2; the screenshots +
> `examples/sample-output/founder/` fixture (P4) shifted from v0.9.2 to v0.9.3.

### Added

- **Founder rubric audit one-pager** at `docs/rubric-audit.md` — side-by-side cross-reference of every dimension on every agent's rubric, grouped by semantic theme, with per-agent uniqueness signal. Confirms the post-`2b1dda0` state (all seven agents at 9 dimensions) and resolves the asymmetry concern that prompted ADR-0001. Linked from ADR-0001 and CONTRIBUTING.
- **Content-aware golden coverage extended to all six remaining agents** (Design, Product, Engineering, Marketing, Trust/Risk, CIO). Each agent now has a primary spec markdown snapshot and `qa_scores.json` snapshot under `tests/golden/snapshots/<agent>/<scenario>/`, plus two new tests using `assert_artifact_exact()` and `assert_qa_within_tolerance()`. Golden suite goes from 42 to 54 tests.
- **Test-coverage notes** at `docs/test-coverage.md` documenting the three marker-gated tests (`cleanroom`, `live`, `live_ollama`) and confirming Hard Rule 4a satisfaction (zero `pytest.skip` markers).

### Changed

- **ADR-0001 narrative refreshed** to reflect the post-`2b1dda0` reality (Founder is at 9 dimensions, not 7). The decision (signal-driven counts, not symmetry) is unchanged.

## [0.9.1] - 2026-04-28

### Fixed

- **Release smoke step now installs the `[mcp]` extra.** v0.9.0's first tag run failed at the `agentsuite-mcp --help` smoke check because the audit-venv was installed from the bare wheel (no extras), so the optional `mcp` dependency was missing and the MCP CLI's deferred import raised `ModuleNotFoundError: No module named 'mcp'`. The smoke now installs the wheel with `[mcp]` so both documented entry points are verified before publish. v0.9.0 is the intended feature surface; v0.9.1 is the same surface with a working release pipeline.

## [0.9.0] - 2026-04-28

Sprint 3 — engineering hardening release. All seven planned items shipped
(content-aware golden coverage shipped lite for Founder; remaining six
agents follow in v0.9.1 per the approved sprint cut).

### ⚠ BREAKING

- **`_state.json` schema is now versioned (`schema_version: 2`).** Loading a
  pre-v0.9 state file raises `RunStateSchemaVersionError` with a message
  naming the run dir to delete. No automatic migration is shipped — pre-v0.9
  has no installed base outside the local workspace and a one-shot migrator
  earns its complexity only when it will be exercised. See ADR-0002.

### Added

- **Per-run cost telemetry.** `CostTracker` tracks `per_stage` cost
  breakdown, identity fields (`run_id`, `agent`, `provider`, `model`), and a
  `summary()`-shaped JSON contract. Every successful stage writes
  `cost_summary.json` to the run dir; best-effort write also fires on
  failure so a crashed run leaves an authoritative cost record. The
  schema is pinned by `tests/unit/kernel/test_cost.py::test_summary_schema_keys`.
- **`Cost.model: str | None` field** on the kernel cost type. Last-non-None
  wins under aggregation so per-stage and total summaries reflect the most
  recent model recorded.
- **Resume-from-failure cost carry-forward.** `_drive()` now seeds the new
  `CostTracker` with `state.cost_so_far` and rehydrates `per_stage` from
  the prior `cost_summary.json` on resume, so cap enforcement reflects
  multi-attempt total spend rather than zeroing on each restart. ADR-0007
  documents the contract; integration test in
  `tests/integration/test_resume_idempotency.py` pins it.
- **`RunStateSchemaVersionError`** typed exception in `agentsuite.kernel.state_store`.
- **Lazy importlib registry** `_INPUTS_BY_AGENT` resolves agent name to
  its input subclass on `StateStore.load()` so subclass-specific fields
  (e.g. `DesignAgentInput.campaign_goal`, `CIOAgentInput.organization_name`)
  survive save/load round-trip. ValidationError fallback to base
  `AgentRequest` preserves legacy fixture paths.
- **Architecture Decision Records** under `docs/adr/`. Seven ADRs backfill
  the load-bearing decisions surfaced during v0.8.x audits: rubric
  dimensions, RunState shape, retry/timeout policy, MCP tool naming,
  cost-cap-vs-telemetry split, no-PyPI distribution, resume idempotency.
  Index at `docs/adr/README.md`; CONTRIBUTING points new contributors at
  the index.
- **CIO `as_of_date: date | None` field** for reproducibility. Helpers
  `_resolve_as_of` + tz-aware `datetime.now(tz=timezone.utc)` replace the
  prior naive `datetime.now()`. Two runs with different `as_of_date`
  produce different quarter / fiscal-year strings in artifacts.
- **Clean-install verification on tag push.** `release.yml` gains a
  README install-block drift check (`scripts/check_install_block_drift.py`)
  and a CLI smoke step that runs `agentsuite --help` + `agentsuite-mcp --help`
  from the freshly-installed wheel. README install commands wrapped with
  `<!-- install:start -->` / `<!-- install:end -->` markers; canonical
  fixture at `tests/fixtures/install-block.md`. Windows matrix deferred to
  v0.9.x — Ubuntu catches the common-case regression.
- **Golden test content-aware helpers** in `tests/golden/_helpers.py`:
  `assert_artifact_exact()` for byte-stable text/JSON, `assert_qa_within_tolerance(rtol=0.05)`
  for numeric QA scores. Type split enforced — text never gets tolerance.
  Founder snapshot extended with `brand-system.md` + `qa_scores.json`
  fixtures.
- **`make update-goldens`** Makefile alias for `resnap-golden`. CONTRIBUTING
  documents the regenerate-and-review workflow.

### Changed

- **`StateStore.save()`** dumps `inputs` using the runtime instance's
  schema (subclass-aware) rather than the declared
  `RunState.inputs: AgentRequest` field type. The on-disk envelope adds
  a `schema_version` field; bump it when the persisted shape changes in
  a way that requires re-running rather than silent migration.

### Fixed

- **CIO date helpers are tz-aware.** `_current_quarter`, `_next_quarter`,
  `_current_fiscal_year`, `_fiscal_year_range` now accept a `date` parameter
  rather than calling naive `datetime.now()`. Year-boundary wrap (Q4 →
  Q1+1) is unit-tested.

### Test counts

- v0.8.4 baseline: 648 passing, 0 skipped
- v0.9.0: 676 passing, 0 skipped (+28 across cost, RunState, CIO date,
  drift check, idempotency, golden helpers)

## [0.8.4] - 2026-04-28

### Fixed

- **Release workflow `pip-audit` + `cyclonedx-py` invocation paths** — the v0.8.3 first-tag release run failed because both tools are installed in the outer system pip while the workflow called them via `.audit-venv/bin/`, where they don't exist. Reverted to system PATH for the tools, kept `.audit-venv` as the dependency-closure source for `pip freeze` and the SBOM interpreter target. v0.8.3 is the intended feature surface; v0.8.4 is the same surface with a working release pipeline.

## [0.8.3] - 2026-04-28

### Added

- **Supply-chain hygiene in `release.yml`** — every tag push now runs `pip-audit --strict` against the freshly-built wheel before publishing, generates a CycloneDX JSON SBOM (`agentsuite-<version>-sbom.cdx.json`), and attaches both the SBOM and the audit report to the GitHub Release. The audit step fails on any reported vulnerability across the installed dependency closure (no severity filter); an explicit `[skip-audit]` token in the commit message of the tagged commit arms a logged one-shot bypass for emergencies.
- **Weekly provider drift workflow** (`.github/workflows/provider-drift.yml`) — Mondays 09:00 UTC, fetches each LLM provider's live `/models` endpoint and asserts every model name in `agentsuite/llm/pricing.py` is still listed. Drift opens a labelled issue (`provider-drift`) with the JSON report attached, so silent model retirements surface within seven days. Providers without an API key in repo secrets are skipped, not failed. Ollama is excluded — local daemon, no pricing surface.
- **`scripts/check_provider_drift.py`** — runtime checker invoked by the weekly workflow; can be run locally with the relevant API keys in env.

### Changed

- **`ArtifactWriter._resolve_safe()` now rejects null-byte paths explicitly and consistently across platforms** — the explicit guard runs before pathlib touches the string, so Windows and POSIX raise the same `ValueError("contains null byte: ...")` instead of Windows producing pathlib's "embedded null character" via a different code path.
- **`release.yml` version-extraction step now strips `\r`** — defensive fix matching the same change shipped in `scripts/verify-release.sh` for v0.8.2; preempts CRLF leakage when `pyproject.toml` carries Windows line endings.

### Fixed

- **`test_resolve_safe_rejects_null_byte_path` no longer skipped on Windows** (Hard Rule 4a) — the platform skip is removed and the assertion tightened to `pytest.raises(ValueError, match="contains null byte")`. Test runs on every platform and verifies the new explicit guard.

## [0.8.2] - 2026-04-28

### ⚠ BREAKING

- **MCP tool names standardized to `agentsuite_<agent>_<verb>` (#37)** — primary tools renamed (e.g. `founder_run` → `agentsuite_founder_run`); stage tools renamed `agentsuite_<agent>_stage_<stage>` (e.g. `founder_stage_intake` → `agentsuite_founder_stage_intake`). Any existing MCP host configuration referencing the old names must be updated. No alias shim is shipped — given the pre-1.0 surface and no known external adopters at rename time, the rename ships clean.

### Changed

- **`mcp_server.py` dispatch refactored to a registry dict (#36)** — replaced 7-arm `if/elif` with `_MCP_MODULES: dict[str, str]` + `importlib.import_module()`. New agents can be added by registering a module path; no `mcp_server.py` edit required. The dispatch lambda now narrows `except Exception` to `except UnknownAgent`, surfacing real errors instead of swallowing them.
- **All `LLMProvider` instances now wrapped in `RetryingLLMProvider` (#38)** — `resolve_provider()` returns a tenacity-backed retry/timeout wrapper around `provider.complete()`. Retries on transient failures with exponential backoff (`stop_any(stop_after_attempt(N), stop_after_delay(T))`); does not retry on `ProviderNotInstalled`, `KeyboardInterrupt`, or `SystemExit`. Tunable via `AGENTSUITE_LLM_MAX_ATTEMPTS` (default 3) and `AGENTSUITE_LLM_TIMEOUT_SECS` (default 120.0). `tenacity>=8.2,<10` added to base dependencies.

### Added

- **6 new unit tests in `tests/unit/llm/test_retry.py`** — pass-through, name/model forwarding, retry-on-transient, give-up-after-max, no-retry-on-`ProviderNotInstalled`, max-attempts env-var honored.
- **`test_agent_without_mcp_module_is_skipped`** in `tests/unit/test_mcp_server.py` — ensures registry-driven dispatch tolerates unregistered agents.

### Dependencies

- `softprops/action-gh-release` 2 → 3 (#31)
- `actions/setup-python` 5 → 6 (#32)
- `actions/checkout` 4 → 6 (#33)
- `pillow` `<12` → `<13` (dev) (#34)
- `openai` `<2` → `<3` (dev) (#35)

## [0.8.1] - 2026-04-27

### Added
- **Unique auto-generated run IDs** (B1) — omitting `--run-id` generates a `run-<timestamp>-<hex>` ID automatically; `run_id` is returned in the JSON output.
- **`--force` flag on all `run` commands** (B2) — re-running an existing run ID without `--force` exits 1 with a clear error; `--force` overwrites.
- **Duplicate agent registration guard** (B3) — `AgentRegistry.register()` raises `ValueError` on duplicate name.
- **`ArtifactWriter._resolve_safe()`** (B4) — private method validating relative paths stay within `run_dir`; raises `ValueError` for traversal, null-byte, and Windows absolute paths.
- **`enabled_names()` always validates** (B5) — validation no longer skipped when registry is empty.
- **`resolve_provider` and `NoProviderConfigured` in public API** (C1) — re-exported from `agentsuite/__init__.py`.
- **Python SDK quick-start in README** (C2) — complete `FounderAgent` programmatic usage example.
- **`NoProviderConfigured` message tests** (C3) — 8 parametrised tests covering all 4 providers.
- **CLI error wrapping with `--debug`** (D2) — exceptions produce a clean one-line stderr message; `--debug` shows full traceback.
- **`--latest` flag on all `approve` commands** (D3) — auto-selects the most recently modified run for the agent.
- **Stage progress markers** (D1) — `✔ <stage> complete` printed after each pipeline stage before the final JSON.
- **Standardised `run` JSON output** (D4) — all 7 agents return `{"run_id", "primary_path", "status"}`.
- **MCP server deferred FastMCP import** (E1) — `FastMCP` moved under `TYPE_CHECKING`; no import error without the `mcp` extra.
- **Founder rubric dimension validation** (E2) — raises `ValueError` (not `KeyError`) for legacy 7-dim input.
- **Windows/mixed-slash path traversal tests** (E3) — platform-gated backslash tests; forward-slash traversal test runs everywhere.
- **USER-MANUAL.md extras table and CLI flag reconciliation** (F1/F3) — provider extras documented; all 7 agent flag sections reconciled with `build_cli_spec()`.
- **Landing page version badge** (F2) — updated to v0.8.1.
- **`docs/troubleshooting.md`** (F4) — new guide covering 5 failure modes.
- **`docs-drift` CI job** (G2) — checks 6 required doc artifacts exist and version in `pyproject.toml` matches latest CHANGELOG entry.

### Fixed
- Windows CI false-positive in path traversal test — backslash paths now correctly gated to `win32` only.
- CLI test crash on mixed progress-marker + JSON output — `_extract_json()` helper skips progress lines before parsing.

## [0.8.0] - 2026-04-27

> **Note:** v0.7.1 was prepared in code but never tagged or released as a standalone version; its contents shipped as part of v0.8.0.

### Added
- **Public API surface** — `from agentsuite import FounderAgent, DesignAgent, ...` now works from the top-level package. All 7 agent classes, kernel types (`BaseAgent`, `AgentRequest`, `RunState`, `ArtifactWriter`), registry (`AgentRegistry`, `default_registry`), and `ProviderNotInstalled` re-exported from `agentsuite/__init__.py`.
- **Registry-driven CLI dispatcher** — `AgentCLISpec` dataclass in `agentsuite.kernel.base_agent`. Each agent module exposes `build_cli_spec() -> AgentCLISpec`. `cli.py` now iterates agent modules and generates Typer subcommands generically — adding a new agent no longer requires touching `cli.py`.
- **Founder rubric expanded to 9 dimensions** — added `constraint_adherence` (strategy respects stated budget, timeline, and resource constraints) and `completeness` (all spec artifacts populated with substantive content). Now consistent with all other agents.
- **Architecture diagram in README** — Mermaid `flowchart LR` diagram of the 5-stage pipeline with QA gate and approval branch.
- **Sample output on landing page** — CLI output example added to `docs/index.html`.
- **CI wheel-smoke job** — builds the wheel, installs in a fresh venv (no extras), and verifies all 7 `prompt_loader` imports plus `agentsuite --help` and `agentsuite-mcp --help`. Catches missing package-data and broken entry points before users do.
- **Branch protection on `main`** — all 5 CI checks required: `lint / ruff-mypy`, `test / cleanroom`, `test / unit-integration-golden (3.11)`, `test / unit-integration-golden (3.12)`, `test / wheel-smoke`. Force-push blocked.
- **`AgentRegistry.registered_names()`** — new public method returning sorted list of all registered agent names. Used by `cli.py` and `agentsuite agents` command.
- **QA boundary test** — `test_qa_boundary_exactly_at_threshold_passes` and `test_qa_boundary_just_below_threshold_fails` pin the `>= 7.0` scoring behavior.
- **RunState round-trip test** — documents that subclass-specific fields do not survive JSON round-trip through `RunState.inputs` (typed as `AgentRequest`).
- **`HardCapExceeded` propagation test** — integration test verifying the exception propagates correctly through `_drive()`.
- **Golden test JSON structure assertions** — all 7 agent golden tests now assert `qa_scores.json` has `scores/average/passed/requires_revision` keys and `consistency_report.json` has `mismatches`.
- **`ProviderNotInstalled(ImportError)`** — new exception class in `agentsuite.llm.base`. Raised by all provider constructors when the optional SDK is missing, with a `pip install agentsuite[extra]` hint.

### Changed
- **LLM SDK dependencies are now optional extras** — `pip install agentsuite` installs only the core library (pydantic, typer, httpx, jinja2). Provider SDKs are opt-in: `pip install agentsuite[anthropic]`, `agentsuite[openai]`, `agentsuite[gemini]`, `agentsuite[ollama]`, `agentsuite[mcp]`, `agentsuite[image]`, or `agentsuite[all]`.
- **`approve` commands normalized** — all 7 agents now return `{"run_id", "status", "approved_by"}` JSON. Previously marketing, engineering, product, trust-risk, and cio returned plain text.

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

[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v0.9.1...HEAD
[0.9.1]: https://github.com/scottconverse/AgentSuite/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/scottconverse/AgentSuite/compare/v0.8.4...v0.9.0
[0.8.4]: https://github.com/scottconverse/AgentSuite/compare/v0.8.3...v0.8.4
[0.8.3]: https://github.com/scottconverse/AgentSuite/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/scottconverse/AgentSuite/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/scottconverse/AgentSuite/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/scottconverse/AgentSuite/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/scottconverse/AgentSuite/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/scottconverse/AgentSuite/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/scottconverse/AgentSuite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/scottconverse/AgentSuite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/scottconverse/AgentSuite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/scottconverse/AgentSuite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottconverse/AgentSuite/releases/tag/v0.1.0
