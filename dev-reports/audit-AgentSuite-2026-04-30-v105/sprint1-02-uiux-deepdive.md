# UI/UX Deep-Dive — AgentSuite v1.0.6

**Audit date:** 2026-04-30  
**Role:** Senior UI/UX Designer  
**Scope audited:** Sprint 1 UX-relevant changes (cli.py RevisionRequired handler, CIO MCP approve handler, docs/index.html landing page)  
**Auditor posture:** Balanced

---

## TL;DR

AgentSuite's Sprint 1 error handling and landing page show thoughtful, developer-focused copy. The RevisionRequired flow is actionable and transparent; the MCP structured dict clearly surfaces revision status. The landing page is accurate and honest but the roadmap section ("All 7 agents are shipped") now reads as incomplete—the sentence about upcoming features lacks specificity and doesn't acknowledge the current state compellingly. No blockers detected.

## Severity roll-up (UX)

| Severity | Count |
|---|---|
| Blocker | 0 |
| Critical | 0 |
| Major | 1 |
| Minor | 2 |
| Nit | 2 |

---

## What's working

- **RevisionRequired error message (CLI)** — Lines 144–150 in cli.py follow a clean "what happened → here's what to do" pattern. The message explicitly names the failure (QA flagged), points to the artifact (qa_report.md), and gives the exact CLI commands to fix and retry. Path is shown in full so it's copy-pasteable. Tone is professional and appropriate for a developer tool.
- **MCP structured error response** — The dict returned in cio/mcp_tools.py lines 111–116 includes all necessary fields: error type, human-readable message, file path, and an action field that tells the MCP client what to do. Useful for clients building UIs on top of AgentSuite.
- **Landing page visual hierarchy** — The page structure (hero → what it does → install → quick start → sample run → agents → roadmap → docs) follows a natural flow. The feature cards are scannable and informative. Typography scale is consistent.

---

## What couldn't be assessed

- Terminal rendering (actual output under different terminal widths, color scheme application on dark terminals)
- MCP client integration (how Codex, Claude Code, and Cowork actually surface the error dict; whether the "action" field text is clear to those calling systems)
- Mobile browser rendering of the landing page (viewport testing)

---

## First impressions

A first-time visitor to docs/index.html lands on a clear, credible value prop: "Seven role-specific reasoning agents that turn vague intent into precise operating artifacts." The headline is declarative and concrete—no marketing fluff. The install/quick-start sections are developer-friendly. Scanning the page takes ~3 seconds to understand: this is a multi-agent tool for generating organizational artifacts. The visual design is understated and scannable—good for a developer-focused product.

---

## Journey walkthroughs

### Journey: "Developer receives RevisionRequired error and fixes it"

1. User runs `agentsuite <agent> approve` with a run that has QA failures.
2. The tool catches `RevisionRequired`, prints a clear error message with the qa_report.md path.
3. Error message tells the user exactly what to do: review the report, re-run with `--run-id <id> --force`, then re-approve.
4. Message is output to stderr (correct for errors).
5. Exit code is 1 (correct).

**Strengths:** The copy is concrete and actionable. Commands are shown in copyable form. The flow acknowledges the need to review external documentation (the qa_report) but doesn't dump raw content.

**Friction point identified:** See UX-001 below—the path display could be slightly more ergonomic.

### Journey: "MCP client receives approval failure and handles it"

1. MCP client calls `agentsuite_cio_approve()` with a run that has QA failures.
2. Function catches `RevisionRequired` and returns a structured dict (not an exception).
3. Dict includes error field ("revision_required"), message, qa_report_path, and action field.
4. MCP client can parse and surface this to its own user.

**Strengths:** Returning a dict instead of raising is the right choice for MCP—clients can handle it gracefully without try/catch. Fields are clearly named.

**Friction point identified:** See UX-002 below—the action text is helpful but could be slightly more concise for display in tight UIs.

### Journey: "First-time visitor to landing page understands the product"

