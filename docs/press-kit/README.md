# AgentSuite Press Kit

Materials for journalists, podcasters, conference organizers, and anyone writing about AgentSuite. Everything here is freely usable under the project's MIT license. No prior approval needed.

If you need something not in this kit — high-res renders, custom visualizations, an interview, a quote, a demo recording — open a [Discussion](https://github.com/scottconverse/AgentSuite/discussions) tagged `press` or email the maintainer (contact in repo metadata).

---

## One-liner

> AgentSuite is seven role-specific reasoning agents that turn vague intent into reusable operating artifacts — locally, with any LLM provider, surfaced as MCP tools.

## Two-sentence description

> AgentSuite codifies the operating system around AI generation. Seven agents (Founder, Design, Product, Engineering, Marketing, Trust/Risk, CIO) each walk a deterministic five-stage pipeline (intake → extract → spec → execute → qa) with a kernel-managed approval step, persist 26 artifacts to disk, and promote approved output into a `_kernel/` that downstream agents read.

## Five-paragraph description

> Modern AI tools generate fast. They do not generate consistently. Without a reusable brand system, brief library, and voice guide, every new asset re-introduces context, drifts on tone, and slowly turns into generic SaaS copy. AgentSuite is the operating layer between intent and output — the *system around* generation, not the generation itself.
>
> Seven role-specific reasoning agents ship at v1.0: a Founder agent that produces brand systems and brief templates from voice samples and goals; a Design agent that lifts brand fidelity into asset specs; Product, Engineering, Marketing, Trust/Risk, and CIO agents each producing 9 spec artifacts and 8 reusable brief templates in their domain. Every agent walks the same five-stage pipeline (intake → extract → spec → execute → qa) with a kernel-managed approval step, so an operator's mental model stays the same across roles.
>
> Output is structured and on disk. Every run produces a versioned `_state.json`, a per-stage `cost_summary.json`, a `qa_report.md` with rubric scores, and a typed Python API surface that downstream tooling can read. Approved runs promote into a long-lived `_kernel/<project>/` directory that the next run consumes — so context compounds instead of evaporating.
>
> Provider-agnostic by design: Anthropic Claude, OpenAI GPT, Google Gemini, or local Ollama. Cost is tracked per stage, capped per run, and previewable before approval. Privacy-respecting (no telemetry, no callbacks home). MCP-native — the same code surfaces as a CLI, a Python library, and an MCP server you can wire into Codex, Claude Code, or Cowork without a separate process.
>
> Open source, MIT-licensed, distributed from GitHub only (no PyPI by design). v1.0.0 ships after a 5–7 day dogfood bake from rc1, with seven agents, 689 tests, content-aware golden coverage, full SBOM and pip-audit on every release, a deterministic mock LLM for offline development, and a committed `examples/sample-output/founder/` directory so prospective adopters can browse a real run on GitHub without installing anything.

## Founder quote

> *(Scott — drop in your preferred quote here. Suggested seeds:)*
>
> **Option A — practical:** "AI tools that generate one-off content miss the actual operating problem: every output is a snowflake. AgentSuite makes the system reusable — your brand, your briefs, your voice — instead of regenerating context every time."
>
> **Option B — pointed:** "There's no shortage of agents that can write copy. There's a shortage of agents that can produce something a downstream agent can read. AgentSuite is the second kind."
>
> **Option C — origin:** "I built this because I was tired of every AI session starting from scratch. The seven agents are the smallest set that covers the operating arc — from founder voice down to CIO governance — without the surface getting too thin to be useful."

## At-a-glance facts

- **License:** MIT
- **Distribution:** GitHub only (no PyPI by design — see ADR-0006)
- **Language:** Python 3.11+
- **Package size:** ~190 KB wheel, ~95 KB sdist
- **Dependencies:** 5 runtime (pydantic, tenacity, typer, httpx, jinja2) + 1 optional per provider
- **Test count:** 689 (default invocation), 0 skipped, 3 deselected (cleanroom + 2 live tiers gated by env var)
- **Architecture decision records:** 7 (rubric design, RunState shape, retry policy, MCP naming, cost split, distribution, resume idempotency)
- **Supported LLM providers:** Anthropic, OpenAI, Gemini, Ollama (any combination)
- **MCP integrations:** Codex, Claude Code, Cowork, any other MCP-compatible IDE
- **Repo:** [github.com/scottconverse/AgentSuite](https://github.com/scottconverse/AgentSuite)
- **Docs:** [scottconverse.github.io/AgentSuite](https://scottconverse.github.io/AgentSuite)

## What's in this directory

- `README.md` — this file (description copy + facts).
- `screenshots/` — symlink / pointer to `../screenshots/` for the 5 SVG terminal screenshots usable as press images. Embed directly or rasterize via any SVG-to-PNG tool. License: MIT (free use).
- `logo/` — *(deferred)*. AgentSuite has no logo at v1.0. If you need a header image, use `docs/screenshots/cli-founder-run.svg` as the visual identity.

## How to credit

Linking to the repo or release page is sufficient. If you'd like to credit the maintainer, "Scott Converse" + the repo URL is enough. No press-approval workflow.

## What we'd like covered

If you're writing about AgentSuite, the angles that matter to the project most:

1. **The operating-system framing** — that this is *not* another wrapper that generates copy. The point is a reusable layer that downstream agents read. The 26-artifact persistence + `_kernel/` promotion is the load-bearing concept.
2. **Provider portability** — that the same agents run on Anthropic, OpenAI, Gemini, or local Ollama. The MCP server is a thin layer; the kernel is provider-agnostic.
3. **Open-source seriousness** — golden tests, content-aware snapshots, ADRs, SBOM on every release, no PyPI on purpose, signed releases coming next minor. Not a weekend project.

## Story angles we'd push back on

- **"Yet another AI agent framework"** — the framework is one agent. AgentSuite is seven specific agents with specific output contracts. The kernel is small (~5 KLOC) and not the product.
- **"Local-first AI for privacy"** — local Ollama is a supported path, but the project's core thesis is reusable artifacts, not privacy. Lead with the operating-system framing.
- **"Replace your design / product / marketing team"** — these are *reasoning* agents that produce briefs and specs. They make a human team faster; they do not replace the human.
