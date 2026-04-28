# AgentSuite User Manual

**Version 0.8.3**

---

This manual is written for people who have never installed a Python package, never used a command line, and are not software engineers. Every step is shown exactly as you would type it. Every term is defined the first time it appears.

If you already know your way around a terminal, you can skim the setup sections and jump straight to the agent chapters.

---

## Table of Contents

1. What Is AgentSuite?
2. What You Need Before You Start
3. Installation
4. Setting Your API Key
5. How AgentSuite Works (The 5-Stage Pipeline)
6. Enabling Agents
7. The Seven Agents
   - Founder Agent
   - Design Agent
   - Product Agent
   - Engineering Agent
   - Marketing Agent
   - Trust/Risk Agent
   - CIO Agent
8. Reading Your Results
9. Configuration Reference
10. Troubleshooting
11. Glossary

---

## 1. What Is AgentSuite?

AgentSuite is a software tool that turns a short description of your business, product, or project into a full set of professional documents — brand guides, product specs, engineering designs, marketing plans, risk assessments, and IT strategies — in about one to two minutes.

Think of it as a one-person creative and planning operations team. Instead of staring at a blank document, you give AgentSuite a few sentences about what you are building, who it is for, and what problem it solves. AgentSuite then writes nine detailed documents and eight ready-to-fill templates for you to use.

AgentSuite has seven specialized agents (think of an "agent" as a specialist). Each agent focuses on a different part of building and running a product or organization:

| Agent | What it produces |
|---|---|
| **Founder** | Brand identity, voice, positioning, and audience documents |
| **Design** | Visual identity, design system, and accessibility guidelines |
| **Product** | Product requirements, user stories, roadmap, and success metrics |
| **Engineering** | System architecture, API design, security review, and operational runbooks |
| **Marketing** | Campaign strategy, messaging, content calendar, and channel plan |
| **Trust/Risk** | Threat model, risk register, incident response plan, and compliance matrix |
| **CIO** | IT strategy, technology roadmap, governance framework, and budget model |

You do not need to use all seven agents. Use only the ones that are relevant to what you are doing today.

AgentSuite is open-source software. It runs on your own computer and uses your own AI provider account (such as Anthropic, OpenAI, or Google). Your documents and data are never stored on anyone else's servers.

---

## 2. What You Need Before You Start

You need three things:

**1. A computer running Windows, Mac, or Linux.**
AgentSuite works on all three operating systems.

**2. Python 3.11 or 3.12 installed.**
Python is a free programming language that AgentSuite is built with. You do not need to know how to program — you just need Python installed.
- Download it at: https://www.python.org/downloads/
- During installation on Windows, check the box that says "Add Python to PATH." This is important.
- To check if Python is already installed, open a terminal (see below) and type `python --version`. If it shows a number starting with 3.11 or 3.12, you are ready.

**3. An AI provider account.**
AgentSuite uses a large language model — the AI brain — to write the documents. You choose one of:
- **Anthropic Claude** (recommended): https://console.anthropic.com — create an account, go to "API Keys," create a key
- **OpenAI GPT**: https://platform.openai.com — create an account, go to "API Keys," create a key
- **Google Gemini**: https://aistudio.google.com/app/apikey — create an account, create a key
- **Ollama (local, free, no account needed)**: runs the AI on your own computer — see Step 2b below

**What is a terminal?**
A terminal (also called a "command prompt" or "command line") is a text-based window where you type instructions directly to your computer.
- **Windows:** Press the Start button, type "Command Prompt," press Enter.
- **Mac:** Press Command + Space, type "Terminal," press Enter.
- **Linux:** Your distribution's terminal application (often Ctrl + Alt + T).

---

## 3. Installation

Open a terminal. Type the following command exactly as shown and press Enter:

```
pip install "agentsuite[anthropic] @ git+https://github.com/scottconverse/AgentSuite.git"
```

This installs AgentSuite with the Anthropic Claude provider. To use a different AI provider instead, replace `[anthropic]` with `[openai]`, `[gemini]`, or `[ollama]`. To install all providers at once: `agentsuite[all]`.

### Extras / Optional dependencies

AgentSuite uses "extras" to install only the AI provider libraries you need. Here is what each extra includes:

| Extra | What it installs | When to use it |
|---|---|---|
| `[anthropic]` | The `anthropic` Python library | You are using Anthropic Claude (recommended default) |
| `[openai]` | The `openai` Python library | You are using OpenAI GPT models |
| `[gemini]` | The `google-generativeai` library | You are using Google Gemini models |
| `[ollama]` | The `ollama` Python library | You are running models locally via Ollama |
| `[all]` | All four provider libraries above | You want to switch between providers without reinstalling |
| `[mcp]` | MCP server dependencies | You are wiring AgentSuite into Claude Code, Codex, or another MCP-compatible tool |

Example — install with OpenAI support:
```
pip install "agentsuite[openai] @ git+https://github.com/scottconverse/AgentSuite.git"
```

Example — install everything including MCP:
```
pip install "agentsuite[all,mcp] @ git+https://github.com/scottconverse/AgentSuite.git"
```

You will see a lot of text scroll by as your computer downloads and installs AgentSuite from GitHub (a website where open-source software is stored). This is normal. When it finishes, your prompt returns.

To confirm the installation worked, type:

```
agentsuite agents
```

You should see output like this:

```json
{
  "enabled": ["founder"],
  "all_registered": ["founder"]
}
```

If you see that, installation succeeded. If you see an error saying "agentsuite is not recognized," close the terminal, reopen it, and try again. On some systems you may need to restart your computer after installing Python.

**Installing from a local copy instead**

If you have downloaded the AgentSuite code directly (for example, from GitHub as a ZIP file), you can install from that folder instead. Navigate to the folder in your terminal and run:

```
pip install -e .
```

For development installs, add your provider: `pip install -e ".[anthropic]"` (or `.[all]` for all providers).

The `-e` flag means "editable install" — changes to the code in that folder take effect immediately without reinstalling.

---

## 4. Setting Your API Key

An API key is like a password that gives AgentSuite permission to use your AI provider account. You set it in your terminal before running AgentSuite.

