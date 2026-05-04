# AgentSuite Troubleshooting Guide

**Version 1.1.0**

This guide covers the five most common failure modes in AgentSuite, with plain-language explanations and specific steps to resolve each one.

---

## 1. `NoProviderConfigured` — No API key set

**What it means**

AgentSuite could not find any AI provider to use. It checked for Anthropic, OpenAI, Google Gemini, and Ollama, and found none of them configured.

**How to fix it**

Set the environment variable for your AI provider before running AgentSuite:

```
# Anthropic Claude (recommended)
Windows:   set ANTHROPIC_API_KEY=sk-ant-your-key-here
Mac/Linux: export ANTHROPIC_API_KEY=sk-ant-your-key-here

# OpenAI GPT
Windows:   set OPENAI_API_KEY=sk-your-key-here
Mac/Linux: export OPENAI_API_KEY=sk-your-key-here

# Google Gemini
Windows:   set GOOGLE_API_KEY=your-key-here
Mac/Linux: export GOOGLE_API_KEY=your-key-here
```

**Important:** the key only lasts for the current terminal window. If you close and reopen the terminal, you must set it again. To make it permanent, see Section 4 of the User Manual.

If you are using Ollama (the free, local option), make sure Ollama is running before you run AgentSuite:

```
ollama serve
```

Then verify it is up by opening a second terminal and running `ollama list`. If you see a model listed, Ollama is ready.

---

## 2. `UnknownAgent` — Misspelled agent name in `AGENTSUITE_ENABLED_AGENTS`

**What it means**

You have set `AGENTSUITE_ENABLED_AGENTS` to a list of agent names, but one or more of the names does not match any registered agent. This usually means a typo or a capitalization error.

**How to fix it**

Run the following command to see the exact, correct names for all registered agents:

```
agentsuite agents
```

The output will list both the enabled agents and all registered agents. Use the names from `all_registered` — they are case-sensitive and must match exactly. The valid agent names are:

```
founder
design
product
engineering
marketing
trust_risk
cio
```

Note that `trust_risk` uses an underscore, not a hyphen. This is a common mistake.

Example of a correct setting:

```
Windows:   set AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio
Mac/Linux: export AGENTSUITE_ENABLED_AGENTS=founder,design,product,engineering,marketing,trust_risk,cio
```

---

## 3. Run directory already exists — add `--force` or use a different `--run-id`

**What it means**

You are trying to run an agent with a `--run-id` (or letting AgentSuite use a default ID) that already exists on disk. AgentSuite refuses to overwrite it by default to protect your existing output.

**How to fix it**

You have two options:

**Option A — Add `--force` to overwrite the existing folder:**

```
agentsuite founder run \
  --business-goal "Launch Acme invoicing for small businesses" \
  --project-slug acme \
  --force
```

This deletes the existing run folder and replaces it with the new output. Use this when you are re-running to improve the result and do not need the old output.

**Option B — Use a different `--run-id` to keep both runs:**

```
agentsuite founder run \
  --business-goal "Launch Acme invoicing for small businesses" \
  --project-slug acme \
  --run-id acme-v2
```

This creates a new folder alongside the old one. Use this when you want to compare two runs or keep a record of previous output.

If you did not specify a `--run-id`, AgentSuite auto-generates one in the format `run-YYYYMMDDTHHMMSS-<6hex>` — each run gets a unique ID and this error should not occur unless you explicitly reused an ID.

---

## 4. Ollama connection refused — start `ollama serve`

**What it means**

AgentSuite tried to connect to Ollama at `http://localhost:11434` but the connection was refused. Ollama is either not installed or not currently running.

**How to fix it**

**Step 1 — Check if Ollama is installed:**

```
ollama --version
```

If this says "command not found," install Ollama from https://ollama.ai before continuing.

**Step 2 — Start Ollama:**

```
ollama serve
```

Leave this terminal window open. Ollama runs as a background server.

**Step 3 — Verify it is running:**

Open a second terminal and run:

```
ollama list
```

You should see a list of downloaded models. If the list is empty, pull a model first:

```
ollama pull gemma4:e4b
```

(For older or slower computers, use `gemma4:e2b`. For powerful workstations, `gemma4:26b-moe` is more capable.)

**Step 4 — If Ollama runs on a non-default port:**

If you have configured Ollama to listen on a port other than 11434, tell AgentSuite where to find it:

```
Windows:   set OLLAMA_HOST=http://localhost:YOUR_PORT
Mac/Linux: export OLLAMA_HOST=http://localhost:YOUR_PORT
```

---

## 5. `HardCapExceeded` — Cost cap exceeded

**What it means**

