# Handoff — v1.0.3 Prep (2026-04-30)

> Read this first. Then read `~/.claude/projects/C--Users-scott-OneDrive-Desktop-Claude/memory/handoff_2026-04-30-agentsuite-v1.0.3-prep.md` for full detail.

## TL;DR

v1.0.2 shipped (commits `16cebe8` + `e391336` + `5e795da`, tag `v1.0.2`, GitHub Release "Latest"). 805 tests, ruff + mypy clean. Then a $0.51 live test against real Anthropic Sonnet surfaced **two systemic bugs that 805 mock tests did not catch**.

Fix both, resume the live test, validate kernel promotion + cost provenance, ship as v1.0.3.

## Tasks

### 1. Fix CR-101 — json.loads not robust to markdown fences (Critical)

**Symptom:** `json.loads(response.text)` crashes with `JSONDecodeError: Expecting value` when Claude wraps response in ```json fences or adds a one-line preamble (real Sonnet behavior even with `"Return ONLY JSON"` system prompt).

**Sites:** 21 across all 7 agents:
- `agentsuite/agents/{founder,design,product,engineering,marketing,trust_risk,cio}/stages/extract.py` (~line 66–79)
- `.../stages/qa.py` (~line 52–53)
- `.../stages/spec.py` (~line 95–148, search for `consistency_response`)

**Fix:**
1. Create `agentsuite/llm/json_extract.py` — `extract_json(text: str) -> Any` that strips leading/trailing whitespace, removes markdown code fences if present, then calls `json.loads`. Raises clean `ValueError` if still unparseable.
2. Replace 21 callsites: `json.loads(response.text)` → `extract_json(response.text)` (and same for `consistency_response.text`).
3. Add `tests/unit/llm/test_json_extract.py` covering: pure JSON, markdown-fenced JSON (with/without `json` lang tag), JSON with leading prose, JSON with trailing prose, both, malformed (raises). 8–10 cases.

### 2. Fix CR-102 — Cost provenance lost (Major)

**Symptom:** `cost_summary.json` shows `"model": null` and `"provider": null` per stage despite real Sonnet pricing being applied correctly.

**Where the data is:** `LLMResponse.model` is populated by every provider. `Cost(model=...)` accepts it. Stages aren't passing it through.

**Fix:**
1. In every stage's `ctx.cost_tracker.add(Cost(...))` call (same 21 sites as CR-101 plus probably the execute stages), add `model=response.model`.
2. Set provider once on `CostTracker.__init__` — read `agentsuite/kernel/cost.py` to pick the cleanest hook.
3. Add a unit test asserting `cost_summary.json["stages"][0]["model"]` and `["provider"]` are non-null after a single mocked stage run.

### 3. Verify with the existing live-test resume

Run dir state preserved at: `C:\Users\scott\OneDrive\Desktop\Claude\.agentsuite-livetest-2026-04-30\runs\livetest-3\`

- Already-spent: $0.508 across extract + spec stages
- 11 spec artifacts on disk (95KB content)
- Crashed at `agentsuite/agents/founder/stages/spec.py:112` consistency check JSON parse

After CR-101 + CR-102 land, ask Scott for a fresh `ANTHROPIC_API_KEY`, then:

```bash
export ANTHROPIC_API_KEY='<fresh>'
export AGENTSUITE_OUTPUT_DIR="/c/Users/scott/OneDrive/Desktop/Claude/.agentsuite-livetest-2026-04-30"
export AGENTSUITE_LLM_PROVIDER=anthropic
python -m agentsuite.cli founder resume --run-id livetest-3 --stage spec
```

Estimated additional cost: $0.40–0.60.

After resume completes:
- Verify `cost_summary.json` now has non-null `model` and `provider` per stage (CR-102 evidence)
- Verify spec consistency report parsed cleanly (CR-101 evidence)
- Approve: `agentsuite founder approve --latest --approver scott --project-slug livetest-2026-04-30`
- Verify `_kernel/livetest-2026-04-30/` has the right artifacts
- Compare `cost_summary.json` total against the Anthropic dashboard line-by-line

### 4. Ship v1.0.3

1. Bump `pyproject.toml` + `agentsuite/__version__.py` + `README.md` 1.0.2 → 1.0.3
2. Add CHANGELOG `[1.0.3] - 2026-04-30` entry
3. Run full release gate (ruff, mypy --strict, pytest)
4. Commit, push to main
5. Tag `v1.0.3`, push tag
6. `gh release create v1.0.3 --title "v1.0.3" --notes ...`

## Critical context

- **Mocks pass, prod doesn't.** 805 tests with mocked LLM responses → all pass. Real Sonnet → spec stage crashes. Don't trust "tests pass" without live validation.
- **The audit predicted this.** W-06 ("golden tests verify structure, not prompt quality") and W-01 ("blast-radius discipline") in `dev-reports/audit-AgentSuite-2026-04-30-v102/next-sprint-watchlist.md` — both confirmed empirically.
- **Bundle CR-101 + CR-102 in one release.** Both are runtime-data-from-LLM failures with the same root-cause class. Splitting them ships the same systemic-fix pattern twice — exactly the W-01 anti-pattern.

## Already done (do NOT redo)

- ✅ v1.0.2 release closed — tag pushed, GitHub Release published, CHANGELOG dated
- ✅ All 6 doc artifacts present
- ✅ Audit packages on disk in `dev-reports/audit-AgentSuite-2026-04-30-v102/`
- ✅ `agentsuite/agents/_common.py` validation helpers in place — use them, don't recreate

## In your way

- Live test artifact dir outside AgentSuite repo at `/c/Users/scott/OneDrive/Desktop/Claude/.agentsuite-livetest-2026-04-30/` — Scott already approved. If permission denials reappear, ask once.
- Hard Rule 10 (subagent obligation) and Hard Rule 12 (test-watchdog) hooks active. Plan parallel subagents for non-overlapping scopes.
