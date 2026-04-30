# External launch posts (drafts)

Three platforms, three different audiences, three different angles. Drafts only — review and revise before posting. Do **not** post until v1.0.0 GA tag is live; rc1 is internal-bake only.

Posting order recommendation:
1. **MCP Discord first** (smallest, most forgiving audience; surfaces any framing problems early)
2. **r/LocalLLaMA second** (Ollama-first angle; technical audience)
3. **Show HN third** (broadest reach; one-shot — be ready before posting)

If signal from #1 and #2 is weak, hold #3 for a week and revise.

---

## 1. MCP Discord — `#showcase` (or whatever the project-launch channel is)

**Format:** chat-conversational. Not a press release.

> Hey all — long-time lurker, first-time post. Just shipped v1.0 of **AgentSuite** — seven role-specific reasoning agents (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO) that surface as MCP tools in Codex / Claude Code / Cowork.
>
> The MCP angle: each agent is a `<agent>_run` / `<agent>_resume` / `<agent>_approve` triplet. Run produces 26 typed artifacts on disk (brand systems, ADRs, threat models, IT strategy, etc., depending on agent). Approve promotes the run into a `_kernel/<project>/` that downstream agents read. Cost is tracked per stage with a per-run cap.
>
> Provider-agnostic — Anthropic / OpenAI / Gemini / local Ollama. Distributed from GitHub only (no PyPI on purpose; install via `uvx --from git+...` or `pip install ... @ git+...`).
>
> Repo: https://github.com/scottconverse/AgentSuite
> Sample output (committed, no install needed): https://github.com/scottconverse/AgentSuite/tree/main/examples/sample-output/founder
>
> Would love eyes on the MCP wiring specifically — I'm particularly curious whether the tool-name contract (per ADR-0004) holds up against weirder MCP clients. Open issues / discussions / DMs welcome.

**Self-check before posting:**
- Channel rules read? (every Discord has different self-promo limits)
- Repo public? (verify `gh repo view scottconverse/AgentSuite --json visibility`)
- Sample-output link resolves? (paste it into a private browser tab first)

---

## 2. r/LocalLLaMA — Ollama-first angle

**Title:** AgentSuite v1.0 — seven role-specific reasoning agents that run on local Ollama (or Anthropic/OpenAI/Gemini if you prefer)

**Body:**

> Just shipped v1.0 of AgentSuite, a Python package + MCP server I've been building for the operating layer between intent and AI output.
>
> Seven agents (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO) each run the same five-stage pipeline (intake → extract → spec → execute → qa) with a kernel-managed approval step and persist 26 structured artifacts per run. Approved runs promote into a long-lived `_kernel/` directory that downstream agents consume — so the system *accumulates* context instead of starting fresh every time.
>
> **Why this might interest r/LocalLLaMA:**
>
> - Local Ollama is a first-class provider, not an afterthought. Same code path as Anthropic/OpenAI/Gemini; one config flag picks the provider.
> - Zero telemetry, zero phone-home. The kernel writes only to `.agentsuite/` in CWD (configurable). No callbacks.
> - Per-stage cost telemetry (`cost_summary.json` per run) — for Ollama the cost is always $0, but the token counts let you compare token-efficiency across local models.
> - Deterministic mock LLM included for offline development and tests. Useful for writing your own agent against the kernel without burning tokens.
>
> **What you get:**
>
> - 7 agents, 689 tests, golden snapshot coverage, content-aware regressions, full SBOM + pip-audit on every release.
> - 7 ADRs explaining design decisions (rubric shape, RunState contract, retry/timeout policy, MCP naming, cost-cap-vs-telemetry split, no-PyPI distribution choice, resume idempotency).
> - MCP-native — surfaces in Codex, Claude Code, Cowork, or any MCP client. Single server with env-gated agent enablement.
>
> **Recommended local model:** Gemma 2/3 9B+ for Founder/Design (long-form structure), Llama 3 8B+ for Engineering/CIO (technical specs). Anything below 7B drifts on the rubric and is worth a flag for the maintainer.
>
> Repo: https://github.com/scottconverse/AgentSuite
> Browse a real Founder run with no install: https://github.com/scottconverse/AgentSuite/tree/main/examples/sample-output/founder
>
> Happy to answer Qs in comments.

**Self-check before posting:**
- Subreddit rules: no excessive self-promo, must add value. ✓ — this is a build post with technical detail, not a Show HN ad.
- Title under 100 chars? ✓
- Lead with what r/LocalLLaMA cares about (privacy, local-first, no telemetry, provider portability), not the project's general thesis.