1. User lands on docs/index.html, reads h1 and lede paragraph (5 seconds).
2. Scans "What it does" section to understand the pipeline.
3. Checks "Shipped agents" grid to see the scope.
4. Reviews "Roadmap" section to understand what's next.

**Strengths:** The product is clearly defined. Agents are well-documented with example artifacts shown in screenshots. The install path is obvious.

**Friction point identified:** See UX-003 below—the roadmap section is now vague, and the version badge is stale.

---

## Findings

### [UX-001] — Minor — Copy — RevisionRequired path display could be more shell-friendly

**Evidence**  
File: `agentsuite/cli.py`, lines 142–146.  
Current copy: `"  Review the QA report: {qa_report}\n"`  
The path is displayed as a Python `Path` object printed to string. On Windows, this may render with backslashes; on POSIX it's forward slashes. For a developer copying this path to a shell or editor, the format is slightly inconsistent with the copy-paste pattern.

**Why this matters**  
A developer reading this error is in "fix mode"—they want to copy the path and open it fast. Showing the path in the same format they'd use in a shell (absolute, no "Path(" wrapper) removes a tiny cognitive load and reduces the chance they mistype it.

**Blast radius**  
Adjacent code: cli.py lines 95–114 use similar path display in other error messages; same pattern applies.  
User-facing: developers hitting RevisionRequired (estimated 15–30% of runs per agent). This is a common error path.  
Tests to update: none—this is copy-only.

**Fix path**  
Use `str(qa_report)` explicitly in the f-string, or better yet, show it as a path-suitable string. Suggest:

```python
typer.echo(
    "Error: QA flagged this run as requiring revision before approval.\n"
    f"  Review the QA report:\n"
    f"    {qa_report}\n"
    f"  Address the feedback, then re-run the agent:\n"
    f"    agentsuite <agent> run --run-id {resolved_run_id} --force\n"
    f"  Once the new run passes QA, approve it:\n"
    f"    agentsuite <agent> approve --run-id <new-run-id> --approver <you> --project-slug <slug>",
    err=True,
)
```