**Anthropic (Claude):**
```
Windows:   set ANTHROPIC_API_KEY=sk-ant-your-key-here
Mac/Linux: export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**OpenAI (GPT):**
```
Windows:   set OPENAI_API_KEY=sk-your-key-here
Mac/Linux: export OPENAI_API_KEY=sk-your-key-here
```

**Google Gemini:**
```
Windows:   set GOOGLE_API_KEY=your-key-here
Mac/Linux: export GOOGLE_API_KEY=your-key-here
```

Replace the text after the `=` sign with your actual key. The key only stays set for the current terminal window. If you close the terminal and reopen it, you need to set it again.

**To make the key permanent (so you never have to type it again):**
- **Windows:** Search "Environment Variables" in the Start menu → "Edit the system environment variables" → "Environment Variables" → "New" under User Variables → enter the name and value.
- **Mac/Linux:** Add the `export` line to your `~/.zshrc` or `~/.bashrc` file and restart the terminal.

**Step 4b — Using Ollama instead (free, local, no cloud account)**

If you prefer to run everything on your own computer without an internet connection or an API account, you can use Ollama. Ollama is free software that runs an AI model locally on your computer.

1. Install Ollama from https://ollama.ai (follow the instructions for your operating system).
2. Open a terminal and pull the recommended model:
   ```
   ollama pull gemma4:e4b
   ```
   (For older or slower computers, try `gemma4:e2b`. For powerful workstations, `gemma4:26b-moe` is more capable.)
3. Make sure Ollama is running. On most systems it starts automatically. If it does not, run:
   ```
   ollama serve
   ```

When Ollama is running and no cloud API key is set, AgentSuite detects Ollama automatically. No further configuration is needed.

---

## 5. How AgentSuite Works (The 5-Stage Pipeline)

Every agent in AgentSuite runs the same five stages in sequence. Understanding what each stage does helps you know what to expect and what to do if something goes wrong.

**Stage 1 — Intake**
AgentSuite reads the inputs you provided on the command line (your product name, mission, target users, and so on) along with any files you pointed it to. It organizes these into a structured internal summary that the rest of the pipeline works from.

**Stage 2 — Extract**
AgentSuite sends your inputs to the AI and asks it to extract the key facts, themes, and structure it will need to write the documents. The result is a structured data file (stored internally as JSON — a format AI tools use to organize information). If the AI returns a malformed response at this stage, you will see the error `extract stage produced invalid JSON`. Running the command again almost always resolves this.

**Stage 3 — Spec**
AgentSuite uses the extracted data to generate a detailed specification — a complete plan for each of the nine documents it will produce. The spec stage resolves any gaps or contradictions before the writing begins.

**Stage 4 — Execute**
The AI writes all nine documents and eight brief templates using the specification. This is the longest stage — typically 20 to 90 seconds depending on your inputs and which AI provider you are using.

**Stage 5 — QA (Quality Assurance)**
AgentSuite runs a quality check on every document it produced. Each document is scored on a scale of 0 to 10 against a rubric (a set of criteria). The rubric checks things like: Is the document complete? Is it internally consistent? Does it contradict anything in the other documents? Are the instructions actionable?

Documents that score 7.0 or above pass automatically. Documents that score below 7.0 are flagged with specific revision instructions telling you exactly what to fix.

**Approval**
After the five stages complete, the run enters an "awaiting approval" state. The agent has done its work and is waiting for you to review what it produced. When you are satisfied with the output, you run the approve command (shown in each agent chapter below). Approval copies the documents from the temporary run folder into a permanent location called the "kernel" where they can be reused by other agents and future runs.

You can approve immediately, or you can edit documents by hand first and then approve. Nothing is locked or permanent until you approve.

---

## 6. Enabling Agents

By default, only the Founder agent is enabled. To use additional agents, you set an environment variable (a setting) that lists the ones you want.

```
Windows:   set AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio
Mac/Linux: export AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio
```

You can enable just the ones you need. For example, to enable only the Product and Marketing agents:

```
Windows:   set AGENTSUITE_ENABLED_AGENTS=product,marketing
Mac/Linux: export AGENTSUITE_ENABLED_AGENTS=product,marketing
```

To confirm which agents are currently enabled:

```
agentsuite agents
```

---

## 7. The Seven Agents

---

### Founder Agent

**What it produces**

The Founder agent is the starting point for everything else. It produces nine documents that define who you are as a company or project:

| Document | What it is |
|---|---|
| `brand-system.md` | Your brand mission, audience profile, tone of voice, vocabulary, visual identity summary, and what you can and cannot say. This is the master document — start here. |
| `founder-voice-guide.md` | Your personal writing style — descriptors, sentence patterns, words to use and words to avoid |
| `product-positioning.md` | What you do, who it is for, why it is better than alternatives, and how to explain it in one sentence |
| `audience-map.md` | A detailed profile of your customers — who they are, what they want, what frustrates them, and how they make decisions |
| `claims-and-proof-library.md` | Things you can truthfully say about your product, each paired with the evidence that supports it |
| `visual-style-guide.md` | Color palette, typography choices, imagery direction, and visual dos and don'ts |
| `campaign-production-workflow.md` | A repeatable process for producing any new marketing asset |
| `asset-qa-checklist.md` | A quality checklist to run on any finished asset before it goes public |
| `reusable-prompt-library.md` | Ready-to-use prompt templates you can paste into ChatGPT, Claude, or any other AI tool |

It also produces eight brief templates in a `brief-template-library/` folder for common founder tasks (pitch deck, investor update, press release, and more).

**When to use it**

Use the Founder agent at the very beginning of a project, when you are establishing your brand identity, or when your existing brand needs to be refreshed and documented properly. Run it before any of the other agents — its output feeds into the Design, Marketing, and other agents.

**What you need to provide**

- `--business-goal` — what you are trying to achieve with this run, in plain language (required)
- `--project-slug` — a short lowercase label for the project, used to name the output folder (optional)
- `--inputs-dir` — path to a folder of source materials such as brand docs or research files (optional)
- `--run-id` — a unique label for this run, used to name the output folder (optional; auto-generated as `run-YYYYMMDDTHHMMSS-<6hex>` if omitted)
- `--force` — overwrite an existing run directory of the same name instead of failing (optional; without this flag, re-running with the same `--run-id` will error to protect your existing output)

**CLI command**

```
agentsuite founder run \
  --business-goal "Launch Acme invoicing for small businesses" \
  --project-slug acme \
  --inputs-dir ./my-brand-inputs
