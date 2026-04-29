# AgentSuite Sprint Plan — Path to v1.0

**Drafted:** 2026-04-28
**Author:** Claude (Engineering, with auditor cross-check)
**Current state:** v0.8.2 shipped, all CI green
**Target:** v1.0.0 (date TBD — driven by completion of below, not calendar)

---

## Release ladder

```
v0.8.2  (shipped 2026-04-28) ──┐
                                │
v0.8.3  (security hygiene)     │  ~3 days
                                │
v0.9.0  (Sprint 3 — engineering hardening)   ~7-10 days
                                │
v0.9.1  (CIO fixes + Founder rubric audit)   ~2 days
                                │
v0.9.2  (P4 — visual + sample output docs)   ~3 days
                                │
v1.0.0-rc1  (release candidate, soft launch) ~2 days
                                │
v1.0.0  (general availability)               ~2 days post-RC
```

Total estimate: 19–22 working days from v0.8.2 ship to v1.0.0 GA.

---

## v0.8.3 — Security hygiene release

**Goal:** Open-source supply-chain hygiene table-stakes before v0.9.0 sprint work introduces churn.

**Scope:**

1. **`pip-audit` in release workflow** (`.github/workflows/release.yml`)
   - Add step before build: `pip-audit --strict --requirement requirements-frozen.txt` (or equivalent against installed extras)
   - Fail release if any HIGH/CRITICAL CVE found
   - Allow override via `[skip-audit]` token in tag message for emergencies, with audit trail in release notes
   - Acceptance: tag push surfaces any vulnerable transitive dep before publish

2. **SBOM generation** (CycloneDX JSON)
   - Add `cyclonedx-py` (or `cyclonedx-bom`) to release workflow as build dep
   - Generate `agentsuite-<version>-sbom.cdx.json` per release
   - Attach to GH release alongside wheel + sdist
   - Acceptance: every published release has machine-readable SBOM downloaders can ingest

3. **Provider price/deprecation drift CI** (`.github/workflows/provider-drift.yml`)
   - Schedule: weekly (`cron: '0 9 * * 1'`)
   - For each provider in `agentsuite/llm/pricing.py`: hit the provider's models endpoint, assert every model name listed in pricing table is still returned
   - Open an issue (not fail master) when drift detected, labelled `provider-drift`
   - Acceptance: silent model retirements caught within 7 days

4. **Windows null-byte path test resolution** (Hard Rule 4a)
   - Investigate the skip in `tests/unit/test_artifact_writer.py` (or wherever it lives)
   - Either: fix so it runs on Windows, or delete with explicit comment explaining why genuinely untestable on platform
   - No `pytest.mark.skip` carried into v1.0
   - Acceptance: pytest reports 0 skipped tests

5. **CHANGELOG + version bump** (0.8.3)

**Sequencing:** all 4 items in parallel (no inter-dependencies). One PR per item for clean blame, or one consolidated `chore/v0.8.3-security-hygiene` PR.

**Acceptance for v0.8.3 tag:**
- All 4 items merged + green
- New release workflow exercised on the v0.8.3 tag itself (clean dogfood)
- pip-audit run against v0.8.3 wheel returns clean
- SBOM attached to GH release
- weekly drift workflow scheduled and runs on first Monday post-merge
- 0 skipped tests in pytest output

---

## v0.9.0 — Sprint 3 (engineering hardening)

**Goal:** Close the principal engineering watchlist items, ship cost telemetry as the headline feature, harden golden tests against semantic regressions.

### 1. Cost telemetry + configurable cost cap

**Files:**
- `agentsuite/kernel/cost.py` (new or extended)
- `agentsuite/kernel/pipeline.py` (write `cost_summary.json` per run)
- `agentsuite/kernel/base_agent.py` (cost cap enforcement read from env)
- `agentsuite/llm/pricing.py` (already exists, extend per-stage tracking)
- `tests/unit/kernel/test_cost.py` (new)
- `examples/sample-output/founder/cost_summary.json` (committed sample)

**Behavior:**
- Per-run JSON written to `.agentsuite/runs/<run-id>/cost_summary.json`:
  ```json
  {
    "run_id": "run-...",
    "agent": "founder",
    "provider": "anthropic",
    "model": "claude-sonnet-4-5",
    "stages": [
      {"stage": "intake", "input_tokens": 1234, "output_tokens": 567, "cost_usd": 0.0123},
      ...
    ],
    "total_input_tokens": 12345,
    "total_output_tokens": 6789,
    "total_cost_usd": 0.234,
    "cap_usd": 5.00,
    "cap_remaining_usd": 4.766
  }
  ```
