# AgentSuite User Manual

This manual walks you through using AgentSuite as a non-technical user. If you've never installed a Python package or used a command line, the steps below show you exactly what to type and what you should see.

## What AgentSuite is, in plain language

AgentSuite is a piece of software that takes loose ideas (like "I want a brand system for my new product") and turns them into structured documents you can use over and over. Think of it as a one-person creative operations team. Instead of starting from scratch every time you write a landing page, social post, or pitch, AgentSuite produces a reusable set of guides — your brand voice, your audience map, your message library — and a set of reusable templates so the next asset takes minutes, not hours.

## What you need before you start

1. **A computer running Windows, Mac, or Linux.**
2. **Python 3.11 or 3.12 installed.** Get it at https://www.python.org/downloads/. During install, check "Add Python to PATH".
3. **An AI brain.** Either:
   - **Cloud API key** (faster, costs a few cents to a few dollars per run): Anthropic (https://console.anthropic.com), OpenAI (https://platform.openai.com), or Google Gemini (https://aistudio.google.com/app/apikey).
   - **Local Ollama** (slower, free): install Ollama from https://ollama.ai and pull `gemma4:e4b`. See "Step 2b" below.

## Step 1 — install AgentSuite

Open a terminal:
- **Windows:** Start menu → "Command Prompt"
- **Mac:** Spotlight (⌘+Space) → "Terminal"
- **Linux:** your distribution's terminal

Type:

```
pip install git+https://github.com/scottconverse/AgentSuite.git
```

Press Enter. You'll see a lot of text scroll by as Python downloads the code from GitHub and installs it. When it finishes, you'll see your prompt return.

(AgentSuite is not published to PyPI — it installs directly from its GitHub repository. The command above tells `pip` to fetch the latest code from GitHub.)

To verify the install:

```
agentsuite agents
```

You should see something like:

```json
{
  "enabled": ["founder"],
  "all_registered": ["founder"]
}
```

## Step 2 — set your API key

In the same terminal:

**Anthropic:**
```
set ANTHROPIC_API_KEY=sk-ant-your-key-here    (Windows)
export ANTHROPIC_API_KEY=sk-ant-your-key-here   (Mac/Linux)
```

**OpenAI:**
```
set OPENAI_API_KEY=sk-your-key-here    (Windows)
export OPENAI_API_KEY=sk-your-key-here   (Mac/Linux)
```

**Google Gemini:**
```
set GEMINI_API_KEY=your-key-here    (Windows)
export GEMINI_API_KEY=your-key-here   (Mac/Linux)
```

(`GOOGLE_API_KEY` is also accepted as an alias.)

The key only stays set for this terminal window. To make it permanent, add the line to your shell profile (`~/.bashrc`, `~/.zshrc`, or set as a User Environment Variable in Windows System Settings).

## Step 2b (alternative) — run Ollama locally instead of using a cloud API key

If you'd rather run AgentSuite entirely offline (and free), install Ollama and pull a Gemma 4 model. There's no API key step.

1. Install Ollama from https://ollama.ai (one-time setup).
2. Pull the recommended model:
   ```
   ollama pull gemma4:e4b
   ```
   (Alternatives: `gemma4:e2b` for laptops, `gemma4:26b-moe` for workstations.)
3. Make sure the daemon is running:
   ```
   ollama serve
   ```
   (On most systems Ollama starts automatically after install.)

That's it — AgentSuite will auto-detect the running daemon as long as no cloud API key is set in your environment.

## Step 3 — gather your inputs

Create a folder somewhere on your computer (call it `my-brand-inputs/`) and put in it any of:
- A README or one-page description of your product (`README.md` or `README.txt`)
- A short writing sample in your own voice (`voice.txt`) — a paragraph from a past blog post, email, or pitch
- Screenshots of your existing site, app, or product (`*.png` or `*.jpg`)

None of these are required. You can run the agent with just a one-sentence business goal and no folder at all.

## Step 4 — run the Founder agent

```
agentsuite founder run --business-goal "Launch My Product v1" --project-slug my-product --inputs-dir ./my-brand-inputs
```

What happens:
1. The agent walks 5 stages and writes 26 files to a folder called `.agentsuite/runs/run-cli/` in your current directory.
2. The terminal prints a JSON status block when it's done (takes 30-90 seconds).
3. The status will say `"awaiting_approval"`. The agent has produced the artifacts but is waiting for you to review and approve.

## Step 5 — review what was produced

Open `.agentsuite/runs/run-cli/` in your file explorer. You'll see:

| File | What it is |
|---|---|
| `brand-system.md` | The single most important file — your brand mission, audience, tone, vocabulary, visual identity, and what you can/can't say |
| `founder-voice-guide.md` | How you write — descriptors, sentence patterns, words to use and avoid |
| `product-positioning.md` | What you do, who it's for, why it's better than alternatives |
| `audience-map.md` | Who your customers are in detail |
| `claims-and-proof-library.md` | Things you can say, with proof for each |
| `visual-style-guide.md` | Colors, typography, imagery |
| `campaign-production-workflow.md` | How to produce any new asset |
| `asset-qa-checklist.md` | Quality checklist for finished assets |
| `reusable-prompt-library.md` | Prompt templates you can paste into ChatGPT, Claude, etc. |
| `brief-template-library/` | 11 ready-to-use briefs for common assets |
| `qa_report.md` | The agent's self-critique with scores |

Open `brand-system.md` first. Read it. If it captures your brand correctly, proceed to Step 6. If not, see "Iterating" below.

## Step 6 — approve

```
agentsuite founder approve --run-id run-cli --approver yourname --project-slug my-product
```

This copies the approved artifacts to `.agentsuite/_kernel/my-product/` where they live permanently and can be used by other AgentSuite agents (Design, Marketing, etc., as those ship in v0.2+).

## Iterating

If `brand-system.md` is wrong:
- **Wrong audience or voice:** add more inputs (a longer voice sample, more product docs) and re-run with a new `--run-id`.
- **A specific section is off:** open the file, edit by hand, and use `agentsuite founder resume --run-id <id> --stage qa` to re-run the QA check on your edits.

You can do this as many times as you want. Each run costs cents to a few dollars depending on input size.

## Common errors and what they mean

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | AgentSuite couldn't find an API key OR a running Ollama daemon | Set an API key (Step 2) or start Ollama (Step 2b) |
| `HardCapExceeded: $5.00` | Your run cost more than the safety limit | Either reduce input size, or increase the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `ConsistencyCheckFailed` | The agent generated artifacts that contradict each other | Look at `consistency_report.json` in your run folder, then re-run after editing inputs |
| `extract stage produced invalid JSON` | The LLM returned malformed output | Re-run — usually transient |

## Glossary

- **MCP (Model Context Protocol):** the standard way AI coding tools (Codex, Claude Code, Cowork) talk to external programs like AgentSuite.
- **Agent:** a program that walks a defined sequence of steps to produce structured output.
- **Pipeline:** the sequence of steps (intake → extract → spec → execute → qa → approval).
- **Artifact:** any file the agent produces.
- **Promotion:** copying approved artifacts from a run folder to the long-lived `_kernel/` folder.
- **LLM:** Large Language Model — the AI brain (Claude, GPT, etc.) that does the actual reasoning.

## Using the Product Agent

The Product Agent takes a product idea and produces a complete set of planning documents — everything a product manager needs to hand off a feature to engineering.

### What it does

In one sentence: you tell it the product name, who it's for, and the problem it solves, and it writes nine specification documents and eight ready-to-fill templates in 30–120 seconds.

### What you need to have ready

**Required:**
- **Product name** — the name of your product or the feature you're specifying (e.g. "Onboarding Flow v2")
- **Target users** — one sentence describing who this is for (e.g. "Small business owners who sign up but never complete setup")
- **Core problem** — one sentence describing what you're solving (e.g. "Users drop off before completing their first task because the setup steps are unclear")
- **Project slug** — a short, lowercase, hyphenated label you choose for the output folder (e.g. `onboarding-v2`)

**Optional (but helpful if you have them):**
- Research documents — user interview notes, survey results, analytics exports (any `.txt`, `.md`, or `.pdf` files)
- Competitor documents — competitor feature lists, pricing pages, review summaries

None of the optional files are required. The agent produces useful output from the four required fields alone.

### Step 1 — run the Product Agent

```
agentsuite product run --product-name "Onboarding Flow v2" --target-users "Small business owners who sign up but never complete setup" --core-problem "Users drop off before completing their first task because the setup steps are unclear" --project-slug onboarding-v2
```

If you have research or competitor files, add them:

```
agentsuite product run --product-name "..." --target-users "..." --core-problem "..." --project-slug onboarding-v2 --research-dir ./my-research --competitor-dir ./competitor-notes
```

The terminal prints a status block when it's done. It will say `"awaiting_approval"`.

### Step 2 — review the nine output documents

Open `.agentsuite/runs/run-cli/` in your file explorer. You'll see nine documents:

| File | What it is |
|---|---|
| `product-requirements-doc.md` | The main spec — what you're building, why, and for whom. Start here. |
| `user-story-map.md` | The features broken into epics (big themes) and user stories (individual steps a user takes) |
| `feature-prioritization.md` | A ranked list of features using MoSCoW scoring (Must / Should / Could / Won't) so you know what to build first |
| `success-metrics.md` | The numbers you'll track to know if the product is working — KPIs, targets, and how to measure them |
| `competitive-analysis.md` | How your product compares to alternatives users might choose instead |
| `user-persona-map.md` | Detailed profiles of your typical users — their goals, frustrations, and daily context |
| `acceptance-criteria.md` | The specific conditions each feature must meet before it's considered done |
| `product-roadmap.md` | A Now / Next / Later view of what ships when |
| `risk-register.md` | Known risks (technical, market, timeline) with suggested ways to reduce each one |

Read `product-requirements-doc.md` first. If it captures the right scope and audience, proceed to Step 3.

### Step 3 — check your QA scores

Open `qa_scores.json` in the same folder. Each document gets a score from 0 to 10. If any score is below 7.0, that document has a specific issue. Look for the `revision_instructions` field next to the low score — it tells you exactly what to change. You can edit the document by hand and re-run the QA step, or adjust your inputs and re-run the full agent.

### Step 4 — approve

```
agentsuite product approve --run-id run-cli --approver yourname --project-slug onboarding-v2
```

This copies the approved documents to `.agentsuite/_kernel/onboarding-v2/` where they live permanently and can be used in future sessions.

### The eight brief templates

Inside `.agentsuite/runs/run-cli/brief-template-library/` you'll find eight fill-in-the-blank templates for common product management tasks:

| Template | When to use it |
|---|---|
| Sprint planning brief | Hand to engineering at the start of each sprint |
| Stakeholder update | Weekly status email or Slack post for leadership |
| Launch announcement | Internal or external announcement when the feature ships |
| Go-to-market summary | One-pager for sales, support, and marketing before launch |
| Executive summary | Board or investor-level overview of what was built and why |
| User interview guide | Question script for 30-minute customer discovery calls |
| A/B test plan | How to set up and measure a controlled experiment |
| Retrospective report | Post-sprint or post-launch review of what went well and what didn't |

### Common errors and what they mean

| Error | What it means | What to do |
|---|---|---|
| `ConsistencyCheckFailed` | Two of the nine documents contradict each other (e.g. different target users in the PRD vs. the persona map) | Make your `--target-users` and `--core-problem` descriptions more specific, then re-run |
| Low QA scores (below 7.0) | A document is missing important detail or is too vague | Open `qa_scores.json`, read `revision_instructions`, edit the flagged document by hand or add more input context and re-run |
| `NoProviderConfigured` | No API key found and Ollama isn't running | Set an API key (Step 2 above) or start Ollama (Step 2b above) |
| `HardCapExceeded: $5.00` | The run cost more than the safety limit | Reduce the size of your research/competitor files, or raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned a formatting error | Re-run — this resolves itself almost every time |

### Glossary additions

- **PRD (Product Requirements Document):** The central spec for a product or feature. It answers: what are we building, who is it for, why does it matter, and what does "done" look like? Engineers, designers, and stakeholders all read from this document.
- **QA rubric:** A scoring checklist the agent runs against its own output. Each document is scored 0–10 on criteria like completeness, internal consistency, and clarity. Scores below 7.0 trigger specific revision instructions.
- **Epic:** A large chunk of work that groups related user stories together. Think of it as a chapter heading — "User Onboarding" is an epic; "User sees a progress bar during setup" is a story inside it.
- **KPI (Key Performance Indicator):** A number you track to know if something is working. For example, "percentage of users who complete setup within 7 days" is a KPI for an onboarding feature.

## Where to get help

- Open an issue: https://github.com/scottconverse/AgentSuite/issues
- Read the developer docs: `CONTRIBUTING.md`
- Full reference: `docs/README-FULL.pdf`