```

On Windows, replace the backslash line breaks with a single long line:

```
agentsuite founder run --business-goal "Launch Acme invoicing for small businesses" --project-slug acme --inputs-dir ./my-brand-inputs
```

To overwrite a previous run with the same ID, add `--force`:

```
agentsuite founder run --business-goal "Launch Acme invoicing for small businesses" --project-slug acme --force
```

**How to approve**

After reviewing the documents in `.agentsuite/runs/<run-id>/`, run:

```
agentsuite founder approve --run-id run-cli --approver "Your Name" --project-slug acme
```

Replace `"Your Name"` with your actual name and `acme` with a short lowercase label for your project (no spaces — use hyphens instead, like `my-project`).

**Common errors**

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | No API key found and Ollama is not running | Set your API key (Section 4) or start Ollama (Section 4b) |
| `ConsistencyCheckFailed` | Two documents contradict each other | Make your `--business-goal` more specific, then re-run |
| `HardCapExceeded: $5.00` | The run exceeded the cost safety limit | Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned malformed output | Re-run — this is almost always transient |

---

### Design Agent

**What it produces**

The Design agent takes a brand name, design brief, and target audience and produces nine documents that define your visual identity and design system:

| Document | What it is |
|---|---|
| `design-system.md` | The master design document — all the rules for how your brand looks and feels. Start here. |
| `color-palette.md` | Primary, secondary, and accent colors with hex codes, usage rules, and accessibility notes |
| `typography-system.md` | Font choices, size scales, line spacing, and rules for headers, body text, and captions |
| `component-library-guide.md` | Guidelines for buttons, forms, cards, navigation, and other repeating UI elements |
| `iconography-guide.md` | Icon style, size rules, usage context, and naming conventions |
| `imagery-guidelines.md` | Photography style, illustration approach, and what to avoid |
| `motion-and-animation.md` | Rules for transitions, loading states, and animated feedback |
| `accessibility-checklist.md` | Color contrast requirements, keyboard navigation, screen reader support, and WCAG compliance notes |
| `brand-application-examples.md` | Annotated examples showing the design system applied to real-world scenarios |

It also produces eight brief templates for common design tasks (design handoff, usability test plan, design critique, and more).

**When to use it**

Use the Design agent after the Founder agent has established your brand identity. It translates the brand values and voice into a concrete visual language that designers, developers, and content creators can all follow.

**What you need to provide**

- `--target-audience` — one sentence describing who will interact with this design (required)
- `--campaign-goal` — one sentence describing the design goal or what this visual identity must achieve (required)
- `--channel` — the primary channel or medium where this design will appear (required; examples: "web app," "print," "mobile")
- `--project-slug` — a short lowercase label for the project, used to name the output folder (optional)
- `--inputs-dir` — path to a folder of existing brand materials (optional)
- `--run-id` — unique label for this run (optional; auto-generated as `run-YYYYMMDDTHHMMSS-<6hex>` if omitted)
- `--force` — overwrite an existing run directory of the same name (optional)

**CLI command**

```
agentsuite design run \
  --target-audience "Small business owners aged 30-55 who are not tech-savvy but expect professional tools" \
  --campaign-goal "Create a modern, trustworthy visual identity that feels professional but approachable" \
  --channel "web app" \
  --project-slug acme-design
```

On Windows, use a single long line:

```
agentsuite design run --target-audience "Small business owners aged 30-55 who are not tech-savvy but expect professional tools" --campaign-goal "Create a modern, trustworthy visual identity that feels professional but approachable" --channel "web app" --project-slug acme-design
```

**How to approve**

```
agentsuite design approve --run-id run-cli --approver "Your Name" --project-slug acme-design
```

**Common errors**

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | No API key found and Ollama is not running | Set your API key (Section 4) or start Ollama (Section 4b) |
| `ConsistencyCheckFailed` | Two design documents contradict each other | Make your `--design-brief` more specific, then re-run |
| `HardCapExceeded: $5.00` | The run exceeded the cost safety limit | Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned malformed output | Re-run — this is almost always transient |

---

### Product Agent

**What it produces**

The Product agent takes a product name, target users, and the problem being solved and produces nine documents that give your team everything needed to plan and build the product:

| Document | What it is |
|---|---|
| `product-requirements-doc.md` | The central spec — what you are building, who it is for, and what "done" looks like. Start here. |
| `user-story-map.md` | Features broken into epics (large themes) and user stories (individual steps a user takes) |
| `feature-prioritization.md` | A ranked list of features using MoSCoW scoring: Must have, Should have, Could have, Won't have this time |
| `success-metrics.md` | The numbers you will track to know if the product is working — targets and how to measure them |
| `competitive-analysis.md` | How your product compares to alternatives users might choose instead |
| `user-persona-map.md` | Detailed profiles of your typical users — their goals, frustrations, and daily context |
| `acceptance-criteria.md` | The specific conditions each feature must meet before it is considered done |
| `product-roadmap.md` | A Now / Next / Later view of what ships when |
| `risk-register.md` | Known risks — technical, market, timeline — with suggested ways to reduce each one |

It also produces eight brief templates: sprint planning brief, stakeholder update, launch announcement, go-to-market summary, executive summary, user interview guide, A/B test plan, and retrospective report.

**When to use it**

Use the Product agent when you are starting a new feature or product, or when you need to create or refresh a formal specification that you can hand off to an engineering team, share with investors, or align stakeholders around.

**What you need to provide**

- `--product-name` — the name of the product or feature being specified (required)
- `--target-users` — one sentence describing who this is for (required)
- `--core-problem` — one sentence describing the problem you are solving (required)
- `--project-slug` — a short lowercase label for the project (optional)
- `--inputs-dir` — path to a folder of source materials such as research files or competitor notes (optional)
- `--run-id` — unique label for this run (optional; auto-generated as `run-YYYYMMDDTHHMMSS-<6hex>` if omitted)
- `--force` — overwrite an existing run directory of the same name (optional)

**CLI command**

```
agentsuite product run \
  --product-name "Onboarding Flow v2" \
  --target-users "Small business owners who sign up but never complete setup" \
  --core-problem "Users drop off before completing their first task because the setup steps are unclear" \
  --project-slug onboarding-v2