Your run spent more than the configured cost limit (default: $5.00 USD) on AI API calls. AgentSuite stops the run when this happens to protect you from unexpectedly large bills.

This most commonly happens when:
- You provided very large input files (long documents in `--inputs-dir`)
- You are running multiple agents in sequence on a complex project
- You are using a high-cost model (such as Claude Opus or GPT-4 Turbo)

**How to fix it**

**Option A — Raise the cost cap:**

```
Windows:   set AGENTSUITE_COST_CAP_USD=10
Mac/Linux: export AGENTSUITE_COST_CAP_USD=10
```

Replace `10` with however much you want to allow. The default is `5.00`. For very large projects, you may need `20` or more.

**Option B — Break the request into a smaller scope:**

- Use a shorter, more focused `--business-goal` or equivalent required field
- Remove large or low-value files from your `--inputs-dir`
- Run one agent at a time rather than chaining several together

**Option C — Switch to a lower-cost model or Ollama:**

If you are using an expensive cloud model, consider switching to a lower-cost tier or to Ollama (free, local, no per-token cost). See Section 4b of the User Manual for Ollama setup.

---

## 6. `AGENTSUITE_COST_CAP_USD` set to a non-numeric value

**What it means**

You have set `AGENTSUITE_COST_CAP_USD` to a value that is not a valid number — for example, `ten` or `$5.00` (with a dollar sign). AgentSuite validates this setting before making any AI calls and exits immediately with an error that names the bad value.

The error message will look similar to:

```
ValueError: AGENTSUITE_COST_CAP_USD must be a valid decimal number (e.g. "5.00" or "10"). Got: "ten"
```

**How to fix it**

Set the variable to a plain decimal number without currency symbols or units:

```
# Correct — numeric only
Windows:   set AGENTSUITE_COST_CAP_USD=10
Mac/Linux: export AGENTSUITE_COST_CAP_USD=10

# Also correct — decimal form
Windows:   set AGENTSUITE_COST_CAP_USD=5.00
Mac/Linux: export AGENTSUITE_COST_CAP_USD=5.00

# Incorrect — these will produce the error above
set AGENTSUITE_COST_CAP_USD=ten
set AGENTSUITE_COST_CAP_USD=$10
set AGENTSUITE_COST_CAP_USD=10 dollars
```

The default value if the variable is not set is `5.00` (five US dollars).

---

## 7. `list_runs` MCP tool — filtering by project

**What it means**

If you are using AgentSuite via MCP (wired into Claude Code, Codex, or another MCP-compatible tool) and call `list_runs` without a filter, it returns every run across all projects. On a workstation with many projects, the result list can be very long.

**How to filter it**

Pass the optional `project_slug` argument to limit results to a specific project:

```json
{ "tool": "list_runs", "arguments": { "project_slug": "acme" } }
```

Replace `"acme"` with the `--project-slug` value you used when running the agent. The filter is exact — it will not match partial names or run IDs that contain the slug.

If you are not sure what slug a run used, omit the filter first and scan the returned list for the `project_slug` field on each entry.

---

## 8. "ValueError: Path ... is outside the project directory"

AgentSuite refuses to read files outside your project directory. This error appears if a voice sample path, source material, or other file path in your request points to a location outside `.agentsuite/` or your current working directory.

**Fix**: Make sure all file paths in `source_materials` or `founder_voice_samples` point to files inside your project directory. Absolute paths to other drives or home directories are not permitted.

**Example paths that work:**
- `./docs/brand-guide.pdf`
- `source/voice-samples/ceo-email.txt`

**Example paths that will be rejected:**
- `/home/user/Downloads/brand-guide.pdf`
- `C:\Users\name\Documents\old-brand.pdf`
- `../../other-project/assets/logo.png`

---

## 9. Cost warning appears in terminal output

If a run's total cost is greater than zero but less than $0.01, AgentSuite emits a warning to stderr:

```
[WARN] Cost $0.0000 recorded — check your LLM provider billing dashboard.
```

This is informational. It typically appears when using Ollama (local, zero-cost) or a provider that does not return billing information. No action is required unless you expect paid calls to have been made.

---

## Getting more help

- **GitHub Issues** — report a bug or ask a question: https://github.com/scottconverse/AgentSuite/issues
- **GitHub Discussions** — community Q&A and feature requests: https://github.com/scottconverse/AgentSuite/discussions
- **User Manual** — full plain-language walkthrough: `USER-MANUAL.md` (or the `docs/` folder)
- **Contributing guide** — developer setup and test instructions: `CONTRIBUTING.md`

---

*AgentSuite v1.1.0 — Troubleshooting Guide*
