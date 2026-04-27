# Next-Sprint Watchlist — AgentSuite v0.7.0 Audit

**Generated:** 2026-04-27  
**Purpose:** Forward-looking items — not acute bugs, but structural debts, scaling concerns, and design decisions that will cost more to fix later if not addressed soon.

---

## W1 — Founder rubric has 7 dimensions, not 9
**Surfaced by:** Principal Engineer (C-003) | **Horizon:** v0.8.0

All 6 non-Founder agents have 9 rubric dimensions. Founder has 7 (`reusability`, `brand_consistency`, `claims_grounded`, `voice_fit`, `template_specificity`, `goal_alignment`, `anti_genericity`). The two missing dimensions likely should be `constraint_adherence` (whether legal/brand constraints from `FounderInputs.constraints` are honored) and `completeness` (whether all 9 spec artifacts are substantive).

The QA math still works — weighted average over 7 dimensions vs 9 doesn't break the 7.0 threshold semantics. But the Founder's quality bar is weaker than every other agent. A brand run that passes Founder QA has been evaluated on 2 fewer axes than a design or product run.

**Action:** Add 2 rubric dimensions to `agentsuite/agents/founder/rubric.py`. Update any test that snapshots the rubric's dimension count.

---

## W2 — Ollama is a hard dependency, should be optional
**Surfaced by:** Principal Engineer (m-001) | **Horizon:** v0.8.0

`pyproject.toml:29` lists `ollama>=0.4` as a required dependency. Ollama requires a local daemon. Users who only use cloud providers (Anthropic, OpenAI, Gemini) must install the ollama package even if they never use it. 

`agentsuite/llm/ollama.py` already has a friendly `ImportError` guard — the package install shouldn't be required.

**Action:** Move `ollama>=0.4` from `[project.dependencies]` to `[project.optional-dependencies]` under `[ollama]`. Document `pip install agentsuite[ollama]` for local-LLM users.

---

## W3 — QA pass/fail exact-boundary behavior is unverified
**Surfaced by:** Test Engineer (C-3) | **Horizon:** next test sprint

`QARubric.score()` uses `passed = average >= pass_threshold`. The comparison operator at exactly 7.0 is `>=` (passes). No test pins this behavior. If the operator is ever changed (or the threshold logic refactored), no test would catch it until a live run stalls in revision loops.

**Action:** Add to `tests/unit/kernel/test_qa.py`:
```python
def test_qa_boundary_exactly_at_threshold():
    """Score exactly at threshold should pass (>=, not >)."""
    rubric = QARubric(dimensions=[RubricDimension(name="a", weight=1.0)], pass_threshold=7.0)
    result = rubric.score({"a": 7.0}, [])
    assert result.passed is True

def test_qa_boundary_just_below_threshold():
    rubric = QARubric(dimensions=[RubricDimension(name="a", weight=1.0)], pass_threshold=7.0)
    result = rubric.score({"a": 6.99}, [])
    assert result.passed is False
```

---

## W4 — HardCapExceeded propagation through stage loop is untested
**Surfaced by:** Test Engineer (M-6) | **Horizon:** next test sprint

`CostTracker.add()` correctly raises `HardCapExceeded` when the cost cap is hit. But no integration test verifies that this exception propagates cleanly through `BaseAgent._drive()`. A poorly placed `except Exception` in the stage loop could silently swallow it. A user who sets `AGENTSUITE_COST_CAP_USD=0.001` and runs a real agent would get either a clean error or a silent infinite loop — untested.

**Action:** Add to `tests/integration/test_founder_pipeline.py`:
```python
def test_pipeline_hard_cap_raises(tmp_path):
    """HardCapExceeded propagates cleanly through the stage loop."""
    import os
    os.environ["AGENTSUITE_COST_CAP_USD"] = "0.000001"
    # mock LLM with non-zero cost response
    # assert HardCapExceeded is raised, not caught
```

---

## W5 — ArtifactWriter has no path traversal guard
**Surfaced by:** Principal Engineer (C-002) | **Horizon:** pre-public-MCP-launch

`agentsuite/kernel/artifacts.py:51-52` constructs artifact paths as `self.run_dir / relative_path` with no containment check. All current callers pass literal strings — no active exploit. But the MCP tool surface (`mcp_tools.py` in all 7 agents) exposes artifact operations to external callers. As the MCP API surface grows, a caller passing `"../../etc/other_run/spec.md"` as a relative path would write outside `run_dir`.

**Action:** After constructing `full`, add:
```python
full = (self.run_dir / relative_path).resolve()
if not str(full).startswith(str(self.run_dir.resolve())):
    raise ValueError(f"Artifact path escapes run_dir: {relative_path}")
```

---

## W6 — CostTracker cost lost when stage raises mid-pipeline
**Surfaced by:** Principal Engineer (M-002) | **Horizon:** v0.8.0

If a stage raises mid-pipeline (e.g., `ConsistencyCheckFailed` after 7 of 9 spec artifacts are generated), the accumulated cost for that partial stage is lost. `RunState.cost_so_far` is only updated after a successful stage completes. A run that spends $1.50 before a consistency-check failure reports `cost_so_far = $0.00` in the saved state.