```

On Windows, use a single long line:

```
agentsuite product run --product-name "Onboarding Flow v2" --target-users "Small business owners who sign up but never complete setup" --core-problem "Users drop off before completing their first task because the setup steps are unclear" --project-slug onboarding-v2
```

**How to approve**

```
agentsuite product approve --run-id run-cli --approver "Your Name" --project-slug onboarding-v2
```

**Common errors**

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | No API key found and Ollama is not running | Set your API key (Section 4) or start Ollama (Section 4b) |
| `ConsistencyCheckFailed` | Two documents contradict each other (for example, different target users in the PRD versus the persona map) | Make your `--target-users` and `--core-problem` descriptions more specific, then re-run |
| Low QA scores (below 7.0) | A document is missing important detail or is too vague | Open `qa_scores.json`, read `revision_instructions`, edit the document by hand or add more input context and re-run |
| `HardCapExceeded: $5.00` | The run exceeded the cost safety limit | Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned malformed output | Re-run — this is almost always transient |

---

### Engineering Agent

**What it produces**

The Engineering agent takes a system name, the technical problem it solves, the technology stack, and scale requirements and produces nine documents that an engineering team needs to design, build, and operate the system:

| Document | What it is |
|---|---|
| `architecture-decision-record.md` | Key architectural choices — what was decided, why, what was considered, and what the consequences are. Start here. |
| `system-design.md` | The high-level system architecture — the major components, how they connect, and how data flows between them |
| `api-spec.md` | API contracts: every endpoint, what you send it, and what it sends back |
| `data-model.md` | The data entities (tables, records, objects), how they relate to each other, and where they are stored |
| `security-review.md` | Threat model, security controls in place, and a ranked assessment of remaining risks |
| `deployment-plan.md` | Infrastructure layout, how the system gets deployed, and the configuration it needs to run |
| `runbook.md` | Step-by-step operational procedures for common tasks and how to respond to incidents |
| `tech-debt-register.md` | Known shortcuts and compromises, each with a priority level and a plan to address it |
| `performance-requirements.md` | Service level agreements, throughput targets, and what load the system must handle |

It also produces eight brief templates: sprint ticket, code review checklist, incident report, capacity plan, on-call handoff, release checklist, postmortem, and vendor evaluation.

**When to use it**

Use the Engineering agent at the start of any significant software project or when designing a new service. It is most valuable when you need a structured technical spec that multiple engineers can align on, or when you want to document the design of an existing system that has never been formally written down.

**What you need to provide**

- `--system-name` — the name of the system or service being designed (required)
- `--problem-domain` — one sentence describing the technical problem being solved (required)
- `--tech-stack` — the languages, frameworks, and databases you plan to use (required)
- `--scale-requirements` — the load and reliability targets the system must meet (required)
- `--project-slug` — a short lowercase label for the project (optional)
- `--inputs-dir` — path to a folder of existing architecture docs, ADR history, or incident reports (optional)
- `--run-id` — unique label for this run (optional; auto-generated as `run-YYYYMMDDTHHMMSS-<6hex>` if omitted)
- `--force` — overwrite an existing run directory of the same name (optional)

**CLI command**

```
agentsuite engineering run \
  --system-name "Payment Processing Service" \
  --problem-domain "Process and reconcile customer payments across multiple payment providers with guaranteed delivery" \
  --tech-stack "Python, FastAPI, PostgreSQL, Redis, Kubernetes" \
  --scale-requirements "10,000 transactions per minute, 99.99% uptime, sub-200ms p99 latency" \
  --project-slug payment-service
```

On Windows, use a single long line:

```
agentsuite engineering run --system-name "Payment Processing Service" --problem-domain "Process and reconcile customer payments across multiple payment providers with guaranteed delivery" --tech-stack "Python, FastAPI, PostgreSQL, Redis, Kubernetes" --scale-requirements "10,000 transactions per minute, 99.99% uptime, sub-200ms p99 latency" --project-slug payment-service
```

**How to approve**

```
agentsuite engineering approve --run-id run-cli --approver "Your Name" --project-slug payment-service
```

**Common errors**

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | No API key found and Ollama is not running | Set your API key (Section 4) or start Ollama (Section 4b) |
| `ConsistencyCheckFailed` | Two documents contradict each other (for example, different scale targets in system-design vs. performance-requirements) | Make your `--scale-requirements` and `--tech-stack` descriptions more specific, then re-run |
| Low QA scores (below 7.0) | A document is missing important detail | Open `qa_scores.json`, read `revision_instructions`, edit or re-run |
| `HardCapExceeded: $5.00` | The run exceeded the cost safety limit | Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned malformed output | Re-run — this is almost always transient |

---

### Marketing Agent

**What it produces**

The Marketing agent takes a brand name, campaign goal, and target market and produces nine documents that a marketing team needs to plan, execute, and measure a campaign:

| Document | What it is |
|---|---|
| `campaign-brief.md` | The master campaign document — objectives, strategy, and core messaging direction. Start here. |
| `target-audience-profile.md` | A detailed profile of your ideal customer: who they are, what they care about, and what motivates their decisions |
| `messaging-framework.md` | Your value propositions, key messages for each audience segment, and the tone and voice to use across all content |
| `content-calendar.md` | An editorial calendar with proposed topics, formats, and the channels each piece of content belongs on |
| `channel-strategy.md` | Which channels to use, how to split the budget, and what success looks like on each channel |
| `seo-keyword-plan.md` | The search terms your audience uses and the content gaps your campaign can fill |
| `competitive-positioning.md` | How your brand sits relative to competitors and how to differentiate in messaging and targeting |
| `launch-plan.md` | The step-by-step sequence for going to market — what happens first, what follows, and the milestones |
| `measurement-framework.md` | The metrics you will track, how to attribute results to the campaign, and the reporting cadence |

It also produces eight brief templates: ad copy brief, blog post brief, email campaign, influencer brief, landing page brief, press release, quarterly report, and social post series.

**When to use it**

Use the Marketing agent when planning a new campaign, launching a product or feature, entering a new market, or when you need to align a marketing team around a shared strategy and messaging framework.

**What you need to provide**

- `--brand-name` — the name of your company or product (required)
- `--campaign-goal` — one sentence describing what you want to achieve (required)
- `--target-market` — one sentence describing who you are trying to reach (required)
- `--project-slug` — a short lowercase label for the project (optional)
- `--inputs-dir` — path to a folder of existing brand documents or competitor notes (optional)
- `--budget-range` — the approximate campaign budget (optional; example: "$10,000–$50,000")
- `--timeline` — the campaign duration or launch window (optional; example: "Q3 2026, 12 weeks")
- `--channels` — preferred marketing channels (optional; example: "LinkedIn, email, content marketing")
- `--run-id` — unique label for this run (optional; auto-generated as `run-YYYYMMDDTHHMMSS-<6hex>` if omitted)
- `--force` — overwrite an existing run directory of the same name (optional)

**CLI command**

```
agentsuite marketing run \
  --brand-name "Acme Widgets" \
  --campaign-goal "Generate 500 qualified leads for our new B2B SaaS product in Q3" \
  --target-market "Operations managers at manufacturing companies with 50-500 employees" \
  --budget-range "$20,000–$40,000" \
  --timeline "Q3 2026, 12 weeks" \
  --channels "LinkedIn, email, content marketing" \
  --project-slug acme-campaign