---

## 3. Show HN — one shot, broadest reach

**Title:** Show HN: AgentSuite — seven role-specific reasoning agents for Codex / Claude Code / Cowork (under 80 chars to fit HN's title limit)

**First comment** (post immediately to seed conversation):

> Author here. AgentSuite is the operating layer between intent and AI output. Seven agents (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO) walk a deterministic five-stage pipeline (intake → extract → spec → execute → qa) with a kernel-managed approval step, and persist 26 structured artifacts per run. Approved runs promote into a `_kernel/<project>/` directory that downstream agents read.
>
> The thesis: AI tools generate fast but not consistently. Without a reusable brand system, brief library, voice guide, or operational playbook on disk, every new asset re-introduces context and drifts on tone. AgentSuite codifies the *system around* generation — the artifacts, the QA scoring, the stage gates, the kernel promotion — instead of the generation itself.
>
> A few specifics that might be useful for HN:
>
> - **Provider-agnostic** by design. Anthropic / OpenAI / Gemini / local Ollama, one-line switch. Same kernel, same artifacts, same MCP surface.
> - **MCP-native.** The Python library, the CLI, and the MCP server are the same code. Wire into Codex / Claude Code / Cowork via a small TOML/JSON config; no separate daemon, no separate API key path.
> - **Cost telemetry per stage** with a per-run cap (default $5, configurable). Hitting the cap raises a typed exception with the partial `cost_summary.json` already written for audit. ADR-0005 documents the cap-vs-telemetry split.
> - **No PyPI on purpose.** Install is `pip install ... @ git+...` or `uvx --from git+...`. Distribution is GitHub-only with SBOM + pip-audit on every release. ADR-0006 explains why.
> - **Test discipline.** 689 tests, 0 skipped, content-aware golden coverage on all 7 agents, full clean-install matrix on tag. Hard rule: no `pytest.skip` markers in the repo.
> - **Architecture decision records.** 7 ADRs covering rubric shape, RunState schema, retry/timeout policy, MCP naming, distribution, resume idempotency. Read before opening a PR that touches a recorded decision.
>
> Open questions I'd love HN's eyes on:
>
> 1. The compatibility freeze starts at v1.0. The public API surface, `_state.json` schema, MCP tool names, and pipeline stage names are locked. Is the surface I picked the *right* surface? Any gaps that would make downstream typing painful?
> 2. The `_kernel/` promotion mechanism is the load-bearing concept. Is there prior art I should be aware of? I cribbed from Make's pattern target idea but the persistence model is closer to Git's index.
> 3. Eight-agent question: which role would you reach for next? Sales-ops, customer-success, legal, HR — or something else? Voting in the GH Discussions Ideas board.
>
> Repo: https://github.com/scottconverse/AgentSuite
> Browse a real Founder run with no install: https://github.com/scottconverse/AgentSuite/tree/main/examples/sample-output/founder
> Docs landing page: https://scottconverse.github.io/AgentSuite

**Self-check before posting:**
- HN doesn't allow editing titles after submission. Title checked? ✓
- First comment posted within 30 sec of submission? Critical — HN ranks comment count.
- Repo public, releases live, sample-output link resolves? Verify all three.
- Be ready to answer comments for the next 4-6 hours. HN engagement window is short.

**HN-specific risks:**
- "Yet another AI agent framework" pushback. **Response template:** "Fair concern — the framework is one agent. The product is the seven specific output contracts and the kernel-promotion mechanism. The kernel is ~5 KLOC; if it disappeared and you only had the seven agents, you'd still have the value."
- "No PyPI = no install" pushback. **Response template:** "`pip install ... @ git+...` is one command and pip handles dependency resolution normally. ADR-0006 explains the trade. PyPI namespacing has its own pathologies; we chose explicit-source over implicit-mutable."
- "How is this different from <X>?" — answer specifically per X, don't deflect. The 26-artifact persistence + `_kernel/` promotion is what's different from generation-only tools.

---

## Posting checklist (use across all three)

- [ ] v1.0.0 GA tag is live (not rc1)
- [ ] GH release is published, NOT marked pre-release
- [ ] Repo is public + Discussions enabled + Issues enabled
- [ ] Three good-first-issue tickets are filed
- [ ] Sample-output link resolves in private browser
- [ ] Docs landing page resolves
- [ ] You have ~4 hours blocked to monitor responses
- [ ] CHANGELOG entry for 1.0.0 is on `main`, not still on a branch
- [ ] First-comment for HN is in your clipboard before submission