**Action:** Wrap the stage loop in `BaseAgent._drive()` with try/except that updates `state.cost_so_far` from the tracker and saves state before re-raising.

---

## W7 — Golden tests assert existence and non-emptiness, not structure
**Surfaced by:** Test Engineer (M-2) | **Horizon:** next test sprint

Golden tests verify that artifact files exist and are non-empty. They do not assert that JSON artifacts (`qa_scores.json`, `extracted_context.json`, `consistency_report.json`) contain expected top-level keys, or that markdown artifacts contain required section headings. A structural regression — key rename, section removal — is invisible until a live run.

**Action:** Add structure assertions to golden tests:
```python
import json
scores = json.loads((run_dir / "qa_scores.json").read_text())
assert "scores" in scores
assert "passed" in scores
assert "average" in scores
```

---

## W8 — `agentsuite/__init__.py` exports nothing useful
**Surfaced by:** Principal Engineer (N-001) | **Horizon:** v0.8.0

`from agentsuite import FounderAgent` fails. Users must know the full import path (`agentsuite.agents.founder.agent.FounderAgent`). The library has no top-level re-exports. This is a developer-experience gap for users wiring agents into their own code.

**Action:** Add to `agentsuite/__init__.py`:
```python
from agentsuite.agents.founder.agent import FounderAgent
from agentsuite.agents.design.agent import DesignAgent
# ... all 7 agents
from agentsuite.llm.mock import MockLLMProvider
__all__ = ["FounderAgent", "DesignAgent", ..., "MockLLMProvider"]
```

---

## W9 — No visual content anywhere (landing page, README, USER-MANUAL)
**Surfaced by:** UI/UX Designer (M5) | **Horizon:** marketing sprint

The landing page, README, and USER-MANUAL contain zero screenshots, terminal output examples, or architecture diagrams in rendered form. A developer evaluating AgentSuite has no way to form a visual mental model of what they would get. The README has an ASCII-art architecture diagram that would be better as a Mermaid or SVG rendering.

**Action (minimum):** Add one 10-20 line excerpt of real `brand-system.md` output to the landing page as a code block. Add a terminal screenshot or GIF of a `founder run` to the README. Regenerate the landing page architecture diagram as inline SVG.

---

## W10 — GitHub Discussions not yet seeded
**Surfaced by:** All roles (referenced in pre-push checklist) | **Horizon:** community sprint

GitHub Discussions is a required doc artifact per project standards. It has not been enabled on the repository. No discussion posts exist. The project has no community presence, which makes the landing page's "Issues + discussion welcome" footer a dead end.

**Action (manual — Scott must perform):**
1. Enable Discussions in GitHub repo Settings → General → Features → Discussions
2. Create posts in these categories:
   - **Announcements:** Welcome/launch post with agent summary + status
   - **Q&A:** 2-3 seeded questions (e.g., "How do I configure multiple providers?", "What's the difference between spec artifacts and brief templates?")
   - **Ideas:** 1-2 roadmap ideas as open questions (v0.8 agent domain, Windows installer)
   - **General:** Community welcome post

---

## W11 — Gemini API key precedence inverted between resolver and provider
**Surfaced by:** Principal Engineer (N-006) | **Horizon:** v0.8.0

`agentsuite/llm/resolver.py` checks `GEMINI_API_KEY` first, then `GOOGLE_API_KEY`.  
`agentsuite/llm/gemini.py` checks `GOOGLE_API_KEY` first, then `GEMINI_API_KEY`.

If a user has both set, the resolver picks the provider based on `GEMINI_API_KEY` presence, but the provider initializes using `GOOGLE_API_KEY`. If they hold different values, the resolver and provider make decisions based on different keys.

**Action:** Standardize both to prefer `GEMINI_API_KEY` first (it's the more specific one), or document the priority explicitly.

---

## W12 — RunState subclass fields unverified in serialization round-trip tests
**Surfaced by:** Test Engineer (M-3) | **Horizon:** next test sprint

`test_state_store.py` asserts `loaded.run_id` and `loaded.stage` after round-trip but does not verify that agent-specific subclass fields (e.g., `organization_name` for `CIOAgentInput`, `risk_domain` for `TrustRiskAgentInput`) survive deserialization. If Pydantic drops subclass-specific fields during JSON round-trip, resume operations would silently fail to reconstruct the typed input.

**Action:** Add a round-trip test that verifies agent-specific fields survive StateStore save/load.

---

## W13 — Deprecation warning in `google.genai.types` (Python 3.17 future risk)
**Surfaced by:** Test Engineer (suite warning) | **Horizon:** Python 3.17 migration

`DeprecationWarning: _UnionGenericAlias is deprecated in Python 3.11 and will be removed in Python 3.17` appears in the Gemini SDK. Not an AgentSuite code issue, but AgentSuite ships with `google-genai>=1.0` and will need a minimum version bump when Google releases a compatible SDK version.

**Action:** Track `google-genai` releases; update minimum version when the deprecation is resolved. Add to CI to fail on DeprecationWarnings in owned code.