```

On Windows, use a single long line:

```
agentsuite marketing run --brand-name "Acme Widgets" --campaign-goal "Generate 500 qualified leads for our new B2B SaaS product in Q3" --target-market "Operations managers at manufacturing companies with 50-500 employees" --project-slug acme-campaign
```

**How to approve**

```
agentsuite marketing approve --run-id run-cli --approver "Your Name" --project-slug acme-campaign
```

**Common errors**

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | No API key found and Ollama is not running | Set your API key (Section 4) or start Ollama (Section 4b) |
| `ConsistencyCheckFailed` | Two documents contradict each other (for example, the channel strategy targets a different audience than the audience profile) | Make your `--campaign-goal` and `--target-market` descriptions more specific, then re-run |
| Low QA scores (below 7.0) | A document is missing important detail | Open `qa_scores.json`, read `revision_instructions`, edit or re-run |
| `HardCapExceeded: $5.00` | The run exceeded the cost safety limit | Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned malformed output | Re-run — this is almost always transient |

---

### Trust/Risk Agent

**What it produces**

The Trust/Risk agent takes a product name, risk domain, and stakeholder context and produces nine documents that a security team, compliance officer, or risk manager needs to assess, document, and communicate organizational risk:

| Document | What it is |
|---|---|
| `threat-model.md` | The primary security document — assets, threat actors, attack vectors, and mitigations. Start here. |
| `risk-register.md` | A prioritized list of identified risks with likelihood, impact rating, owner, and current status |
| `control-framework.md` | The security and compliance controls in place or needed, mapped to specific threats and regulatory requirements |
| `incident-response-plan.md` | Step-by-step playbook for detecting, containing, communicating, and recovering from a security incident |
| `compliance-matrix.md` | A traceability table showing which regulatory requirements are met, partially met, or not yet addressed |
| `vendor-risk-assessment.md` | A structured evaluation of the security posture of third-party vendors and suppliers |
| `security-policy.md` | Organizational security policy covering access control, data handling, acceptable use, and enforcement |
| `audit-readiness-report.md` | An evidence summary and gap analysis preparing the organization for an upcoming audit |
| `residual-risk-acceptance.md` | Formal documentation of risks that have been reviewed and accepted rather than fully mitigated |

It also produces eight brief templates: breach notification, executive risk summary, penetration test brief, remediation tracker, risk acceptance form, security awareness brief, tabletop exercise scenario, and vendor security questionnaire.

**When to use it**

Use the Trust/Risk agent before a security audit, when preparing for regulatory compliance (such as SOC 2, HIPAA, or PCI-DSS), when onboarding a significant new vendor, or any time you need formal documentation of your risk posture.

**What you need to provide**

- `--product-name` — the name of your product, system, or organization being assessed (required)
- `--risk-domain` — the area of risk you want to focus on (required; examples: "cloud infrastructure security," "regulatory compliance — SOC 2 Type II," "third-party vendor risk")
- `--stakeholder-context` — who needs to see and act on these documents (required; examples: "CISO, VP Engineering, and external auditors")
- `--regulatory-context` — applicable regulations or standards (optional; example: "SOC 2 Type II, HIPAA, PCI-DSS")
- `--threat-model-scope` — the boundaries of what is in and out of scope for the threat model (optional)
- `--compliance-frameworks` — specific compliance frameworks you are working toward (optional; example: "NIST CSF, ISO 27001")
- `--policy-dir` — path to a folder of existing security policies (optional)
- `--incident-dir` — path to a folder of past incident reports (optional)
- `--run-id` — unique label for this run (optional; auto-generated as `run-YYYYMMDDTHHMMSS-<6hex>` if omitted)
- `--force` — overwrite an existing run directory of the same name (optional)

**CLI command**

```
agentsuite trust-risk run \
  --product-name "PaymentVault API" \
  --risk-domain "cloud infrastructure security" \
  --stakeholder-context "CISO, VP Engineering, and external auditors" \
  --regulatory-context "PCI-DSS, SOC 2 Type II" \
  --compliance-frameworks "NIST CSF"
```

On Windows, use a single long line:

```
agentsuite trust-risk run --product-name "PaymentVault API" --risk-domain "cloud infrastructure security" --stakeholder-context "CISO, VP Engineering, and external auditors"
```

**How to approve**

```
agentsuite trust-risk approve --run-id run-cli --approver "Your Name" --project-slug payment-vault
```

**Common errors**

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | No API key found and Ollama is not running | Set your API key (Section 4) or start Ollama (Section 4b) |
| `ConsistencyCheckFailed` | Two documents contradict each other (for example, the threat model lists a control that the control framework does not include) | Make your `--risk-domain` and `--stakeholder-context` descriptions more specific, then re-run |
| Low QA scores (below 7.0) | A document is missing important detail | Open `qa_scores.json`, read `revision_instructions`, edit or re-run |
| `HardCapExceeded: $5.00` | The run exceeded the cost safety limit | Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned malformed output | Re-run — this is almost always transient |

---

### CIO Agent

**What it produces**

The CIO agent takes an organization name, strategic priorities, and IT maturity level and produces nine documents that a CIO, IT director, or technology steering committee needs to plan, communicate, and govern technology investment:

| Document | What it is |
|---|---|
| `it-strategy.md` | The primary document — a multi-year IT strategy aligned to the business priorities you provided. Start here. |
| `technology-roadmap.md` | A time-phased view of technology investments, retirements, and capability milestones |
| `vendor-portfolio.md` | A structured inventory of technology vendors with spend estimates, risk ratings, and strategic fit assessments |
| `digital-transformation-plan.md` | A sequenced plan for digitizing processes and modernizing platforms |
| `it-governance-framework.md` | Decision rights, escalation paths, and a charter for the IT steering committee |
| `enterprise-architecture.md` | A current-state and target-state view of the application, data, and infrastructure landscape |
| `budget-allocation-model.md` | An IT budget breakdown across run (keep the lights on), grow (incremental improvements), and transform (strategic change) |
| `workforce-development-plan.md` | A skills gap analysis, training roadmap, and hiring plan for the IT organization |
| `it-risk-appetite-statement.md` | A formal statement of the organization's tolerance for IT and technology risk |

It also produces eight brief templates: board technology briefing, IT steering committee agenda, vendor review summary, project portfolio status, digital initiative proposal, IT investment case, technology modernization pitch, and quarterly IT review.

**When to use it**

Use the CIO agent at the start of an annual planning cycle, when preparing a technology strategy for board presentation, when a new IT leader is onboarding and needs to document the current state, or when the organization is undertaking significant technology change.

**What you need to provide**

- `--organization-name` — the name of your company or department (required)
- `--strategic-priorities` — two or three sentences describing what the business is trying to achieve in the next one to three years (required)
- `--it-maturity-level` — an honest description of where the IT function stands today (required; examples: "Reactive — we fix things when they break; no formal architecture or governance process," or "Managed — we have documented processes but they are not consistently followed")
- `--budget-context` — the approximate IT budget or spend context (optional; example: "$2M annual IT budget, 60% run/40% change")
- `--digital-initiatives` — current or planned digital transformation initiatives (optional)
- `--regulatory-environment` — regulatory or compliance obligations that affect IT (optional; example: "HIPAA, SOX")
- `--it-docs-dir` — path to a folder of existing IT documentation (optional)
- `--run-id` — unique label for this run (optional; auto-generated as `run-YYYYMMDDTHHMMSS-<6hex>` if omitted)
- `--force` — overwrite an existing run directory of the same name (optional)

**CLI command**

```
agentsuite cio run \
  --organization-name "Acme Manufacturing Co." \
  --strategic-priorities "Expand into two new markets, reduce operational costs by 15%, and improve customer self-service capabilities" \
  --it-maturity-level "Reactive — we fix things when they break; no formal architecture or governance process in place" \
  --budget-context "$3M annual IT budget" \
  --regulatory-environment "SOX, state data privacy laws"