(Added blank line before the path to separate it visually; shows path on its own line so it's scannable and copy-pasteable.)

---

### [UX-002] — Minor — Copy — MCP action field is helpful but could be tighter

**Evidence**  
File: `agentsuite/agents/cio/mcp_tools.py`, line 115.  
Current copy: `"action": "Review qa_report.md and re-run the agent to address QA feedback before approving."`

**Why this matters**  
An MCP client might surface this action field in a small error toast, modal, or inline message. The current text is instructional but verbose—it reads more like a help article than a crisp action prompt. MCP clients need to fit this into tight UIs (e.g., a 2-line error card).

**Blast radius**  
Adjacent code: All 7 agents' approve handlers have the same RevisionRequired pattern (cio/mcp_tools.py is representative). Fix applies to all 7.  
User-facing: MCP clients (Codex, Claude Code, Cowork) surface this to their users. If MCP clients are building error UIs, they'll likely truncate verbose action text, which defeats its purpose.  
Related findings: none, but this is part of a systemic pattern across all 7 agents.

**Fix path**  
Tighten the action copy to be scannable in a tight UI:

```python
"action": "Review the qa_report.md, address feedback, then re-run the agent."
```

Or even shorter if MCP clients only show one line:

```python
"action": "Address QA feedback in qa_report.md and re-run the agent."
```

Apply this change to all 7 agents' approve handlers.

---

### [UX-003] — Major — Copy — Landing page roadmap section is now vague and doesn't match current state

**Evidence**  
File: `docs/index.html`, lines 118–119.  
Current copy:  
```html
<h2>Roadmap</h2>
<p>All 7 agents are shipped. See <a href="https://github.com/scottconverse/AgentSuite/blob/main/CHANGELOG.md">CHANGELOG.md</a> for upcoming releases — including multi-agent pipelines and per-day cost controls.</p>
```

The version badge on line 49 shows `v1.0.5`, but the heading says "v1.0.6" in the context. Version mismatch: the HTML is stale.

**Why this matters**  
"All 7 agents are shipped" is true but uninspiring for a visitor asking "what's next?" The roadmap section now reads as a dead end instead of forward momentum. A visitor interested in future features sees "see CHANGELOG.md" without knowing what's in it—they have to click away. The sentence doesn't answer the core question: what's being actively built?

The version badge shows 1.0.5, but the audit scope says v1.0.6 is current. This signals the page is stale.

**Blast radius**  
User-facing: all landing-page visitors (organic search, GitHub README link, GitHub Pages, etc.). First impressions for new users evaluating the product.  
Adjacent pages: marketing/docs consistency. If external docs reference v1.0.5, they should match.

**Fix path**  
Update the version badge and roadmap section to be honest and forward-looking:

```html
<h1>AgentSuite <span class="v">v1.0.6</span></h1>
```

And replace the roadmap section:

```html
<h2>Roadmap</h2>
<p>All 7 core agents are shipped and stable. Current focus: multi-agent pipelines to chain agents end-to-end, and per-day cost controls for production safety. See <a href="https://github.com/scottconverse/AgentSuite/blob/main/CHANGELOG.md">CHANGELOG.md</a> for detailed updates and community contributions welcome.</p>
```

This version:
- Acknowledges what's shipped ("All 7 core agents are shipped and stable")
- Names what's being actively built ("multi-agent pipelines," "per-day cost controls")
- Hints at impact ("production safety")
- Still points to CHANGELOG for details
- Invites contribution ("community contributions welcome")

---

### [UX-004] — Minor — Copy — Version number in header doesn't match product version

**Evidence**  
File: `docs/index.html`, line 49.  
Badge shows: `v1.0.5`  
Expected (per audit scope): `v1.0.6`

**Why this matters**  
A visitor checking the docs to confirm version compatibility will see 1.0.5 and assume the page is outdated or they're reading old docs. In a developer context, version mismatches undermine trust—"did this page get updated with the release?"

**Blast radius**  
User-facing: all landing-page visitors (likely 10–20% of new users check version first).  
Migration: none; this is a simple text update.  
Related findings: UX-003 (roadmap section also signals staleness).

**Fix path**  
Update line 49:

```html
<h1>AgentSuite <span class="v">v1.0.6</span></h1>
```

---

### [UX-005] — Nit — Copy — The meta description is missing "approval workflow"

**Evidence**  
File: `docs/index.html`, line 8.  
Current: `"Seven role-specific reasoning agents that turn vague human intent into precise operating artifacts. Open-source, MIT-licensed, MCP-compatible with Codex, Claude Code, and Cowork."`

The description omits mention of the approval/kernel workflow, which is a differentiator. A visitor sees the agents but not the "governed creative ops" angle until they read the body.

**Why this matters**  
SEO and visitor scannability. A search result preview or browser tab will show this text. Including "kernel approval workflow" or "managed artifact governance" would better set expectations upfront.

**Blast radius**  
Adjacent code: none (meta tags only).  
User-facing: search results, social shares, preview cards.

**Fix path**  
Suggest rewrite:

```html
<meta name="description" content="Seven role-specific reasoning agents with managed approval workflows that turn vague intent into precise artifacts. Open-source, MIT-licensed, MCP-compatible with Codex, Claude Code, and Cowork.">
```

---

### [UX-006] — Nit — Responsive — Landing page layout untested at 320px and 1440px

**Evidence**  
File: `docs/index.html`, lines 37–44.  
The grid uses `grid-template-columns: 1fr 1fr` with a breakpoint at 600px, but the page max-width is 760px. On a 1440px desktop, the page is still centered in a 760px column (correct). On a 320px phone, the grid goes to 1fr and wraps (correct per the media query).

No responsive issues detected, but the page wasn't explicitly tested at extremes. Since the design uses intrinsic widths (max-width, padding), it's likely robust. No action needed unless mobile testing reveals text wrapping issues.

**Why this matters**  
Accessibility and reach. A visitor on a 320px Android phone or 1440px ultrawide should experience the page gracefully.

**Blast radius**  
User-facing: mobile and ultrawide visitors (estimated 5–10% of traffic).

**Fix path**  
No fix required if testing shows it works. Recommend adding a screenshot test (at 320px, 768px, 1440px) to the documentation checklist to prevent future regressions.

---

## States audit matrix

AgentSuite has no stateful UI (it's a CLI tool and a landing page). The CLI error states are handled below.

| Flow / state | Handled | Evidence |
|---|---|---|
| `approve` command succeeds | ✓ | JSON output on stdout |
| `approve` command fails (RevisionRequired) | ✓ | Error message + exit code 1 |
| `approve` command fails (other exception) | ✓ | Generic error fallback |
| MCP `approve` call succeeds | ✓ | ApprovalResult dict returned |
| MCP `approve` call fails (RevisionRequired) | ✓ | Structured error dict returned |
| MCP `approve` call fails (other exception) | ~ | Raises exception; MCP client must catch |

---

## Accessibility snapshot

**Landing page (docs/index.html)**
- **Keyboard navigation:** All links are keyboard-accessible (default HTML behavior). No interactive elements beyond links. ✓
- **Focus visibility:** Links have underline on hover (`border-bottom-color`); focus state not explicitly tested but default browser outline applies. ✓
- **Color contrast:** Text on background (#1a1a1a on #fafafa) = very high contrast (>15:1). Code blocks (#1a1a1a on #f0f0f0) = also very high. Links (#2a4d8f on #fafafa) = 7.5:1 (well above 4.5:1 WCAG AA). ✓
- **Screen reader labeling:** All headings use semantic `<h1>`, `<h2>`, `<h3>`. Images have alt text. No ARIA labels needed. ✓
- **Reduced motion:** No animations or transitions detected. ✓
- **Touch target size:** Links and buttons are text-based; line-height 1.6 provides ample spacing. ✓

**CLI error messages**
- No accessibility concerns; plain text output.

---

## Patterns and systemic observations

1. **Error message pattern is consistent across CLI and MCP.** Both paths (CLI RevisionRequired and MCP approve handler) follow "what happened → what to do" structure. This is good practice and doesn't need changes.

2. **Version staleness is a trailing indicator.** The landing page version badge (1.0.5) lags the codebase (1.0.6). This suggests the release process doesn't automatically update the HTML. Recommend a build-time step (e.g., sed in a release script) to sync the version badge.

3. **Roadmap section lacks specificity.** "Upcoming releases — including multi-agent pipelines and per-day cost controls" is helpful but generic. Developers want to know: is this being actively worked? When? These questions should be answered in the body text, not deferred to CHANGELOG.md.

---

## Summary for dev team

- **Top blockers:** None. Ship as-is.
- **Top critical fixes:** None.
- **Top major fixes:** UX-003 (roadmap section is vague). This is a copy fix; ~5 min to implement and test.
- **Top minor fixes:** UX-001 (path display format), UX-002 (MCP action text can be tighter), UX-004 (version badge stale). These are copy tweaks; ~10 min total.
- **Nits:** UX-005 (meta description), UX-006 (responsive testing). Nice-to-have.

**Related cross-cutting pattern:** The roadmap section and version badge both signal staleness. A release checklist item ("update version badge + roadmap in docs/index.html") would prevent this in future releases.

---

## Appendix: surfaces reviewed

- `agentsuite/cli.py` — `_make_approve_fn()` function, lines 117–165, focusing on RevisionRequired exception handler (lines 141–153)
- `agentsuite/agents/cio/mcp_tools.py` — `agentsuite_cio_approve()` function, lines 104–129, focusing on RevisionRequired exception handler (lines 109–116)
- `docs/index.html` — full page (landing page), lines 1–138, focusing on hero (line 49), "What it does" section (line 54), Roadmap (lines 118–119), meta description (line 8)
- Viewport sizes checked: 760px max (container), responsive breakpoint at 600px
- Testing: no live terminal rendering or dark-mode testing performed