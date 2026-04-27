---
description: Run the AgentSuite Design agent to produce a complete design specification bundle (9 artifacts + 8 brief templates).
---

Invoke the design-agent skill. If the user has provided arguments after `/design-agent`, parse them as `--target-audience`, `--campaign-goal`, `--channel`, `--project-slug`, `--inputs-dir` overrides. Otherwise prompt for target audience, campaign goal, and channel one at a time, then call `design_run`.