```

On Windows, use a single long line:

```
agentsuite cio run --organization-name "Acme Manufacturing Co." --strategic-priorities "Expand into two new markets, reduce operational costs by 15%, and improve customer self-service capabilities" --it-maturity-level "Reactive — we fix things when they break; no formal architecture or governance process in place"
```

**How to approve**

```
agentsuite cio approve --run-id run-cli --approver "Your Name" --project-slug acme-it
```

**Common errors**

| Error | What it means | What to do |
|---|---|---|
| `NoProviderConfigured` | No API key found and Ollama is not running | Set your API key (Section 4) or start Ollama (Section 4b) |
| `ConsistencyCheckFailed` | Two documents contradict each other (for example, the budget model allocates more to transformation than the maturity level supports) | Make your `--strategic-priorities` and `--it-maturity-level` descriptions more specific, then re-run |
| Low QA scores (below 7.0) | A document is missing important detail | Open `qa_scores.json`, read `revision_instructions`, edit or re-run |
| `HardCapExceeded: $5.00` | The run exceeded the cost safety limit | Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` |
| `extract stage produced invalid JSON` | The AI returned malformed output | Re-run — this is almost always transient |

---

## 8. Reading Your Results

After any agent run completes, open the output folder in your file explorer. By default this is `.agentsuite/runs/<run-id>/` inside whatever folder you were in when you ran the command. If you did not specify a `--run-id`, the folder will be named with the auto-generated ID shown in the command output (for example, `.agentsuite/runs/run-20260427T143022-a3f9c1/`).

**The nine documents** are the primary output. Read the "Start here" document for each agent first (listed in each agent chapter above). It gives you the overall picture. The other eight documents fill in specific areas in more depth.

**The brief template library** is a subfolder called `brief-template-library/`. Each template is a fill-in-the-blank document for a common task. Open any template, fill in the bracketed placeholders with your specific details, and it is ready to use.

**qa_scores.json**

This file contains the quality scores from Stage 5. Open it in any text editor. It looks like this (abbreviated):

```json
{
  "overall_pass": true,
  "pass_threshold": 7.0,
  "documents": {
    "brand-system.md": {
      "score": 8.5,
      "requires_revision": false,
      "revision_instructions": null
    },
    "founder-voice-guide.md": {
      "score": 6.2,
      "requires_revision": true,
      "revision_instructions": "The voice guide lacks specific sentence-length guidance and does not include examples of the founder's preferred vocabulary in context. Add three to five sample sentences that demonstrate the voice, and specify whether short punchy sentences or longer explanatory ones are preferred."
    }
  }
}
```

**What `requires_revision: true` means**

The document is technically complete but the quality check found something that should be improved before you rely on it. The `revision_instructions` field tells you exactly what to fix in plain language. You have two choices:

1. Open the document in a text editor, make the changes described in `revision_instructions`, and approve.
2. Add more detail to your command-line inputs (for example, a more specific `--mission` or `--target-users`) and run the agent again.

A score below 7.0 does not mean the document is useless — it means one specific thing needs more detail. Read the revision instructions first before deciding whether to fix it manually or re-run.

**overall_pass: false**

If the overall pass is false, at least one document scored below 7.0. You do not have to fix everything before approving — you can approve and edit documents afterward. But be aware that the flagged document has a known gap.

---

## 9. Configuration Reference

All AgentSuite settings are controlled through environment variables — settings you type into your terminal before running a command. Here is a complete reference:

| Variable | Required? | Default | What it does |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | One of these four is required | (none) | Your Anthropic Claude API key. Get one at console.anthropic.com. |
| `OPENAI_API_KEY` | One of these four is required | (none) | Your OpenAI GPT API key. Get one at platform.openai.com. |
| `GOOGLE_API_KEY` | One of these four is required | (none) | Your Google Gemini API key. Also accepted as `GEMINI_API_KEY`. Get one at aistudio.google.com. |
| `OLLAMA_HOST` | Only if Ollama is not on the default port | `http://localhost:11434` | The address where Ollama is running. Change this only if you installed Ollama on a different computer or port. |
| `AGENTSUITE_ENABLED_AGENTS` | No | `founder` | Comma-separated list of agents to enable. Options: `founder,design,product,engineering,marketing,trust_risk,cio`. |
| `AGENTSUITE_OUTPUT_DIR` | No | `.agentsuite/` in your current folder | Where AgentSuite writes its output. Change this if you want documents saved somewhere else. |
| `AGENTSUITE_COST_CAP_USD` | No | `5.00` | Maximum amount in US dollars that a single run can spend on AI API calls. If a run exceeds this, it stops and reports a `HardCapExceeded` error. Raise it if you have large inputs or need longer documents. |