- `AGENTSUITE_COST_CAP_USD` default raised from current to **`5.00`** (TBD — confirm with Scott; current likely $1 or $2)
- Cap enforcement composes with approval gate: operator sees cost before approving
- `MCP` tool surfaces `cost_summary` field in run-result payload

**Acceptance:**
- Every run produces `cost_summary.json` with full per-stage breakdown
- Hitting cap raises `HardCapExceeded` with `cost_summary.json` already written for the partial run
- Test: synthesize 3-stage run, assert sum of stage costs == total
- Test: cap enforcement at boundary (just under cap completes; just over fails)
- Test: `cost_summary.json` survives interrupt + resume (covered by item 5 below)

### 2. RunState discriminated union + schema-version error

**Files:**
- `agentsuite/kernel/run_state.py`
- `agentsuite/kernel/exceptions.py` (new `RunStateSchemaVersionError`)
- `tests/unit/kernel/test_run_state.py`
- 7 agent input modules (`*/agent.py` — `*AgentInput` classes already exist)

**Behavior:**
- `RunState.inputs` retyped from `AgentRequest` to discriminated union keyed by `agent_name`:
  ```python
  AgentInputUnion = Annotated[
      Union[FounderAgentInput, DesignAgentInput, ProductAgentInput,
            EngineeringAgentInput, MarketingAgentInput, TrustRiskAgentInput, CIOAgentInput],
      Field(discriminator="agent_name"),
  ]
  ```
- `_state.json` schema version field added: `"schema_version": 2`
- Reading `_state.json` without `schema_version` (pre-v0.9) raises `RunStateSchemaVersionError("pre-v0.9 state file at <path>; delete .agentsuite/runs/<run-id>/ and re-run")`
- No migration shipped (YAGNI per pre-v1.0 + zero known persisted-state users)
- CHANGELOG `BREAKING:` line for persisted-state schema change

**Acceptance:**
- Parametrised test across 7 agents: spec → persist → reload → resume → every subclass field survives round-trip
- Test: pre-v0.9 fixture (no schema_version) raises `RunStateSchemaVersionError` with the documented message
- Test: agent_name discriminator correctly hydrates the right subclass
- mypy clean on the new union

### 3. Golden content assertions

**Files:**
- `tests/golden/_helpers.py` (new) — `assert_artifact_exact()`, `assert_qa_within_tolerance(rtol=0.05)`
- `tests/golden/test_<agent>.py` for each of 7 agents — extend
- `examples/<agent>/` fixtures — extended with content snapshots
- `Makefile` — new `update-goldens` target
- `CONTRIBUTING.md` — document `update-goldens` workflow

**Behavior:**
- Helper API enforces split:
  - `assert_artifact_exact(path, fixture_path)` — exact byte match for markdown, JSON-with-fixed-keys, etc.
  - `assert_qa_within_tolerance(actual: dict, fixture: dict, rtol=0.05)` — only for `qa_scores.json` numeric fields (`scores.*`, `average`)
  - Tolerance never applies to text content; signatures enforce this (helper rejects non-numeric input)
- For each agent, golden fixture asserts:
  - (a) `extracted_context.json` keyed values exact
  - (b) primary spec markdown — section headings + required phrases (use exact match against committed fixture; rebuild via `update-goldens`)
  - (c) `qa_scores.json` — within `rtol=0.05` of fixture average + per-dimension
- Pair with existing structural assertions, do not replace
- `update-goldens` make target: `pytest --update-goldens tests/golden/` re-runs all golden tests with fixture-write mode

**Acceptance:**
- All 7 agent golden tests pass against current main with extended assertions
- Deliberately mutate one Founder prompt template → at least one golden assertion fails (smoke proof of regression-catching)
- CONTRIBUTING.md has step-by-step "regenerating goldens" section

### 4. CIO agent fixes (rolled into v0.9.0 PR)

**Files:**
- `agentsuite/agents/cio/agent.py` (`CIOAgentInput` + execute date logic)
- `tests/unit/agents/cio/test_cio.py`

**Behavior:**
- New field `cio_name: str = Field(default="Acting CIO", description="...")` on `CIOAgentInput`; replaces `strategic_priorities.split()[0]` hack
- New optional field `as_of_date: date | None = None`; if `None`, use `datetime.now(tz=timezone.utc).date()` at execute time
- Hardcoded date literals in `cio/agent.py` removed; replaced with `as_of_date` references
- All artifact templates that interpolate dates updated

