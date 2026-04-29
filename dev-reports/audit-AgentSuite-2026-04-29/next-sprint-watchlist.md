# v1.x Watchlist (next-sprint and beyond)

**Source:** Audit-team pass against `v1.0.0` at `9540957`, dated 2026-04-29.
**Scope:** Majors that are structural / require cross-team or product decisions, plus design-debt items that are not acute now but will get worse with growth. Acute Majors are in [`sprint-punchlist.md`](sprint-punchlist.md).

These items do not block v1.0.1. They belong in v1.1 sprint planning, the v1.0.x backlog, or as Discussions Ideas posts depending on shape.

---

## Architecture & engineering watchlist

### W-01 — Cassette discipline: real-provider integration coverage
**Source:** TEST-001 (Critical, deferred to watchlist via punchlist option (b))
**Why watchlist not punchlist:** Re-recording 7 agents x 4 providers cassettes is a multi-day spike, requires real LLM credits ($30-50 budget), and makes CI brittle to provider response-shape changes. Worth doing, not worth rushing.
**Decision needed:** When v1.1 plans land, decide between (a) full cassette tier, (b) live-tier only at GA, or (c) periodic cassette refresh on a quarterly cadence.
**Pre-work:** Spike with one agent + one provider in v1.0.x to estimate the recording effort and CI flake risk.

### W-02 — Live tier expansion to all 7 agents
**Source:** TEST-002 (Critical, deferred — paired with W-01)
**Why watchlist:** Same reasoning as W-01. Live tier is gated to v0.X.0 / GA tags with $10 cap; expanding to 7 x 4 providers blows the cap unless cap is raised or providers are matrixed.
**Decision needed:** Cap policy. $10 / GA is comfortable for 1 agent x 1 provider; 7 x 4 is closer to $80 per GA.

### W-03 — Concurrent-run behavior on the same `output_root`
**Source:** ENG-006 (Major, deep-dive)
**Why watchlist:** No two-process locking on `.agentsuite/runs/<run-id>/`. Two `agentsuite founder run --run-id same` processes will race the state-file writer. v1.0.x users will not hit this; v1.1 multi-tenant or CI-parallel use will.
**Decision needed:** File-lock library, lock-free design (UUID run-ids and refuse explicit dup), or out-of-scope for v1.0.x — enforce single-process via documentation.

### W-04 — Cost provenance hardening (model-alias normalization)
**Source:** ENG-002 (Critical, partial fix in punchlist; full fix is structural)
**Why watchlist:** v1.0.1 normalizes model strings at the cost-lookup site. The architectural fix is a single canonical model-id type that pricing, providers, and telemetry all share. Worth a v1.1 ADR-0008 before code lands.

### W-05 — Per-day cost cap (per Discussions Ideas seed)
**Source:** Roadmap; ADR-0005 framing
**Why watchlist:** Designed in `docs/community/discussions-seeds.md` as an Ideas post. Per-day requires a date-keyed accumulator and migration discipline beyond v1.0 schema.
**Decision needed:** Community signal from Discussions before committing engineering.

---

## UX / DX watchlist

### W-06 — CLI progress telemetry (post-stub fix)
**Source:** UX-006 + QA-005 (Critical fixed in v1.0.1 stub form; full design for v1.1)
**Why watchlist:** v1.0.1 ships a basic stage-complete line on stderr. v1.1 should consider richer progress: token/sec ticker, partial-output streaming, cost-running display, --quiet vs --verbose vs --progress=<json|tty> flag matrix. Design before build.

### W-07 — MCP tool surface for 6 of 7 agents
**Source:** QA-007 supplement
**Why watchlist:** Currently only Founder has full MCP tool registration; the other 6 are CLI-only despite README implying parity. Either implement registration for the other 6 (substantial work; v1.1 minor) or document the asymmetry honestly in v1.0.1 (Critical-grade fix in CR-03).

### W-08 — Cleanroom test reality check
**Source:** TEST-007 (Major)
**Why watchlist:** `scripts/run-cleanroom.sh` runs a full kernel pass under mock LLM but does not exercise the real install flow that a new user takes (`pip install ...@git+...`, then `agentsuite founder run`). Worth promoting cleanroom from "kernel smoke" to "actual user happy path."

### W-09 — Documentation sync rule mechanization
**Source:** DOC-014 (Major)
**Why watchlist:** Project standard requires updating all 6 doc artifacts on every push. Today it is enforced by self-discipline + verify-release.sh. Could be enforced by a CI job that diffs touch-area against doc-touch-area and warns. v1.1 maintenance investment.

---

## Test discipline watchlist

### W-10 — Mutation testing
**Source:** TEST-008 (Minor -> Major if v1.0 takes off)
**Why watchlist:** mutmut not in CI. The 689 tests pass; coverage looks good; but mutation score (which assertions actually catch bugs) is unknown. Worth a v1.1 spike to pick a mutation tool and establish baseline. Do not gate releases on it until baseline is established.

### W-11 — Snapshot regeneration cadence
**Source:** TEST-005 (Minor -> Major if golden tests ossify)
**Why watchlist:** Goldens are byte-stable under deterministic mock; that is a feature. But it means a content-relevant prompt change will silently produce a passing test if the assertion is structural. The content-aware tests (assert_artifact_exact) catch most of this. Watch for ossification on the brief-template-library tests.

---

## Product / community watchlist

### W-12 — 8th agent vote (per Discussions Ideas seed)
**Source:** Roadmap; `docs/community/discussions-seeds.md` Idea 1
**Why watchlist:** Sales-ops? Customer-success? Legal? HR? Wait for community signal before committing. Do not ship in v1.1 without >=5 votes for a single candidate.

### W-13 — GPG-signed tags
**Source:** Roadmap; deferred at rc1
**Why watchlist:** OSS credibility plus reproducible-release argument. ~30 min one-time setup. Tag this for v1.1.0 cut-over. v1.0.x patches stay unsigned.

### W-14 — Press-kit logo
**Source:** `docs/press-kit/README.md` notes "AgentSuite has no logo at v1.0"
**Why watchlist:** Visual identity is fine without a logo for v1.0; if the project takes off, a logo helps press coverage. Not engineering work; assign to a designer or open a Discussion.

---

## Polish & hygiene (batch as one v1.0.x sprint or roll into v1.1)

These are Minor/Nit items that accumulate. Worth one batched sweep but not individually.

- DOC-008 — README pip-install command style mismatch with USER-MANUAL
- DOC-010 — Inconsistent code-fence languages across docs (`bash` vs `sh` vs `console`)
- ENG-007 — Some `# type: ignore` comments without explanation
- ENG-008 — `httpx` timeout values inconsistent across providers
- TEST-009 — Test names mix snake_case and verb-first conventions
- UX-007 through UX-013 — minor copy/voice tweaks across surfaces (see UX deep-dive)
- QA-009 — `agentsuite founder resume` subcommand mentioned in ADR-0007 but not registered in CLI

---

## Decisions needed before v1.1 cut

1. **W-01 / W-02:** Cassette and live-tier strategy + GA cost cap. Engineering + maintainer.
2. **W-03:** Concurrent-run policy. Engineering + ADR-0008.
3. **W-05 / W-12 / W-13:** Per-day cap, 8th agent, signed tags. Maintainer + community signal.
4. **W-09:** Doc-sync mechanization investment. Maintainer.

The rest can land iteratively without a big-bang decision.
