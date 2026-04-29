# GitHub Discussions seed content (v1.0.0-rc1)

This page is a draft of the seed posts for AgentSuite's GitHub Discussions board. **Discussions must be enabled in repo Settings → General → Features → Discussions before any of these can be posted.** Once enabled, paste each block into the noted category. Edit freely before posting — these drafts are starting points, not final copy.

Tone: human, conversational, maintainer-excited. No press-release voice, no bot phrasing.

---

## Announcements — Welcome / Launch (PIN this)

**Title:** Welcome to AgentSuite — and what's coming next

> Hi all — if you found this repo, you're either looking for a way to wire AI agents into Codex / Claude Code / Cowork, or you got linked from somewhere. Either way, glad you're here.
>
> AgentSuite is seven role-specific reasoning agents (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO) that take vague intent and produce structured, reusable artifacts — brand systems, brief libraries, voice guides, ADRs, IT strategies, threat models, and more. Each agent walks a deterministic six-stage pipeline (intake → extract → spec → execute → qa → approval), persists 26 artifacts to disk, and promotes approved output into a `_kernel/` that downstream agents read. The output is a *system*, not a one-off.
>
> Where it is: v1.0.0-rc1 (release candidate). The 7 agents are shipped, golden-tested, and content-snapshot covered. Provider-agnostic (Anthropic / OpenAI / Gemini / local Ollama). MCP-native — the same code surfaces as a CLI, Python library, and MCP server.
>
> What I'd like from you: try it on a real project, file issues for anything that breaks, and tell me what's missing. The roadmap below is a starting point, not a plan written in stone — community feedback shapes it.
>
> **Roadmap candidates** (vote with reactions on the Ideas posts):
> - 8th agent (Sales-ops? Customer-success? Legal? Other?)
> - Per-day cost cap in addition to per-run
> - Web UI in addition to CLI + MCP
> - Multi-tenant API server mode
>
> Thanks for being here on day one.

---

## Q&A — anticipated questions (3 seeds)

### Q1: "Which provider should I use?"

**Title:** Which provider should I use — Anthropic, OpenAI, Gemini, or Ollama?

> All four work, with different trade-offs:
>
> - **Anthropic Claude** — best long-form structured output (the artifacts are markdown specs; Claude excels here). Use the `[anthropic]` extra. Costs ≈ $0.10–0.30 per Founder run.
> - **OpenAI GPT** — good general performance, large context. Use `[openai]`. Costs ≈ $0.15–0.40 per Founder run.
> - **Google Gemini** — competitive on long context, fastest of the three. Use `[gemini]`. Costs ≈ $0.05–0.20 per Founder run.
> - **Local Ollama** — zero cost per run, full privacy, requires a daemon and a pulled model (Gemma 4 / Llama 3.x / Qwen recommended). Use `[ollama]`. Wall time depends on hardware; expect minutes per stage on consumer GPUs.
>
> The provider-agnostic interface is intentional — switching is a one-line config change in your MCP env or CLI flag. There is no "right" choice; pick what your stack already uses or what you're willing to pay for.
>
> See `docs/USER-MANUAL.md` for cost telemetry detail (every run produces `cost_summary.json` with per-stage breakdown).

### Q2: "How do I add an 8th agent?"

**Title:** How do I add an 8th agent (or any custom agent)?

> Short version: subclass `BaseAgent`, build a `QARubric`, register, and ship.
>
> Long version is in [`CONTRIBUTING.md`](../CONTRIBUTING.md) under "Adding a new agent" — the seven-step recipe. Roughly:
>
> 1. Create `agentsuite/agents/<name>/` with `agent.py`, `input_schema.py`, `rubric.py`, `prompts/`, and `stages/`.
> 2. Subclass `BaseAgent` and implement `stage_handlers()` for `intake`, `extract`, `spec`, `execute`, `qa`. The kernel handles `approval` and state persistence.
> 3. Build a domain-specific `QARubric` with 7–9 dimensions. See `docs/rubric-audit.md` for what makes a dimension "carry signal."
> 4. Add prompt templates in `prompts/*.jinja2` (StrictUndefined — fail loudly on missing variables).
> 5. Register in `agentsuite/agents/registry.py`.
> 6. MCP wiring in `<name>/mcp_tools.py`.
> 7. Tests: full unit + golden snapshot + integration.
>
> If you build one and want it upstream, open a PR — but a fork or out-of-tree agent is also fine. The kernel doesn't know or care whether the agent ships in this repo.