**Setting variables on Windows (temporary — for this terminal session only):**
```
set AGENTSUITE_COST_CAP_USD=10
```

**Setting variables on Windows (permanent — survives closing the terminal):**
Search "Environment Variables" in the Start menu → "Edit the system environment variables" → "Environment Variables" → "New" under User Variables.

**Setting variables on Mac/Linux (temporary):**
```
export AGENTSUITE_COST_CAP_USD=10
```

**Setting variables on Mac/Linux (permanent):**
Add the `export` line to your `~/.zshrc` or `~/.bashrc` file, then run `source ~/.zshrc` (or restart the terminal).

---

## 10. Troubleshooting

**"agentsuite is not recognized" or "command not found"**

Python's scripts folder is not in your system PATH. The easiest fix:
- Close the terminal, reopen it, and try again.
- On Windows, search "Edit the system environment variables" in the Start menu, click "Environment Variables," find `Path` under User Variables, and add the folder where pip installs scripts. This is usually `C:\Users\YourName\AppData\Local\Programs\Python\Python312\Scripts\`.
- Alternatively, run AgentSuite as: `python -m agentsuite founder run ...`

**`NoProviderConfigured`**

AgentSuite could not find any AI provider to use. Check:
1. Did you set an API key in this terminal session? The key only lasts for the current terminal window. Set it again.
2. Is Ollama running? Type `ollama list` in a second terminal. If it says "command not found," install Ollama first.
3. Did you type the variable name correctly? It must be exactly `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY`.

**`ConsistencyCheckFailed`**

Two of the nine documents produced by the agent contradict each other — for example, the target audience described in one document does not match the target audience in another. This usually means your inputs were ambiguous.

Fix: make your required inputs more specific. For example, instead of `--target-users "entrepreneurs"`, try `--target-users "first-time founders building B2B SaaS products with less than $1M in funding."` Then re-run.

**`HardCapExceeded: $5.00`**

Your run cost more than the $5.00 safety limit. This most often happens when you provide very large input files. Options:
- Raise the cap: `set AGENTSUITE_COST_CAP_USD=10` (or any amount)
- Reduce your input: use shorter, more focused documents as inputs
- Switch to Ollama, which has no per-token cost

**Low QA scores (below 7.0)**

Open `qa_scores.json` and read the `revision_instructions` for each flagged document. The instructions are written in plain language and tell you exactly what is missing. You can:
- Edit the flagged document directly in a text editor
- Add more detail to your command-line inputs and re-run
- Approve anyway if the document is good enough for your purposes

**"extract stage produced invalid JSON"**

The AI returned output that AgentSuite could not parse. This is a transient error caused by the AI occasionally producing malformed output. Run the same command again — it resolves itself almost every time. If it happens repeatedly (three or more times in a row), try a different AI provider or check whether the AI provider is reporting service issues.

**Documents look generic or miss the point**

This almost always means the inputs were too brief or too vague. Add more specifics to your required fields. A one-sentence mission statement gives the AI less to work with than three sentences that include your specific customer, the specific problem, and the specific outcome you are targeting.

**The run folder is empty or missing**

Check that `AGENTSUITE_OUTPUT_DIR` is not set to an unexpected location. By default, output goes to `.agentsuite/runs/run-cli/` inside the folder where you ran the command. Make sure you are looking in the right place.

---

## 11. Glossary

This glossary defines every technical term used in this manual. Terms are listed alphabetically.

**ADR (Architecture Decision Record):** A short document capturing a single architectural choice — what was decided, why, what alternatives were considered, and what the consequences are. ADRs are written once and kept forever as a log of how a system's design evolved.

**Agent:** In AgentSuite, an agent is a specialized program that runs a defined sequence of steps (the pipeline) to produce a set of documents about a specific business function. AgentSuite has seven agents: Founder, Design, Product, Engineering, Marketing, Trust/Risk, and CIO.

**API (Application Programming Interface):** A way for one piece of software to communicate with another. When AgentSuite calls Anthropic or OpenAI, it does so through their APIs. An API key is the credential that proves you have an account.

**API key:** A long string of characters (looks like a password) that identifies your account with an AI provider. You set it as an environment variable before running AgentSuite. Never share your API key with other people — it is linked to your billing account.

**Approval:** The step you take after reviewing an agent's output. Running the approve command signals that you are satisfied with the documents and copies them from the temporary run folder into a permanent location (the kernel) for future use.

**Artifact:** Any file that an agent produces — a document, a template, a score file. AgentSuite agents produce nine primary artifacts (documents) and eight brief templates per run.

**Brief template:** A fill-in-the-blank document for a specific task (for example, "sprint planning brief" or "press release"). Brief templates are produced by every AgentSuite agent and stored in the `brief-template-library/` subfolder of the run output. You fill in the bracketed placeholders with your specific details.

**CLI (Command-Line Interface):** A way of running software by typing commands into a terminal, as opposed to clicking buttons in a graphical application. AgentSuite is a CLI tool.

**Compliance matrix:** A table that maps each requirement from a regulation or standard (such as SOC 2, HIPAA, or PCI-DSS) to the controls, policies, or evidence that satisfy it. Auditors use this table to verify that nothing has been missed.

**ConsistencyCheckFailed:** An error that occurs when two of the nine documents produced by an agent contradict each other. The fix is to make your inputs more specific and re-run.

**Digital transformation:** The process of replacing manual, paper-based, or legacy-technology processes with modern digital tools and ways of working. It usually requires changes to processes, skills, and organizational structures, not just technology.

**Environment variable:** A named setting stored in your terminal session (or permanently in your operating system) that programs can read. AgentSuite reads environment variables for your API key, output folder, cost cap, and enabled agents. You set them with `set` (Windows) or `export` (Mac/Linux).

**Epic:** A large chunk of work that groups related user stories together. Think of it as a chapter heading — "User Onboarding" is an epic; "User sees a progress bar during setup" is a user story inside it.

**Extract stage:** The second stage of the AgentSuite pipeline. AgentSuite sends your inputs to the AI and asks it to extract key facts and structure them. If the AI returns malformed output at this stage, you see the error `extract stage produced invalid JSON`.

**HardCapExceeded:** An error that occurs when a run's AI API costs exceed the limit set by `AGENTSUITE_COST_CAP_USD` (default: $5.00). Raise the cap or reduce input size to resolve.

**ICP (Ideal Customer Profile):** A detailed description of the type of company or person who is the best fit for your product. Unlike a persona (which describes an individual), an ICP describes the characteristics of the whole account — industry, size, budget, and buying process.

**IT governance:** The system of decision rights and accountability structures that determines who can authorize IT investments, who sets technology standards, and how IT-related risks are managed.

**IT maturity level:** A description of how well-developed the IT function is. Common levels run from "reactive" (fixing problems as they arise, no formal processes) through "managed" (documented but inconsistently followed) to "optimizing" (continuously measured and improved).

**JSON (JavaScript Object Notation):** A standard file format for structured data. It looks like this: `{"key": "value"}`. AgentSuite uses JSON files internally to pass structured data between pipeline stages. You do not need to edit JSON files directly — AgentSuite reads and writes them automatically.

**Kernel:** The permanent storage location for approved agent output. When you run the approve command, your documents are copied from the temporary run folder into `.agentsuite/_kernel/<project-slug>/`. The kernel is where approved documents live long-term and can be reused by future runs.

**KPI (Key Performance Indicator):** A number you track to know if something is working. For a marketing campaign, examples include cost per lead, click-through rate, and conversion rate. For a product, examples include daily active users, task completion rate, and customer satisfaction score.

**Large language model (LLM):** The AI brain that AgentSuite uses to write documents. Examples include Claude (made by Anthropic), GPT (made by OpenAI), and Gemini (made by Google). When you set an API key, you are telling AgentSuite which LLM to use.

**MCP (Model Context Protocol):** A standard protocol that allows AI coding tools (such as Claude Code or Codex) to communicate with external programs like AgentSuite. If you are a developer, MCP lets you wire AgentSuite into your AI-assisted development workflow so agents can be invoked directly from your coding environment.

**MoSCoW scoring:** A prioritization method that sorts features into four categories: Must have (required for launch), Should have (important but not critical for day one), Could have (nice to have if time allows), and Won't have this time (explicitly deferred to a future release).

**NoProviderConfigured:** An error that occurs when AgentSuite cannot find an API key or a running Ollama instance. Set an API key (Section 4) or start Ollama (Section 4b) to resolve.

**Ollama:** Free, open-source software that runs large language models locally on your own computer. Using Ollama means no API account, no per-use costs, and no data sent to external servers. It requires more computer resources than a cloud API and is typically slower.

**Pass threshold:** The minimum QA score a document must achieve to be considered passing. AgentSuite's pass threshold is 7.0 out of 10. Documents that score below this threshold have a `requires_revision: true` flag and specific revision instructions in `qa_scores.json`.

**Pen test (penetration test):** A controlled, authorized attempt to breach a system's defenses. A pen test brief specifies the scope (which systems), the rules of engagement (what is allowed), and what the tester should report.

**Pipeline:** The five stages every AgentSuite agent runs in sequence: intake → extract → spec → execute → qa. After the pipeline completes, the run enters the approval state.

**Postmortem:** A blame-free review conducted after an incident. The goal is to understand what happened, why, and what changes prevent it from happening again.

**Project slug:** A short, lowercase, hyphenated label you choose to identify a run or project. It becomes part of the folder name where approved documents are stored. For example, `--project-slug my-product` stores approved documents at `.agentsuite/_kernel/my-product/`. No spaces — use hyphens.

**QA rubric:** The set of criteria that AgentSuite uses to score each document during Stage 5 (QA). Criteria vary by agent but generally include: completeness, internal consistency, alignment with inputs, actionability, and specificity.

**Requires_revision:** A field in `qa_scores.json` that is `true` when a document scored below the pass threshold (7.0). When `requires_revision` is true, read the `revision_instructions` field for specific guidance on what to improve.

**Residual risk:** The risk that remains after all controls have been applied. No system is perfectly secure — residual risk is what you accept when the cost of further mitigation exceeds the benefit. Documenting this acceptance formally is a sign of a mature risk program.

**Risk register:** A living document that lists every known risk to the organization, rated by likelihood and impact, with an owner and a current mitigation status.

**Run ID:** A label that identifies a specific agent run. If you do not specify `--run-id`, AgentSuite auto-generates one in the format `run-YYYYMMDDTHHMMSS-<6hex>` (for example, `run-20260427T143022-a3f9c1`). You reference the run ID when you approve: `--run-id run-20260427T143022-a3f9c1`. You can specify a custom run ID with `--run-id my-label` if you want a predictable folder name. If you re-run with the same run ID, add `--force` to overwrite the existing folder — without it, the run will error to protect your previous output.

**Runbook:** A set of step-by-step instructions for operating a system. Good runbooks let any engineer — not just the person who built the system — handle common tasks and incidents without guessing.

**SLA (Service Level Agreement):** A formal commitment about system behavior — typically uptime percentage (for example, 99.9%), response time (for example, under 200 milliseconds), or error rate (for example, fewer than 0.1% of requests fail).

**Spec stage:** The third stage of the AgentSuite pipeline. AgentSuite uses the extracted data to generate a detailed plan for each of the nine documents before writing begins.

**Tech debt:** Code, design choices, or shortcuts that work now but will cost more to maintain or change later. Not inherently bad — sometimes the right trade-off — but it needs to be tracked and addressed deliberately.

**Tabletop exercise:** A discussion-based simulation in which a team walks through a hypothetical incident scenario together. No systems are touched — the goal is to identify gaps in the response plan before a real event forces them to the surface.

**Threat model:** A structured analysis of what could go wrong with a system, who might cause it, and how likely and damaging each scenario is. A threat model lists assets worth protecting, the threat actors who might target them, the attack paths they might use, and the controls that reduce the risk.

**Value proposition:** A clear statement of the specific benefit your product or service delivers to a customer. A strong value proposition answers: "Why should I choose this over the alternative?"

**Vendor portfolio:** The complete set of technology vendors an organization relies on, with associated spend, contract terms, risk ratings, and strategic importance.

---

## Where to Get Help

- **GitHub Issues** — report a bug or ask a question: https://github.com/scottconverse/AgentSuite/issues
- **Contributing guide** — how to set up the development environment and run tests: `CONTRIBUTING.md` in the AgentSuite folder
- **Full technical reference** — detailed developer documentation: `docs/README-FULL.pdf`
- **GitHub Discussions** — community Q&A and feature requests: https://github.com/scottconverse/AgentSuite/discussions

---

*AgentSuite v0.8.3 — User Manual*