**Acceptance:**
- Test: two CIO runs invoked with `freezegun` set to different days produce artifacts with different date strings
- Test: `cio_name` survives RunState round-trip (covered by item 2 parametrised test)
- Test: `as_of_date=None` defaults to today; explicit override honored

### 5. Resume-from-failure idempotency test + ADR

**Files:**
- `tests/integration/test_resume_idempotency.py` (new)
- `docs/adr/0007-resume-idempotency.md` (new — see item 6)

**Behavior:**
- Test: drive a Founder run that crashes mid-Stage 4 via injected exception. Persist state. Resume from `execute`. Assert:
  - Stages 1–3 not re-billed (cost_summary deltas == 0 for those stages)
  - Stage 4 picks up from beginning of stage (not mid-stage; AgentSuite is stage-atomic)
  - Stages 5+ run normally
  - Final `cost_summary.json` reflects total cost across both run attempts
- ADR documents the contract: stage-atomic resume, cost preservation, no partial-stage credit

**Acceptance:**
- Test passes with deterministic mock LLM
- ADR reviewed and merged

### 6. ADR backfill (G1)

**Files:**
- `docs/adr/0001-rubric-dimensions.md`
- `docs/adr/0002-runstate-shape.md`
- `docs/adr/0003-retry-timeout-policy.md`
- `docs/adr/0004-mcp-tool-naming.md`
- `docs/adr/0005-cost-cap-vs-telemetry-split.md`
- `docs/adr/0006-no-pypi-distribution.md`
- `docs/adr/0007-resume-idempotency.md` (from item 5)
- `docs/adr/README.md` (index + template)