### Q3: "What does cost telemetry actually track?"

**Title:** What does the per-run `cost_summary.json` actually track?

> Every run writes `.agentsuite/runs/<run-id>/cost_summary.json` with per-stage cost breakdown:
>
> ```json
> {
>   "run_id": "run-...",
>   "agent": "founder",
>   "provider": "anthropic",
>   "model": "claude-sonnet-4-5",
>   "stages": [
>     {"stage": "intake",  "input_tokens": 1234, "output_tokens": 567,  "cost_usd": 0.0123},
>     {"stage": "extract", "input_tokens": ...},
>     ...
>   ],
>   "total_input_tokens": 12345,
>   "total_output_tokens": 6789,
>   "total_cost_usd": 0.234,
>   "cap_usd": 5.00,
>   "cap_remaining_usd": 4.766
> }
> ```
>
> Token counts come from the provider's response (no estimation). Cost is `tokens × pricing[provider][model]` from `agentsuite/llm/pricing.py`. The cap is enforced per run; hitting the cap raises `HardCapExceeded` and the partial `cost_summary.json` is preserved for audit. ADR-0005 explains the cap-vs-telemetry split.

---

## Ideas / Feature Requests — roadmap candidates (2 seeds)

### Idea 1: 8th agent — which role?

**Title:** What 8th agent would you actually use?

> Seven shipped: Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO. The kernel handles 8+ without code changes — the question is which role would you reach for first.
>
> Candidates I've thought about:
> - **Sales-ops** (ICP profile, sales playbook, objection library, pricing rationale)
> - **Customer-success** (onboarding flow, escalation runbook, churn-signal catalog)
> - **Legal** (terms-of-service drafting, privacy-policy generation, vendor-contract review)
> - **HR / People-ops** (job-spec library, interview-rubric set, perf-review templates)
>
> 👍 the candidate(s) you'd use. Open with your own pitch if none of those fit. No commitment — voting helps me prioritize.

### Idea 2: Per-day cost cap

**Title:** Should we add a per-day cost cap in addition to per-run?

> v1.0 ships with a per-run cap (`AGENTSUITE_COST_CAP_USD`, default $5). Some users have asked for a per-day cap on top — bullets:
>
> - **Pro:** protects against runaway loops or repeated experimentation
> - **Con:** more state to track, requires a date-keyed accumulator, trickier to implement correctly across resume scenarios
>
> If you'd find this useful, 👍 here. If you've already wired your own per-day cap externally and the per-run is enough, 💬 with your setup. I'm gathering signal before committing engineering time.

---

## Show and Tell — empty, ready for community

(No seed post. Leave the category empty for users to populate.)

---

## General — community pointers (PIN this)

**Title:** Pointers for getting help, contributing, and reading the docs

> Quick links:
>
> - 📖 [`README.md`](../README.md) — install + 5-minute quick start
> - 📘 [`docs/USER-MANUAL.md`](../USER-MANUAL.md) — full walkthrough for non-technical readers
> - 🛠️ [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — dev setup, test infrastructure, adding agents
> - 🏗️ [`docs/adr/`](../adr/) — architecture decision records (rubric shape, RunState contract, retry policy, MCP naming, etc.)
> - 🧪 [`examples/sample-output/founder/`](../../examples/sample-output/founder/) — a complete real Founder run, browse without installing
> - 🐛 [Issues](https://github.com/scottconverse/AgentSuite/issues) for bugs, [Discussions Q&A](.) for questions
>
> Three issues marked `good first issue` are filed if you want a small place to start. Code review on every PR; CI runs golden tests, content-aware snapshots, and a fresh-clone install matrix on tag. Talk to me here or in PRs — I read everything.