**Behavior:**
- One paragraph each: context, decision, consequences. Template per [MADR](https://adr.github.io/madr/) shortened.
- Index `docs/adr/README.md` lists all ADRs with one-line summary

**Acceptance:**
- All 7 ADRs merged
- Index links resolve
- Linked from CONTRIBUTING.md ("decisions reference")

### 7. Clean-install verification on tag push

**Files:**
- `.github/workflows/release.yml` — new job `clean-install-check`

**Behavior:**
- Runs on `release` workflow trigger (tag push)
- Matrix: `os: [ubuntu-latest, windows-latest]`, `python: ["3.11", "3.12"]`
- Steps:
  1. Checkout
  2. Extract install commands from `README.md` install block (regex match between `<!-- install:start -->` and `<!-- install:end -->` markers — add markers to README in same PR)
  3. Run extracted commands verbatim in a fresh Python venv
  4. Run extracted commands from `docs/index.html` (different parser, same intent)
  5. `agentsuite --help` and `agentsuite-mcp --help` must exit 0
  6. Diff-check `README` install block against canonical fixture `tests/fixtures/install-block.md` — fail if drifted
- Fail the release on any exit non-zero

**Acceptance:**
- Workflow runs on v0.9.0 tag, matrix all green
- Deliberately corrupt README install command in a test PR → workflow fails (smoke proof)

### v0.9.0 sequencing

```
Day 1-2: Item 2 (RunState union)            ── enables item 5
Day 1-3: Item 3 (golden helpers + fixtures) ── parallel, biggest chunk
Day 2-3: Item 4 (CIO fixes)                 ── parallel
Day 3-4: Item 1 (cost telemetry)            ── after RunState (uses persisted state)
Day 4:   Item 5 (idempotency test + ADR-7)  ── after cost telemetry
Day 4-5: Item 6 (ADR backfill)              ── parallel with item 5
Day 5-6: Item 7 (clean-install verification) ── after all above stable
Day 6-7: Integration, dogfood, tag v0.9.0
```

**Acceptance for v0.9.0 tag:**
- All 7 items merged + green
- v0.9.0 tag triggers clean-install workflow → green
- pytest 0 skipped, 0 deselected (deselected items reviewed and either rolled in or removed)
- `examples/sample-output/founder/` committed with full artifact set + cost_summary.json
- CHANGELOG entry includes BREAKING for state-schema change + cost-cap default change

---

## v0.9.1 — CIO fixes follow-up + Founder rubric audit

**Pulled out of v0.9.0** to keep that release focused on engineering hardening. v0.9.1 is documentation + small polish.

1. **Founder rubric audit one-pager** (`docs/rubric-audit.md`)
   - Side-by-side table: each agent × each dimension. Marked: matched, unique, semantic-overlap-with-X.
   - Decision: keep current 7-vs-9 split, or consolidate elsewhere.
   - No code changes unless the audit produces a clear signal.
   - Acceptance: doc merged, decision recorded; if code change needed, separate PR.

2. **Skipped/deselected pytest items audit**
   - List every skip/deselect remaining post-v0.9.0; either fix or document permanently with rationale.
   - Acceptance: every remaining skip has a paragraph in `docs/test-coverage.md` explaining why.

3. **Bug-bash from auditor backlog**
   - Whatever lands during v0.9.0 review that doesn't make the cut.
   - Acceptance: PR-by-PR.

---

## v0.9.2 — Visual + sample-output docs (P4)

**Goal:** Replace text-only landing experience with screenshots + committed sample run.

**Files:**
- `docs/screenshots/` — new dir with PNGs (capture via OBS or `asciinema → svg-term` for terminal)
  1. `cli-founder-run.png` — terminal showing `agentsuite founder run` end-to-end with stage progress + final JSON
  2. `runs-tree.png` — `tree .agentsuite/runs/<run-id>/` after success
  3. `brand-system-rendered.png` — rendered markdown of `brand-system.md`
  4. `qa-report-rendered.png` — rendered `qa_report.md`
  5. `mcp-tool-list-claude-code.png` — Claude Code surfacing the MCP tools
  6. `kernel-tree.png` — `_kernel/<project_slug>/` after approval
- `examples/sample-output/founder/` — committed full run output (no LLM calls during clone/test; pre-baked artifacts)
- `README.md` — hero screenshot above install block; add screenshot section
- `USER-MANUAL.md` — one screenshot per agent walkthrough
- `docs/index.html` — replace text-only sample with embedded `cli-founder-run.png`

**Acceptance:**
- All 6 screenshots committed and embedded
- `examples/sample-output/founder/` browsable on GitHub without install
- Lighthouse pass on `docs/index.html` (perf + a11y still green)

---

## v1.0.0-rc1 — Release candidate (soft launch)

**Goal:** Tag a candidate; let it bake against own dogfood for 5–7 days before declaring v1.0.0 GA.

**Items:**

1. **Compatibility freeze**
   - All public APIs locked. Any breaking change post-rc1 requires explicit Scott approval.
   - Type stubs (`agentsuite/py.typed` already exists) verified accurate.
   - mypy clean against a downstream consumer (synthesize a small package that imports AgentSuite — fixture in `tests/integration/test_downstream_consumer.py`).

2. **Discussions seeded** (P5)
   - Repo Settings → Discussions enabled.
   - Pinned: "Welcome to AgentSuite v1.0" announcement post.
   - Q&A: 2–3 anticipated questions ("Which provider should I use?", "How do I add an 8th agent?", "What does cost telemetry actually track?") with genuine answers.
   - Ideas: 1–2 roadmap items framed as open questions.
   - Show & Tell: empty, ready for community.
   - Links from README, USER-MANUAL, `docs/index.html`.

3. **"Why AgentSuite" hook in README**
   - One-paragraph value-prop above install block.
   - Hero screenshot (from v0.9.2).
   - 30-second pitch: what it is, who it's for, what makes it different.

4. **Three "good first issue" tickets**
   - Filed but unstaffed; visible in Issues with `good first issue` label.
   - Examples: "Add a screenshot to USER-MANUAL agent X", "Add brief template to agent Y", "Add regression test for behavior Z."

5. **CHANGELOG promotion to 1.0.0-rc1**
   - All `Unreleased` items rolled into v1.0.0-rc1 entry.
   - Pre-release flag on GH release.

6. **Internal dogfood**
   - Run AgentSuite end-to-end against a real Scott project for one full day. Capture screen recording. Note every friction point.
   - Open issues for friction; triage as v1.0.0 blockers vs v1.0.x post-launch.

**Acceptance for rc1 tag:**
- All 6 items done
- pip-audit + SBOM + clean-install matrix all green on rc1
- Dogfood produced 0 v1.0-blocking issues (or all blockers fixed)

---

## v1.0.0 — General availability

**Goal:** Public launch.

**Items:**

1. **Resolve any rc1 blocker issues** discovered during 5–7 day bake.

2. **CHANGELOG promotion** rc1 → 1.0.0.

3. **External launch** (held until here per agreed plan)
   - Show HN: "AgentSuite — seven role-specific reasoning agents for Codex / Claude Code / Cowork"
   - r/LocalLLaMA: focus on Ollama-first local-LLM story
   - MCP Discord: announcement post
   - Each post: link to GH release, landing page, sample-output dir, screencast from rc1 dogfood

4. **Press kit** (`docs/press-kit/`)
   - Hero screenshot, logo (if exists), one-paragraph description, founder quote (Scott).

5. **Tag, sign, ship**
   - `git tag -s v1.0.0` (signed tag for v1.0)
   - GH release with full changelog, signed checksums for wheel + sdist, SBOM
   - Pin announcement in Discussions

**Acceptance for v1.0.0 tag:**
- All rc1 items resolved
- Launch posts live
- Discussions active (≥3 inbound responses within 24h is the success signal; if ≤1, regroup before pushing harder)

---

## Cross-cutting concerns

### Hard rules in effect across the sprint

- **No subagents** (`feedback_no_subagents_inline_only.md` active) — all work inline
- Hard Rule 11 (commit size): tag commits >800 lines with `[LARGE-CHANGE]` etc.
- Hard Rule 12 (watchdog): arm state file on any test/build/CI watch >1 min
- Pre-push: ruff + mypy + pytest ALL THREE before any push
- No skipped tests carried into v1.0 (Hard Rule 4a)
- 6 doc artifacts gate: README, CHANGELOG, CONTRIBUTING, LICENSE, .gitignore, docs/index.html — every release verifies

### Per-release pre-push checklist

For each tag (v0.8.3, v0.9.0, v0.9.1, v0.9.2, v1.0.0-rc1, v1.0.0):
1. `git pull --ff-only`
2. Bump version in: `pyproject.toml`, `agentsuite/__version__.py`, `README.md`, `USER-MANUAL.md`, `docs/index.html`, `docs/troubleshooting.md` (single commit)
3. CHANGELOG entry written + reviewed
4. `bash scripts/verify-release.sh` → ALL CHECKS PASSED
5. Stage + commit
6. Surface tag command for Scott approval
7. Tag + push main + push tag
8. Watch CI to green
9. Verify GH release exists with assets

### Risk register

| Risk | Mitigation |
|---|---|
| pip-audit surfaces unfixable transitive CVE | `[skip-audit]` override token + open issue tracking upstream fix |
| Provider price drift detected during weekly job | Open issue, fix in patch release; existing pricing assertions guard runtime |
| Golden tests too brittle after content extension | Tolerance helper API split (exact vs numeric-only) prevents text drift |
| Discriminated union breaks downstream serializer (e.g. user has custom hook reading `_state.json`) | YAGNI — no known users; loud `RunStateSchemaVersionError` if hit |
| v1.0 launch lands on dead audience (HN miss) | Soft-launch through Discussions + MCP Discord first; HN attempt second |
| Sprint scope creep | Each release has acceptance criteria; new asks → backlog or v1.0.x |

### What's NOT in this plan (deferred to v1.0.x or later)

- Multi-tenancy / API server mode
- Web UI for AgentSuite (CLI + MCP only at v1.0)
- Additional agents beyond the 7 currently shipped
- Per-day cost cap (per-run only at v1.0)
- Per-agent MCP server topology (single MCP server with env-gated enablement only)
- Cloud-hosted provider for AgentSuite itself (it remains a local tool)

---

## Open decisions Scott needs to make

1. **`AGENTSUITE_COST_CAP_USD` default value for v0.9.0** — current default is unknown to me; need confirmed raise target. Suggest **$5.00** as starting point; runs over $5 are unusual for current agent set.
2. **v0.9.2 screenshot capture** — Scott captures, or Claude generates via headless terminal automation? Scott's manual capture probably faster + more authentic.
3. **External launch timing** — held until v1.0.0, agreed. Before launch, confirm: still want HN Show + r/LocalLLaMA + MCP Discord, or different channel mix?
4. **Signed tags from v1.0** — currently unsigned. Switching to GPG-signed for v1.0 + onward? (Recommended for OSS credibility but adds setup friction.)
5. **`good first issue` ticket content** — three placeholder examples in plan; Scott to confirm the actual three before rc1.

---

## Status checkpoints

After each tag, produce a dev report under `dev-reports/<date>-<tag>-shipped.md` matching the v0.8.2 format. The report is the source of truth for what landed; this plan is the forward-looking commitment.
